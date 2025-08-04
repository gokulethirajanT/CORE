import os, argparse, csv
import pandas as pd
from datetime import datetime
from helpers_class2 import (
    connect_to_database, get_data_types, get_pseudo_variables,
    get_constant_variables, clean_data, get_column_max_length,
    get_class2_technique
)
from dotenv import load_dotenv
load_dotenv()

REPLACE_IDS = {}

def normalize_value(val):
    if isinstance(val, memoryview):
        val = val.tobytes().decode(errors='ignore')
    if pd.isna(val) or val in ("", "NaT", "nan", "NaN", "<NA>"):
        return None

    # 🧠 Properly cast numeric types
    if isinstance(val, float) and val.is_integer():
        return int(val)  # e.g., 123456789012.0 → 123456789012 (as int)
    elif isinstance(val, float):
        return round(val, 6)  # limit precision if truly float

    return str(val)[:20]  # truncate long strings


def get_columns(table: str, cursor):
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,))
    return [r[0] for r in cursor.fetchall()]

def process_table(table: str):
    print(f"🔐 Anonymizing (Class 2): {table}")
    dtypes = get_data_types()
    seeder_conn, cursor = connect_to_database(puf=False)

    # Step 1: Load all rows and columns from the original table
    cursor.execute(f'SELECT * FROM {table}')
    df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    # Step 2: Process each column based on its Class 2 technique
    for e, col in enumerate(df.columns):
        col_upper = col.upper()
        if col_upper not in dtypes:
            print(f"⚠️ Skipping column (no dtype found): {col}")
            continue

        dtype = dtypes[col_upper].lower()
        technique = get_class2_technique(col)
        max_len = get_column_max_length(table.lower(), col.lower(), cursor)

        print(f" Processing column: {col_upper} | Type: {dtype} | Technique: {technique}")

        try:
            if technique in [None, "None", "", float("nan")]:
                data = df[col]
            else:
                # Convert category to numeric if needed for Noise
                if technique == "Noise":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                data = clean_data(df[col], dtype, variable_name=col, max_len=max_len)

            # Step 3: Write to output_csv
            if e == 0:
                os.makedirs("output_csv", exist_ok=True)
                with open(f"output_csv/{table}.csv", "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([col_upper])
                    for val in data:
                        writer.writerow([normalize_value(val)])
            else:
                with open(f"output_csv/{table}.csv", "r") as f_in:
                    reader = list(csv.reader(f_in))
                    header, rows = reader[0], reader[1:]
                with open(f"output_csv/{table}.csv", "w", newline="") as f_out:
                    writer = csv.writer(f_out)
                    writer.writerow(header + [col_upper])
                    for i, row in enumerate(rows):
                        row.append(normalize_value(data.iloc[i]))
                        writer.writerow(row)

        except Exception as err:
            print(f"❌ Error processing {col}: {err}")
            continue

    cursor.close()
    seeder_conn.close()

def write_to_puf_db(table: str):
    table_name = f"{table}_puf"
    print(f" Attempting to insert into table: {table_name}")
    csv_path = f"output_csv/{table}.csv"

    if not os.path.exists(csv_path):
        print(f" CSV file not found: {csv_path}")
        return

    print(f" File found. Proceeding to open...")
    puf_conn, puf_cursor = connect_to_database(puf=True)

    try:
        with open(csv_path, "r") as f:
            print(f" File opened successfully: {csv_path}")
            reader = csv.reader(f)
            try:
                columns = next(reader)
                columns = [col.lower() for col in columns]
            except StopIteration:
                print(f" CSV file is empty: {csv_path}")
                return

            print(f" Columns loaded: {columns}")
            placeholders = ", ".join(["%s"] * len(columns))
            column_names = ', '.join([f'"{col.upper()}"' for col in columns])
            insert_sql = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'

            for i, row in enumerate(reader, start=1):
                cleaned_row = [normalize_value(v) for v in row]
                try:
                    puf_cursor.execute(insert_sql, cleaned_row)
                    if i % 100 == 0:
                        print(f" Inserted {i} rows...")
                except Exception as row_err:
                    print(f" Row {i} failed: {cleaned_row} | Error: {row_err}")

        puf_conn.commit()
        print(f" Finished inserting into: {table_name}")

    except Exception as e:
        print(f" General failure during insert into {table_name}: {e}")

    finally:
        puf_cursor.close()
        puf_conn.close()
        print(f" Database connection closed.")

if __name__ == "__main__":
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", nargs="+", help="List of tables to process")
    args = parser.parse_args()

    for table in args.tables:
        print(f"\n🔐 Anonymizing (Class 2): {table}")
        start = time.time()

        try:
            print("⏳ Calling process_table()...")
            process_table(table)
            print("✅ process_table() finished.")
        except Exception as e:
            print(f"❌ Error during process_table('{table}'): {e}")
            continue

        try:
            print("⏳ Calling write_to_puf_db()...")
            write_to_puf_db(table)
            print("✅ write_to_puf_db() finished.")
        except Exception as e:
            print(f"❌ Error during write_to_puf_db('{table}'): {e}")

        print(f"⏱ Table {table} done in {round(time.time() - start, 2)}s")
