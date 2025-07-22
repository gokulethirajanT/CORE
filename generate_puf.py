import random
import sys
import argparse
import pandas as pd
import warnings
from datetime import datetime
from dotenv import load_dotenv
import os

from helpers import (
    connect_to_database,
    get_data_types,
    get_pseudo_variables,
    get_constant_variables,
    clean_data,
    get_pseudo_mapping,
    get_secondary_pools_dm3
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

def generate_pool_of_ids(variable: str, source_table: str, cursor) -> list:
    cursor.execute(f"SELECT DISTINCT {quote_identifier(variable)} FROM {source_table}")
    return [generate_pseudonym(variable) for _ in cursor.fetchall()]

def process_column(col: str, table: str, cursor, dtypes, mapping, row_count: int) -> pd.Series:
    if col in get_constant_variables():
        cursor.execute(f"SELECT {quote_identifier(col)} FROM {table} LIMIT 1")
        row = cursor.fetchone()
        const_val = row[0] if row else None
        return pd.Series([const_val] * row_count)

    elif col in get_pseudo_variables():
        pool = mapping.get(col, [generate_pseudonym(col) for _ in range(row_count)])
        return pd.Series([pool[i % len(pool)] for i in range(row_count)])

    else:
        cursor.execute(f"SELECT {quote_identifier(col)} FROM {table}")
        data = pd.Series([row[0] for row in cursor.fetchall()])

        dt = dtypes.get(col)
        if dt:
            data = clean_data(data, dt)
            data = shuffle_column(data)
            data = force_k(data, dt, k=K)

        return data

def process_table(table: str, cursor, dtypes, pools) -> pd.DataFrame:
    columns = get_columns(table, cursor)
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]

    if row_count <= 1:
        print(f"⚠️  Skipping {table} — only {row_count} row(s).")
        return pd.DataFrame()

    data_dict = {}
    for col in columns:
        print(f"Processing column: {col}")
        data_dict[col] = process_column(col, table, cursor, dtypes, pools, row_count)

    return pd.DataFrame(data_dict)

def write_table_to_postgres(table: str, df: pd.DataFrame, target_cursor, target_conn):
    if df.empty:
        print(f"⚠️  Skipping write for {table} — no data.")
        return

    target_table = f"{table}_puf"
    quoted_headers = ','.join([quote_identifier(col) for col in df.columns])
    placeholders = ','.join(['%s'] * len(df.columns))

    for _, row in df.iterrows():
        target_cursor.execute(
            f"INSERT INTO {target_table} ({quoted_headers}) VALUES ({placeholders})",
            list(row)
        )
    target_conn.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Anonymize DM3 Seeder DB and write to PUF DB")
    parser.add_argument("--dsn", default="postgres", help="Data source (PostgreSQL only)")
    parser.add_argument("--source_username", default=os.getenv("DB_USER"), help="Seeder DB username")
    parser.add_argument("--source_password", default=os.getenv("DB_PASSWORD"), help="Seeder DB password")
    parser.add_argument("--target_username", default=os.getenv("PUF_DB_USER"), help="PUF DB username")
    parser.add_argument("--target_password", default=os.getenv("PUF_DB_PASSWORD"), help="PUF DB password")
    parser.add_argument("--source_db", required=True, help="Name of seeder database (e.g., CORE_MASTER_THESIS)")
    parser.add_argument("--target_db", required=True, help="Name of PUF database (e.g., dm3_puf_1)")
    parser.add_argument("--tables", nargs='+', required=True, help="List of tables to process")
    args = parser.parse_args()
    args.tables = [t.lower() for t in args.tables]

    # Safety check: ensure credentials are available
    if not args.source_username or not args.source_password:
        raise EnvironmentError(" Missing Seeder DB credentials in CLI or .env")

    if not args.target_username or not args.target_password:
        raise EnvironmentError(" Missing PUF DB credentials in CLI or .env")

    # ─── Open DB connections ─────────────────────────────────
    read_conn, read_cursor = connect_to_database(args.dsn, args.source_username, args.source_password, dbname=args.source_db)
    write_conn, write_cursor = connect_to_database(args.dsn, args.target_username, args.target_password, dbname=args.target_db)


    # ─── Anonymization Setup ─────────────────────────────────
    dtypes = get_data_types()
    pseudo_map = get_pseudo_mapping()
    pools = {key: generate_pool_of_ids(key, pseudo_map[key], read_cursor) for key in pseudo_map}
    for key, val in get_secondary_pools_dm3().items():
        pools[key] = pools[val]

    begin = datetime.now()

    for table in args.tables:
        print(f"\n🔐 Anonymizing: {table}")
        df = process_table(table, read_cursor, dtypes, pools)
        write_table_to_postgres(table, df, write_cursor, write_conn)

    read_conn.close()
    write_conn.close()

    print(f"\n✅ Done. Total time: {datetime.now() - begin}")
