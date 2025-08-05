import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from functions_class3 import (
    homomorphic_encrypt,
    apply_differential_privacy
)

load_dotenv()

# ========== DB Connection ==========
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
        print(f"❌ PostgreSQL connection failed to {dbname}: {e}")
        return None, None

# ========== Get Variable Metadata ==========
def get_data_types():
    df = pd.read_csv("data_types.csv")
    return dict(zip(df["Variable"], df["Type"]))

def get_class3_technique(variable):
    df = pd.read_csv("data_processing_DM3_class3.csv")
    match = df[df["Variable"].str.upper() == variable.upper()]
    if not match.empty:
        return match.iloc[0]["PUF_3 Methode"]
    return None

# ========== DB Column Length ==========
def get_column_max_length(table: str, column: str, cursor) -> int:
    cursor.execute("""
        SELECT character_maximum_length 
        FROM information_schema.columns 
        WHERE UPPER(table_name) = %s AND UPPER(column_name) = %s
    """, (table.upper(), column.upper()))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 3  # fallback to safe short length

# ========== Data Cleaner ==========
def clean_data(column_data, dt, variable_name=None, max_len=None):

    technique = get_class3_technique(variable_name)

    # ⏳ Format conversion before anonymization
    if dt == "category":
        column_data = column_data.astype("category")

    elif dt == "date":
        column_data = column_data.astype(str).str.zfill(8)
        parsed = pd.to_datetime(column_data, format='%Y%m%d', errors='coerce')
        parsed = parsed.fillna(pd.Timestamp("2020-01-01"))
        column_data = parsed.dt.strftime('%Y%m%d').astype(int)

    elif dt == "year":
        column_data = pd.to_numeric(column_data, errors="coerce")
        column_data = column_data.apply(lambda x: 1930 if pd.notnull(x) and x < 1930 else x)
        column_data = column_data.fillna(1930).astype(int)

    elif dt == "integer":
        column_data = pd.to_numeric(column_data, errors="coerce").fillna(0).astype("Int64")

    elif dt == "float":
        column_data = pd.to_numeric(column_data, errors="coerce").fillna(0.0)

    # 🧠 Class 3 Anonymization Logic
    if technique == "Homomorphic Encryption":
        column_data = homomorphic_encrypt(column_data)

    elif technique == "Differential Privacy":
        column_data = apply_differential_privacy(column_data)

    # 🛡️ Ensure no NULLs for NOT NULL columns
    if variable_name and column_data.isnull().any():
        if dt == "integer":
            column_data = column_data.fillna(0)
        elif dt == "float":
            column_data = column_data.fillna(0.0)
        elif dt in ["category", "alphanumeric", "string"]:
            fallback = "X" if max_len == 1 else "XX"
            if pd.api.types.is_categorical_dtype(column_data):
                if fallback not in column_data.cat.categories:
                    column_data = column_data.cat.add_categories([fallback])
            column_data = column_data.fillna(fallback)

    return column_data
