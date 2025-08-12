# create_delta_tables.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

PUF_URL    = os.getenv("DATABASE_URL")        # e.g., DM3_PUF_1
SEEDER_URL = os.getenv("BASELINE_DB_URL")     # e.g., DM3_SEEDER

if not PUF_URL or not SEEDER_URL:
    raise SystemExit("Missing DATABASE_URL or BASELINE_DB_URL in .env")

# --- Helpers -----------------------------------------------------------------
def run_sql_script(engine, sql_blob: str, label: str = ""):
    """
    Execute multiple SQL statements separated by ';' inside a single transaction.
    Compatible with SQLAlchemy 2.0.
    """
    stmts = [s.strip() for s in sql_blob.split(";") if s.strip()]
    try:
        with engine.begin() as conn:  # transaction; commits on success
            for s in stmts:
                conn.exec_driver_sql(s)
    except SQLAlchemyError as e:
        raise RuntimeError(f"{label} failed on statement:\n{s}\nError: {e}") from e

def scalar_count(engine, table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()

# --- SQL (Seeder) -------------------------------------------------------------
SEEDER_SQL = r"""
-- Latest gender per person from versq (population DB)
DROP TABLE IF EXISTS vers_qi_seed_gender;
CREATE TABLE vers_qi_seed_gender AS
SELECT DISTINCT ON ("VSID")
       "VSID", "GESCHLECHT"
FROM versq
ORDER BY "VSID", "BJAHR" DESC, "VERSQ" DESC;

-- Presence QIs: PLZ3 (digits-only → pad → left 3), decade of birth, gender
DROP TABLE IF EXISTS vers_qi_seed_plus;
CREATE TABLE vers_qi_seed_plus AS
SELECT
  v."VSID",
  LEFT(LPAD(NULLIF(regexp_replace(COALESCE(v."PLZ", ''), '[^0-9]', '', 'g'), ''), 5, '0'), 3) AS "PLZ3",
  (FLOOR(v."GEBJAHR"/10)*10)::int AS "GEBJAHR_BAND",
  g."GESCHLECHT"
FROM vers v
LEFT JOIN vers_qi_seed_gender g USING ("VSID");

CREATE INDEX IF NOT EXISTS vers_qi_seed_plus_plz3_idx ON vers_qi_seed_plus ("PLZ3");
CREATE INDEX IF NOT EXISTS vers_qi_seed_plus_gebband_idx ON vers_qi_seed_plus ("GEBJAHR_BAND");
CREATE INDEX IF NOT EXISTS vers_qi_seed_plus_geschl_idx ON vers_qi_seed_plus ("GESCHLECHT");
CREATE INDEX IF NOT EXISTS vers_qi_seed_plus_vsid_idx ON vers_qi_seed_plus ("VSID");
"""

# --- SQL (PUF) ---------------------------------------------------------------
PUF_SQL = r"""
-- Latest gender per person from versq_puf (PUF DB)
DROP TABLE IF EXISTS vers_qi_puf_gender;
CREATE TABLE vers_qi_puf_gender AS
SELECT DISTINCT ON ("VSID")
       "VSID", "GESCHLECHT"
FROM versq_puf
ORDER BY "VSID", "BJAHR" DESC, "VERSQ" DESC;

-- Presence QIs: PLZ3 (digits-only → pad → left 3), decade of birth, gender
DROP TABLE IF EXISTS vers_qi_puf_plus;
CREATE TABLE vers_qi_puf_plus AS
SELECT
  v."VSID",
  LEFT(LPAD(NULLIF(regexp_replace(COALESCE(v."PLZ", ''), '[^0-9]', '', 'g'), ''), 5, '0'), 3) AS "PLZ3",
  (FLOOR(v."GEBJAHR"/10)*10)::int AS "GEBJAHR_BAND",
  g."GESCHLECHT"
FROM vers_puf v
LEFT JOIN vers_qi_puf_gender g USING ("VSID");

CREATE INDEX IF NOT EXISTS vers_qi_puf_plus_plz3_idx ON vers_qi_puf_plus ("PLZ3");
CREATE INDEX IF NOT EXISTS vers_qi_puf_plus_gebband_idx ON vers_qi_puf_plus ("GEBJAHR_BAND");
CREATE INDEX IF NOT EXISTS vers_qi_puf_plus_geschl_idx ON vers_qi_puf_plus ("GESCHLECHT");
CREATE INDEX IF NOT EXISTS vers_qi_puf_plus_vsid_idx ON vers_qi_puf_plus ("VSID");
"""

# --- Main --------------------------------------------------------------------
def main():
    eng_seed = create_engine(SEEDER_URL, future=True)
    eng_puf  = create_engine(PUF_URL,    future=True)

    print("Creating δ-presence helper tables in SEEDER...")
    run_sql_script(eng_seed, SEEDER_SQL, label="SEEDER DDL")
    print(f"  vers_qi_seed_plus rows: {scalar_count(eng_seed, 'vers_qi_seed_plus')}")

    print("Creating δ-presence helper tables in PUF...")
    run_sql_script(eng_puf, PUF_SQL, label="PUF DDL")
    print(f"  vers_qi_puf_plus rows:  {scalar_count(eng_puf, 'vers_qi_puf_plus')}")

    print("Done.")

if __name__ == "__main__":
    main()
