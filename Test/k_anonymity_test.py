import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Load .env
load_dotenv()

# --- Config ---
PUF_VERS_TABLE = os.getenv("PUF_VERS_TABLE", "vers_puf")
K_TARGET = int(os.getenv("K_TARGET", 3))

def build_pg_url(prefix: str):
    user = os.getenv(f"{prefix}_DB_USER") or os.getenv("DB_USER")
    pwd = os.getenv(f"{prefix}_DB_PASSWORD") or os.getenv("DB_PASSWORD")
    host = os.getenv(f"{prefix}_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv(f"{prefix}_DB_PORT") or os.getenv("DB_PORT", "5432")
    name = os.getenv(f"{prefix}_DB_NAME") or os.getenv("DB_NAME")
    if not (user and pwd and host and port and name):
        return None
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"

DATABASE_URL = os.getenv("DATABASE_URL") or build_pg_url("PUF")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def table_exists(tbl: str) -> bool:
    """Check if table exists in public schema."""
    insp = inspect(engine)
    return insp.has_table(tbl, schema="public")

def get_columns(tbl: str):
    """Get column names for given table."""
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :tbl
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(sql, {"tbl": tbl}).all()]

def check_k_anonymity():
    if not table_exists(PUF_VERS_TABLE):
        return {"status": "FAIL", "reason": f"Missing table {PUF_VERS_TABLE}"}
    
    cols = get_columns(PUF_VERS_TABLE)
    qis = []
    if "PLZ" in cols:
        qis.append('LEFT("PLZ",3) AS PLZ3')
    if "GEBJAHR" in cols:
        qis.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS GEBJAHR_BAND')
    if "GESCHLECHT" in cols:
        qis.append('"GESCHLECHT"')
    
    if not qis:
        return {"status": "FAIL", "reason": "No quasi-identifiers found"}

    select = ", ".join(qis)
    groupby = ", ".join([q.split(" AS ")[-1] if " AS " in q else q for q in qis])
    sql = f'SELECT {select}, COUNT(*) AS n FROM {PUF_VERS_TABLE} GROUP BY {groupby};'

    df = pd.read_sql_query(sql, engine)
    if df.empty:
        return {"status": "FAIL", "reason": f"{PUF_VERS_TABLE} is empty"}

    min_k = int(df["n"].min())
    small = int((df["n"] < K_TARGET).sum())
    if min_k >= K_TARGET and small == 0:
        return {"status": "PASS", "min_k": min_k, "small_cells": small}
    return {"status": "FAIL", "min_k": min_k, "small_cells": small}

if __name__ == "__main__":
    print("Running only k_anonymity check...")
    result = check_k_anonymity()
    print(result)
