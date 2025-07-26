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
from functions import force_k, generate_pseudonym, shuffle_column, _psid_map

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
                    values.append(row[col])
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
        dt = get_data_type(col)
        data = clean_data(data, dt)
        data = shuffle_column(data)
        if col not in get_pseudo_variables():
            data = force_k(data, dt, k=K)
        return data

def process_table(table: str, cursor, dtypes, pools) -> pd.DataFrame:
    columns = get_columns(table, cursor)

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
        for k in join_keys:
            if pd.api.types.is_object_dtype(df[k]) and isinstance(df[k].iloc[0], memoryview):
                df[k] = df[k].apply(lambda x: x.tobytes().hex() if isinstance(x, memoryview) else x)
        df = df[df.apply(lambda row: tuple(row[key] for key in join_keys) in valid_fk_set, axis=1)]
        after = len(df)
        if before != after:
            print(f"⚠️ Dropped {before - after} orphan rows in {table} not matching FK in raw {parent}")

        row_count = len(df)
        if row_count <= 1:
            print(f"⚠️ Skipping {table} — only {row_count} row(s) after FK filtering.")
            return pd.DataFrame()
    else:
        cursor.execute(f'SELECT * FROM {table}')
        raw_data = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(raw_data, columns=colnames)
        row_count = len(df)

    data_dict = {}
    for col in columns:
        print(f"Processing column: {col}")
        data_dict[col] = process_column(col, table, cursor, dtypes, pools, row_count)

    return pd.DataFrame(data_dict)

def write_table_to_postgres(table: str, df: pd.DataFrame, target_cursor, target_conn):
    # ✅ Guard clause to skip processing if DataFrame is empty (no rows, no columns)
    if df is None or df.empty or df.columns.empty:
        print(f"⚠️ Skipping write for {table} — no data to write.")
        return

    if table in UNIQUE_KEYS:
        subset = UNIQUE_KEYS[table]

        # ✅ Safe check before touching any column
        for col in subset:
            if col in df.columns and pd.api.types.is_object_dtype(df[col]) and isinstance(df[col].iloc[0], memoryview):
                df[col] = df[col].apply(lambda x: x.tobytes().hex() if isinstance(x, memoryview) else x)

        before = len(df)
        df = df.groupby(subset).first().reset_index()
        after = len(df)
        if before != after:
            print(f"⚠️ Dropped {before - after} duplicate rows based on {subset}")

    # ✅ Safe memoryview decoding for all other columns
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) and isinstance(df[col].iloc[0], memoryview):
            df[col] = df[col].apply(lambda x: x.tobytes().hex() if isinstance(x, memoryview) else x)

    df = df.where(pd.notna(df), None)

    target_table = f"{table}_puf"
    quoted_headers = ','.join([quote_identifier(col) for col in df.columns])
    placeholders = ','.join(['%s'] * len(df.columns))

    for _, row in df.iterrows():
        target_cursor.execute(
            f"INSERT INTO {target_table} ({quoted_headers}) VALUES ({placeholders})",
            list(row)
        )



FK_DEPENDENCIES = {
    "versq": {"child_table": "versqdmp", "join_columns": ["PSID", "VERSQ"]},
    "rez": {"child_table": "ezd", "join_columns": ["REZNR"]},
    "ambfall": {"child_table": ["ambdiag", "ambleist", "ambops"], "join_columns": ["FALLIDAMB"]},
    "khfall": {"child_table": ["khfa", "khdiag", "khproz", "khentg"], "join_columns": ["FALLIDKH"]},
    "zahnfall": {"child_table": ["zahnleist", "zahnbef"], "join_columns": ["FALLIDZAHN"]},
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
    args.tables = [t.lower() for t in args.tables]

    read_conn, read_cursor = connect_to_database(args.dsn, args.source_username, args.source_password, dbname=args.source_db)
    write_conn, write_cursor = connect_to_database(args.dsn, args.target_username, args.target_password, dbname=args.target_db)

    dtypes = get_data_types()
    pseudo_map = get_pseudo_mapping()
    global_mapping = {}
    foreign_key_pseudonym_maps = {}

    def generate_shared_pseudonym(variable, table, conn, original_value):
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
