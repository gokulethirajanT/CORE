import random
import sys
import argparse
import pandas as pd
import warnings
from datetime import datetime
from dotenv import load_dotenv
import os
import time

from helpers import (
    connect_to_database,
    get_data_types,
    get_pseudo_variables,
    get_constant_variables,
    clean_data,
    get_pseudo_mapping,
    get_secondary_pools_dm3,
    get_data_type
)
from functions import force_k, generate_pseudonym, shuffle_column

# ─── Load credentials from .env if not passed via CLI ───────
load_dotenv()
warnings.simplefilter(action='ignore', category=UserWarning)
K = 3

def quote_identifier(identifier: str) -> str:
    return f'"{identifier}"'

def get_columns(table: str, cursor) -> list:
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE LOWER(table_name) = LOWER('{table}')
    """)
    return [row[0] for row in cursor.fetchall()]

def generate_pool_of_ids(variable: str, source_table: str, cursor, conn) -> list:
    cursor.execute(f"SELECT DISTINCT {quote_identifier(variable)} FROM {source_table}")
    return [generate_pseudonym(variable, table=source_table, conn=conn) for _ in cursor.fetchall()]

def process_column(col: str, table: str, cursor, dtypes, mapping, row_count: int) -> pd.Series:
    if col in get_constant_variables():
        cursor.execute(f"SELECT {quote_identifier(col)} FROM {table} LIMIT 1")
        row = cursor.fetchone()
        const_val = row[0] if row else None
        return pd.Series([const_val] * row_count)
    elif col in get_pseudo_variables():
        cursor.execute(f"SELECT * FROM {table}")
        raw_data = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(raw_data, columns=colnames)

        # Check if this table is a child with a known parent
        parent = None
        join_keys = []
        for p, spec in FK_DEPENDENCIES.items():
            children = spec["child_table"]
            if isinstance(children, str): children = [children]
            if table in children:
                parent = p
                join_keys = spec["join_columns"]
                break

        if parent and set(join_keys).issubset(df.columns) and col in join_keys:
            fk_map = foreign_key_pseudonym_maps.get(parent, {})
            unmatched = 0
            values = []
            for _, row in df.iterrows():
                key = tuple(row[k] for k in join_keys)
                if key not in fk_map:
                    unmatched += 1
                    values.append(row[col])  # fallback
                else:
                    values.append(fk_map[key][join_keys.index(col)])  
            if unmatched > 0:
                print(f"⚠️ Warning: {unmatched} unmatched FK rows in {table} for parent {parent}")
            return pd.Series(values)


        else:
            raw_values = df[col].tolist()
            processed = [
                generate_shared_pseudonym(col, table, cursor.connection, val)
                for val in raw_values
            ]
            return pd.Series(processed)

    else:
        cursor.execute(f"SELECT {quote_identifier(col)} FROM {table}")
        data = pd.Series([row[0] for row in cursor.fetchall()])

        dt = get_data_type(col)  # per-column type detection
        data = clean_data(data, dt)
        data = shuffle_column(data)
        data = force_k(data, dt, k=K)

        return data

def process_table(table: str, cursor, dtypes, pools) -> pd.DataFrame:
    columns = get_columns(table, cursor)

    # FK pre-filtering for child tables
    parent = None
    join_keys = []
    for p, spec in FK_DEPENDENCIES.items():
        children = spec["child_table"]
        if isinstance(children, str): children = [children]
        if table in children:
            parent = p
            join_keys = spec["join_columns"]
            break

    if parent:
        quoted_keys = ','.join([f'"{key}"' for key in join_keys])
        cursor.execute(f'SELECT {quoted_keys} FROM {parent}')
        valid_fk_set = set(cursor.fetchall())

        cursor.execute(f'SELECT * FROM {table}')
        raw_data = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(raw_data, columns=colnames)

        before = len(df)
        df = df[df.apply(lambda row: tuple(row[key] for key in join_keys) in valid_fk_set, axis=1)]
        after = len(df)
        if before != after:
            print(f"⚠️ Dropped {before - after} orphan rows in {table} not matching FK in raw {parent}")

        row_count = len(df)

        # Store mapping for foreign key reuse
        if table in UNIQUE_KEYS and table in FK_DEPENDENCIES:
            join_keys = UNIQUE_KEYS[table]
            foreign_key_pseudonym_maps[table] = {
                tuple(original_vals): tuple(
                    generate_shared_pseudonym(col, table, cursor.connection, original_vals[i])
                    for i, col in enumerate(join_keys)
                )
                for original_vals in df[join_keys].itertuples(index=False, name=None)
            }

        if row_count <= 1:
            print(f"⚠️ Skipping {table} — only {row_count} row(s) after FK filtering.")
            return pd.DataFrame()
    else:
        cursor.execute(f'SELECT * FROM {table}')
        raw_data = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(raw_data, columns=colnames)
        row_count = len(df)

        # Store mapping for foreign key reuse
        if table in UNIQUE_KEYS and table in FK_DEPENDENCIES:
            join_keys = UNIQUE_KEYS[table]
            foreign_key_pseudonym_maps[table] = {
                tuple(original_vals): tuple(
                    generate_shared_pseudonym(col, table, cursor.connection, original_vals[i])
                    for i, col in enumerate(join_keys)
                )
                for original_vals in df[join_keys].itertuples(index=False, name=None)
            }


    data_dict = {}
    for col in columns:
        print(f"Processing column: {col}")
        data_dict[col] = process_column(col, table, cursor, dtypes, pools, row_count)

    return pd.DataFrame(data_dict)

FK_DEPENDENCIES = {
    "versq": {
        "child_table": "versqdmp",
        "join_columns": ["PSID", "VERSQ"]
    },
    "rez": {
        "child_table": "ezd",
        "join_columns": ["REZNR"]
    },
    "ambfall": {
        "child_table": ["ambdiag", "ambleist", "ambops"],
        "join_columns": ["FALLIDAMB"]
    },
    "khfall": {
        "child_table": ["khfa", "khdiag", "khproz", "khentg"],
        "join_columns": ["FALLIDKH"]
    },
    "zahnfall": {
        "child_table": ["zahnleist", "zahnbef"],
        "join_columns": ["FALLIDZAHN"]
    }
}

UNIQUE_KEYS = {
    "versq": ["PSID", "VERSQ"],
    "versqdmp": ["PSID", "VERSQ"],
    "rez": ["REZNR"],
    "ezd": ["REZNR"],
    "ambfall": ["FALLIDAMB"],
    "ambdiag": ["FALLIDAMB"],
    "ambleist": ["FALLIDAMB"],
    "ambops": ["FALLIDAMB"],
    "khfall": ["FALLIDKH"],
    "khfa": ["FALLIDKH"],
    "khdiag": ["FALLIDKH"],
    "khproz": ["FALLIDKH"],
    "khentg": ["FALLIDKH"],
    "zahnfall": ["FALLIDZAHN"],
    "zahnleist": ["FALLIDZAHN"],
    "zahnbef": ["FALLIDZAHN"]
}

def write_table_to_postgres(table: str, df: pd.DataFrame, target_cursor, target_conn):

    for parent, spec in FK_DEPENDENCIES.items():
        children = spec["child_table"]
        if isinstance(children, str): children = [children]
        if table in children:
            parent_table = f"{parent}_puf"
            join_keys = spec["join_columns"]

            query = f'SELECT {",".join([quote_identifier(k) for k in join_keys])} FROM {parent_table}'
            target_cursor.execute(query)
            valid_fk_pairs = set(target_cursor.fetchall())

            before = len(df)
            df = df[df.apply(lambda row: tuple(row[k] for k in join_keys) in valid_fk_pairs, axis=1)]
            after = len(df)

            if before != after:
                print(f"⚠️ Skipped {before - after} {table} rows not in {parent_table}")
            break

    if table in UNIQUE_KEYS:
        subset = UNIQUE_KEYS[table]
        before = len(df)
        df = df.groupby(subset).first().reset_index()
        after = len(df)
        if before != after:
            print(f"⚠️ Dropped {before - after} duplicate rows based on {subset}")

    if df.empty:
        print(f"⚠️  Skipping write for {table} — no data.")
        return

    target_table = f"{table}_puf"
    quoted_headers = ','.join([quote_identifier(col) for col in df.columns])
    placeholders = ','.join(['%s'] * len(df.columns))

    for _, row in df.iterrows():
        target_cursor.execute(
            f"INSERT INTO {target_table} ({quoted_headers}) VALUES ({placeholders})",
            [row_val if not pd.isna(row_val) else None for row_val in row]
        )
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Anonymize DM3 Seeder DB and write to PUF DB")
    parser.add_argument("--dsn", default="postgres")
    parser.add_argument("--source_db", default=os.getenv("DB_NAME"))
    parser.add_argument("--source_username", default=os.getenv("DB_USER"))
    parser.add_argument("--source_password", default=os.getenv("DB_PASSWORD"))
    parser.add_argument("--target_db", default=os.getenv("PUF_DB_NAME"))
    parser.add_argument("--target_username", default=os.getenv("PUF_DB_USER"))
    parser.add_argument("--target_password", default=os.getenv("PUF_DB_PASSWORD"))
    parser.add_argument("--tables", nargs='+', default=os.getenv("PUF_TABLES", "").split())

    args = parser.parse_args()
    if not all([args.source_db, args.source_username, args.source_password]):
        raise EnvironmentError(" Missing Seeder DB credentials in .env or CLI")
    if not all([args.target_db, args.target_username, args.target_password]):
        raise EnvironmentError(" Missing PUF DB credentials in .env or CLI")
    if not args.tables:
        raise EnvironmentError(" No tables specified — set PUF_TABLES in .env or pass via CLI")

    args.tables = [t.lower() for t in args.tables]
    read_conn, read_cursor = connect_to_database(args.dsn, args.source_username, args.source_password, dbname=args.source_db)
    write_conn, write_cursor = connect_to_database(args.dsn, args.target_username, args.target_password, dbname=args.target_db)

    dtypes = get_data_types()
    pseudo_map = get_pseudo_mapping()
    global_mapping = {}

    # Store FK pseudonym mappings
    foreign_key_pseudonym_maps = {}

    def generate_shared_pseudonym(variable, table, conn, original_value):
        # Special case: PSID must be globally consistent across tables
        if variable == "PSID":
            key = (variable, original_value)
        else:
            key = (variable, table, original_value)

        if key not in global_mapping:
            global_mapping[key] = generate_pseudonym(variable, table=table, conn=conn, original_value=original_value)
        return global_mapping[key]

    pools = {}
    for key in pseudo_map:
        pools[key] = generate_pool_of_ids(key, pseudo_map[key], read_cursor, read_conn)
    for key, val in get_secondary_pools_dm3().items():
        pools[key] = pools[val]

    begin = datetime.now()
    for table in args.tables:
        print(f"\n🔐 Anonymizing: {table}")
        df = process_table(table, read_cursor, dtypes, pools)
        write_table_to_postgres(table, df, write_cursor, write_conn)

        write_conn.commit()
        print(f" Commit complete for {table}")
        time.sleep(2) 

    read_conn.close()
    write_conn.close()
    print(f"\n Done. Total time: {datetime.now() - begin}")
