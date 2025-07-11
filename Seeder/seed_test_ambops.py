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

# Define function to generate OPS Codes from the ops_catalogue  
def get_ops_code_pool(conn, limit=500): # [52] DIMDI / BfArM (2023)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "SCHLUESSELNUMMER" FROM "ops_catalogue" WHERE "SCHLUESSELNUMMER" IS NOT NULL;')
    raw_codes = [row[0] for row in cur.fetchall()]
    # Clean: remove dash and dot to match FDZ rules (e.g., '5-987.0' → '59870')
    cleaned = [code.replace("-", "").replace(".", "") for code in raw_codes if isinstance(code, str)]
    return random.sample(cleaned, min(limit, len(cleaned)))


OPS_LOKAL_VALUES = [None, "R", "L", "B"]  # None = unspecified; R = right, L = left, B = both sides

def generate_ops_lokal(): #[53] Martinez et al. (2006)
    """
    Randomly select OPS localization:
    - 95% chance of being None (not side-specific)
    - 5% chance split equally among 'R', 'L', 'B'
    """
    return random.choices(
        population=[None, "R", "L", "B"],
        weights=[95, 1.67, 1.67, 1.66],  # Adds up to 100
        k=1
    )[0]


# ───────────────────── main seeding routine ────────────────────────────────

def seed_ambops_table(conn, row_count: int = 1):
    cur = conn.cursor()
    OPS_CODE_POOL = get_ops_code_pool(conn)
    # reference patients (same as DM-3)
    cur.execute('SELECT "VSID", "PSID", "FALLIDAMB", "BJAHR", "BNR" FROM "ambfall";')
    ambfall_rows = cur.fetchall()
    if not ambfall_rows:
        raise ValueError("Table 'ambfall' is empty – nothing to link to.")

    fallid_tracker: dict[tuple[int,int],int] = {}

    for _ in range(row_count):
        vsid, psid, fallidamb, bjahr, bnr = random.choice(ambfall_rows)
 
        ops_code = random.choice(OPS_CODE_POOL) # [52] DIMDI / BfArM (2023)
        ops_lokal  = generate_ops_lokal() # [53] Martinez et al. (2006)
        ops_date   = yyyymmdd_int(random_service_date())
        datenmodell = 3  

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
    print(f"Inserted {row_count} synthetic rows into 'ambops'")

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
