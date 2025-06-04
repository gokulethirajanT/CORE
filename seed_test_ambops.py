import random
import psycopg2
from datetime import date, timedelta

"""Seed DM-7 table AMBOPS with synthetic OPS procedures."""

# ───────────────────── helper functions ─────────────────────────────────────

def random_service_date(start_year: int = 2019, end_year: int | None = None) -> date:
    if end_year is None:
        end_year = date.today().year
    start = date(start_year, 1, 1)
    end   = date(end_year,   12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def yyyymmdd_int(d: date) -> int:
    return int(d.strftime("%Y%m%d"))

# Simple generator for German OPS code strings (max 12 chars)
OPS_MAIN_CATEGORIES = ["1", "3", "5", "6", "8"]  # diagnostics, endoscopy, surgery, etc.

def generate_ops_code() -> str:
    chapter     = random.choice(OPS_MAIN_CATEGORIES)
    group       = f"{random.randint(100,999)}"   # 3-digit group
    sub_section = random.choice(["",
                                  f".{random.randint(0,99):02d}",
                                  f".{random.randint(0,99):02d}.{random.randint(0,9)}"])
    return f"{chapter}-{group}{sub_section}"

OPS_LOKAL_VALUES = [None, "R", "L", "B"]  # right, left, both, non-side-specific

def generate_ops_lokal():
    return random.choice(OPS_LOKAL_VALUES)

# ───────────────────── main seeding routine ────────────────────────────────

def seed_ambops_table(conn, row_count: int = 100):
    cur = conn.cursor()

    # reference patients (same as DM-3)
    cur.execute('SELECT "VSID", "PSID", "FALLIDAMB", "BJAHR", "BNR" FROM "ambfall";')
    ambfall_rows = cur.fetchall()
    if not ambfall_rows:
        raise ValueError("Table 'ambfall' is empty – nothing to link to.")

    fallid_tracker: dict[tuple[int,int],int] = {}

    for _ in range(row_count):
        vsid, psid, fallidamb, bjahr, bnr = random.choice(ambfall_rows)


        ops_code   = generate_ops_code()
        ops_lokal  = generate_ops_lokal()
        ops_date   = yyyymmdd_int(random_service_date())
        datenmodell = 3  #

        cur.execute(
            """
            INSERT INTO "ambops" (
              "VSID", "PSID", "FALLIDAMB",
              "OPS",  "OPSLOKAL", "OPSDAT",
              "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
              %s,%s,%s,%s,%s,%s,%s,%s,%s
            );""",
            (
                vsid, psid, fallidamb,
                ops_code, ops_lokal, ops_date,
                bjahr, bnr, datenmodell
            )
        )

    conn.commit()
    print(f"Inserted {row_count} rows into 'ambops'")

# ───────────────────── run directly ─────────────────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname   = "CORE_MASTER_THESIS",
        user     = "postgres",
        password = "London@123",
        host     = "localhost",
        port     = "5432"
    )
    try:
        seed_ambops_table(conn, row_count=1)
    finally:
        conn.close()
