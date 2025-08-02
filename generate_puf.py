import os, argparse, csv
import pandas as pd
from datetime import datetime
from helpers import (
    connect_to_database, get_data_types, get_pseudo_variables,
    get_constant_variables, clean_data, get_column_max_length
)
from functions import force_k, generate_pseudonym, shuffle_column
from dotenv import load_dotenv
load_dotenv()

REPLACE_IDS = {}
K = 3

def get_columns(table: str, cursor):
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,))
    return [r[0] for r in cursor.fetchall()]

def process_table(table: str):
    dtypes = get_data_types()
    columns = []

    seeder_conn, seeder_cursor = connect_to_database(puf=False)
    seeder_cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,))
    columns = [row[0] for row in seeder_cursor.fetchall()]

    for e, col in enumerate(columns):
        # ⚠️ Reuse the same cursor instead of reconnecting every time
        seeder_cursor.execute(f'SELECT "{col}" FROM {table}')
        data = pd.Series([row[0] for row in seeder_cursor.fetchall()])

        data_type = dtypes.get(col.upper(), "string").lower()

        # 🧪 PRINT raw date values before cleaning
        if col.upper() in ["VODAT", "ABGABEDAT"]:
            print(f"\n🧪 RAW DATA for column '{col}':")
            print(data.head(10))  # Show first 10 values before any processing
            
        if col in get_constant_variables():
            pass  # Leave unchanged
        elif col in get_pseudo_variables():
            #  Use actual max length from DB schema
            max_len = get_column_max_length(table, col, seeder_cursor)
            for val in data.unique():
                if val not in REPLACE_IDS:
                    REPLACE_IDS[val] = generate_pseudonym(variable=col, length=max_len)
            data = data.map(REPLACE_IDS)
        elif data_type == "pseudo":
            continue  # Skip special pseudonyms like FALLIDAMB, REZNR
        else:
            print(f" Cleaning column: {col} | Type: {data_type}")
            data = clean_data(data, data_type)
            data = shuffle_column(data)
            data = force_k(data, data_type, K)

        #  Write to CSV
        if e == 0:
            os.makedirs("output_csv", exist_ok=True)
            with open(f"output_csv/{table}.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([col.upper()])
                for val in data:
                    writer.writerow([val])
        else:
            with open(f"output_csv/{table}.csv", "r") as f_in:
                reader = list(csv.reader(f_in))
                header, rows = reader[0], reader[1:]
            with open(f"output_csv/{table}.csv", "w", newline="") as f_out:
                writer = csv.writer(f_out)
                writer.writerow(header + [col.upper()])
                for i, row in enumerate(rows):
                    row.append(data.iloc[i])
                    writer.writerow(row)

    #  Close connection only once at the end
    seeder_cursor.close()
    seeder_conn.close()



def write_to_puf_db(table: str):
    table_name = f"{table}_puf"  # ← Adjusted to use correct table name in DM3_PUF_1

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

            print(f" Prepared INSERT SQL: {insert_sql}")

            for i, row in enumerate(reader, start=1):
                cleaned_row = [None if v in ("", "NaT", "nan", "NaN", "<NA>") else v for v in row]
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
        print(f"\n Anonymizing: {table}")
        
        start = time.time()

        try:
            print(" Calling process_table()...")
            process_table(table)
            print(" process_table() finished.")
        except Exception as e:
            print(f" Error during process_table('{table}'): {e}")
            continue

        try:
            print(" Calling write_to_puf_db()...")
            write_to_puf_db(table)
            print(" write_to_puf_db() finished.")
        except Exception as e:
            print(f" Error during write_to_puf_db('{table}'): {e}")

        print(f"⏱ Table {table} done in {round(time.time() - start, 2)}s")

