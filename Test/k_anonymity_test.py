# k_anonymity_check.py
import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
PUF_VERS_TABLE = os.getenv("PUF_VERS_TABLE", "vers_puf")
K_TARGET = int(os.getenv("K_TARGET", 3))

def build_pg_url(prefix: str):
    user = os.getenv(f"{prefix}_DB_USER") or os.getenv("DB_USER")
    pwd  = os.getenv(f"{prefix}_DB_PASSWORD") or os.getenv("DB_PASSWORD")
    host = os.getenv(f"{prefix}_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv(f"{prefix}_DB_PORT") or os.getenv("DB_PORT", "5432")
    name = os.getenv(f"{prefix}_DB_NAME") or os.getenv("DB_NAME")
    if not (user and pwd and host and port and name):
        return None
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"

DATABASE_URL = os.getenv("DATABASE_URL") or build_pg_url("PUF")
engine = create_engine(DATABASE_URL)

def table_exists(tbl: str) -> bool:
    return inspect(engine).has_table(tbl, schema="public")

def get_columns(tbl: str):
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:tbl
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(sql, {"tbl": tbl}).all()]

def build_group_sql(tbl: str, cols: list[str]) -> tuple[str, list[str]]:
    """Return SQL that groups by available QIs (PLZ->PLZ3, GEBJAHR->5y band, optional GESCHLECHT) using a CTE."""
    select_parts, aliases = [], []

    if "PLZ" in cols:
        select_parts.append('LEFT("PLZ",3) AS "PLZ3"'); aliases.append('PLZ3')
    if "GEBJAHR" in cols:
        select_parts.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS "GEBJAHR_BAND"'); aliases.append('GEBJAHR_BAND')
    if "GESCHLECHT" in cols:
        select_parts.append('"GESCHLECHT"'); aliases.append('GESCHLECHT')

    if not aliases:
        raise RuntimeError("No quasi-identifiers found (need PLZ/GEBJAHR and optional GESCHLECHT).")

    select_qis = ", ".join(select_parts)
    alias_sql  = ", ".join(f'"{a}"' for a in aliases)

    sql = f"""
        WITH base AS (
            SELECT {select_qis}
            FROM {tbl}
        )
        SELECT {alias_sql}, COUNT(*)::bigint AS n
        FROM base
        GROUP BY {alias_sql}
        ORDER BY {alias_sql};
    """
    return sql, aliases

def check_k_anonymity():
    if not table_exists(PUF_VERS_TABLE):
        return {"status": "FAIL", "reason": f"Missing table {PUF_VERS_TABLE}"}

    cols = get_columns(PUF_VERS_TABLE)
    try:
        sql, group_cols = build_group_sql(PUF_VERS_TABLE, cols)
    except RuntimeError as e:
        return {"status": "FAIL", "reason": str(e)}

    df = pd.read_sql_query(text(sql), engine)
    if df.empty:
        return {"status": "FAIL", "reason": f"{PUF_VERS_TABLE} produced no groups"}

    # Save all groups
    groups_csv = "k_anonymity_groups.csv"
    df.to_csv(groups_csv, index=False)

    min_k = int(df["n"].min())
    viol_df = df[df["n"] < K_TARGET].copy()
    small = int(viol_df.shape[0])

    result = {
        "status": "PASS" if small == 0 else "FAIL",
        "min_k": min_k,
        "small_cells": small,
        "k_target": K_TARGET,
        "groups_csv": groups_csv
    }

    if small > 0:
        viol_csv = "k_anonymity_violations.csv"
        viol_df.to_csv(viol_csv, index=False)
        result["violations_csv"] = viol_csv

    return result

if __name__ == "__main__":
    print("Running k-anonymity check...")
    res = check_k_anonymity()
    print(res)
