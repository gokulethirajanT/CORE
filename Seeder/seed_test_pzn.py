import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Load PZN values from CSV
df = pd.read_csv("reference/pzn_prep_j05ar03.csv")  # Or full path

# Connect to seeder DB
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# Step 1: Create table (if not exists)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pzn_prep_j05ar03 (
        pzn VARCHAR(10) PRIMARY KEY
    );
""")

# Step 2: Insert PZN values
for pzn in df["PZN"]:
    cursor.execute("""
        INSERT INTO pzn_prep_j05ar03 (pzn)
        VALUES (%s)
        ON CONFLICT (pzn) DO NOTHING;
    """, (pzn,))

# Finalize
conn.commit()
cursor.close()
conn.close()

print(" PZN values inserted into 'pzn_prep_j05ar03' table.")
