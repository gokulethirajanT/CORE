import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_database(puf=False):
    """
    Connects to the PostgreSQL database. Switches between Seeder and PUF DB using `puf=True`.
    """
    dbname = os.getenv("PUF_DB_NAME") if puf else os.getenv("DB_NAME")
    user = os.getenv("PUF_DB_USER") if puf else os.getenv("DB_USER")
    password = os.getenv("PUF_DB_PASSWORD") if puf else os.getenv("DB_PASSWORD")
    host = os.getenv("PUF_DB_HOST") if puf else os.getenv("DB_HOST")
    port = os.getenv("PUF_DB_PORT") if puf else os.getenv("DB_PORT")

    try:
        conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        return conn, conn.cursor()
    except Exception as e:
        print(f" PostgreSQL connection failed to {dbname}: {e}")
        return None, None

def get_column_max_length(table: str, column: str, cursor) -> int:
    cursor.execute("""
        SELECT character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 19  # fallback to 19 if null


def get_pseudo_variables():
    df = pd.read_csv("data_processing_DM3.csv")
    return df[df["PUF Methode"] == "Pool"]["Datenfeldname"].str.upper().tolist()

def get_constant_variables():
    df = pd.read_csv("data_processing_DM3.csv")
    return df[df["PUF Methode"] == "Nichts"]["Datenfeldname"].str.upper().tolist()

def get_data_types():
    df = pd.read_csv("data_types.csv")
    return dict(zip(df["Variable"], df["Type"]))

def clean_data(column_data, dt):
    if dt == "category":
        return column_data.astype("category")
    elif dt == "date":
        return pd.to_datetime(column_data, errors='coerce').dt.strftime('%Y%m%d').astype('Int64')
    elif dt == "year":
        return pd.to_datetime(column_data, format='%Y', errors='coerce').dt.year
    elif dt == "float":
        return pd.to_numeric(column_data, errors="coerce")
    elif dt == "integer":
        try:
            return pd.to_numeric(column_data, errors="coerce").astype("Int64")
        except Exception as e:
            print(f" Failed to convert column to Int64:\n{column_data.head(10)}")
            print(" Error:", e)
            raise e
    else:
        return column_data
