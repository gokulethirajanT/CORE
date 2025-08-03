import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from functions_class2 import (
    apply_top_coding, bucket_numeric, add_noise,
    micro_aggregate, mask_sensitive_text, swap_data
)

load_dotenv()

def connect_to_database(puf=False):
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
    return result[0] if result and result[0] else 19

def get_pseudo_variables():
    df = pd.read_csv("data_processing_DM3_class2.csv")
    return df[df["PUF_2 Methode"] == "Swapping"]["Datenfeldname"].str.upper().tolist()

def get_constant_variables():
    return []  # In Class 2 only, we don't preserve any variables as-is

def get_data_types():
    df = pd.read_csv("data_types.csv")
    return dict(zip(df["Variable"], df["Type"]))

def get_class2_technique(variable):
    df = pd.read_csv("data_processing_DM3_class2.csv")
    match = df[df["Datenfeldname"].str.upper() == variable.upper()]
    if not match.empty:
        return match.iloc[0]["PUF_2 Methode"]
    return "None"

def clean_data(column_data, dt, variable_name=None):
    technique = get_class2_technique(variable_name)

    if dt == "category":
        column_data = column_data.astype("category")

    elif dt == "date":
        column_data = column_data.astype(str).str.zfill(8)
        parsed = pd.to_datetime(column_data, format='%Y%m%d', errors='coerce')
        parsed = parsed.fillna(pd.Timestamp("2020-01-01"))
        column_data = parsed.dt.strftime('%Y%m%d').astype(int)

    elif dt == "year":
        column_data = pd.to_datetime(column_data, format='%Y', errors='coerce').dt.year

    elif dt == "integer":
        column_data = pd.to_numeric(column_data, errors="coerce").fillna(0).astype("Int64")

    elif dt == "float":
        column_data = pd.to_numeric(column_data, errors="coerce")


    # Apply Class 2 logic
    if technique == "Top-Coding":
        column_data = apply_top_coding(column_data)
    elif technique == "Bucketing":
        column_data = bucket_numeric(column_data, bins=[0, 1000, 2000, 3000, 5000, 10000])
    elif technique == "Noise":
        column_data = add_noise(column_data)
    elif technique == "Masking":
        column_data = mask_sensitive_text(column_data)
    elif technique == "Micro-Aggregation":
        column_data = micro_aggregate(column_data)
    elif technique == "Swapping":
        column_data = swap_data(column_data)

        if dt in ["integer", "year"]:
            column_data = pd.to_numeric(column_data, errors="coerce").fillna(0).astype("Int64")

        elif dt == "float":
            column_data = pd.to_numeric(column_data, errors="coerce").round(3)  # round to avoid long decimals

        elif dt == "category":
            column_data = column_data.astype("category")

        elif dt in ["alphanumeric", "string"]:
            column_data = column_data.astype(str).str[:20]


    return column_data
