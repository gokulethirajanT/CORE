import random
import sys
import argparse
from pathlib import Path
import csv
import pandas as pd
import warnings
from datetime import datetime
from multiprocessing import Pool, cpu_count

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

warnings.simplefilter(action='ignore', category=UserWarning)
K = 3

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def quote_identifier(identifier: str) -> str:
    return f'"{identifier}"'

def get_columns(table: str, cursor) -> list:
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE LOWER(table_name) = LOWER('{table}')")
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
        print(f"Fetching column {col} from database...")
        cursor.execute(f"SELECT {quote_identifier(col)} FROM {table}")
        data = pd.Series([row[0] for row in cursor.fetchall()])

        dt = dtypes.get(col)
        if dt:
            print(f"Cleaning {col}...")
            data = clean_data(data, dt)
            print(f"Shuffling {col}...")
            data = shuffle_column(data)
            print(f"Applying k-anonymity to {col} (k={K})...")
            data = force_k(data, dt, k=K)

        return data

def process_table(table: str, args: argparse.Namespace):
    conn, cursor = connect_to_database(args.dsn, args.username, args.password)
    dtypes = get_data_types()
    columns = get_columns(table, cursor)

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    if row_count <= 1:
        print(f"⚠️  Skipping {table} — only {row_count} row(s) (likely metadata-only).")
        conn.close()
        return

    pseudo_map = get_pseudo_mapping()
    pools = {key: generate_pool_of_ids(key, pseudo_map[key], cursor) for key in pseudo_map}
    for key, val in get_secondary_pools_dm3().items():
        pools[key] = pools[val]

    temp_csvs = []

    for i, col in enumerate(columns):
        print(f"Processing column {col}...")
        col_data = process_column(col, table, cursor, dtypes, pools, row_count)
        temp_path = OUTPUT_DIR / f"{table}_{i}.csv"
        temp_csvs.append(temp_path)

        if i == 0:
            with open(temp_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([col])
                for val in col_data:
                    writer.writerow([val])
        else:
            with open(temp_csvs[i - 1], "r") as f_in, open(temp_path, "w", newline="") as f_out:
                reader = csv.reader(f_in)
                writer = csv.writer(f_out)
                headers = next(reader)
                writer.writerow(headers + [col])
                for row, val in zip(reader, col_data):
                    writer.writerow(row + [val])
            temp_csvs[i - 1].unlink()

    final_csv = OUTPUT_DIR / f"{table}.csv"
    if final_csv.exists():
        final_csv.unlink()
    temp_csvs[-1].rename(final_csv)
    conn.close()

def write_table_to_postgres(table: str, args: argparse.Namespace):
    conn, cursor = connect_to_database(args.dsn, args.username, args.password)
    csv_file = OUTPUT_DIR / f"{table}.csv"
    if not csv_file.exists():
        print(f"⚠️  Skipping write for {table} — no generated CSV.")
        conn.close()
        return

    target_table = f"{table}_puf"
    with csv_file.open("r") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            placeholders = ','.join(['%s'] * len(row))
            quoted_headers = ','.join([quote_identifier(h) for h in headers])
            cursor.execute(f"INSERT INTO {target_table} ({quoted_headers}) VALUES ({placeholders})", row)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate DM3 PUF data into PostgreSQL")
    parser.add_argument("--dsn", default="postgres", help="Data source (only 'postgres' supported)")
    parser.add_argument("--username", required=True, help="Database username")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--tables", nargs='+', required=True, help="List of table names to process")
    parser.add_argument("--multi_threading", action='store_true', help="Use multiprocessing for table generation")
    args = parser.parse_args()
    args.tables = [t.lower() for t in args.tables]

    begin = datetime.now()

    if args.multi_threading:
        with Pool(min(len(args.tables), cpu_count())) as pool:
            pool.map(lambda t: process_table(t, args), args.tables)
    else:
        for table in args.tables:
            print(f"\n--- Processing table: {table} ---")
            process_table(table, args)
            print(f"Writing table {table} to database...")
            write_table_to_postgres(table, args)

    print(f"\n All tables processed in {datetime.now() - begin}.")
