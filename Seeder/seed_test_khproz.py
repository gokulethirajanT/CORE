import random
import psycopg2
from datetime import date, timedelta

# Define function to generate OPS Codes from the ops_catalogue  
def get_proz_code_pool(conn, limit=500):
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "SCHLUESSELNUMMER" FROM "ops_catalogue" WHERE "SCHLUESSELNUMMER" IS NOT NULL;')
    raw_codes = [row[0] for row in cur.fetchall()]
    # Clean: remove dash and dot to match FDZ rules (e.g., '5-987.0' → '59870')
    cleaned = [code.replace("-", "").replace(".", "") for code in raw_codes if isinstance(code, str)]
    return random.sample(cleaned, min(limit, len(cleaned)))

# Define static helper pools
PROZLOKAL_POOL = [None, "R", "L", "B"]

# Random date generator
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")  # JJJJMMTT

# Generate synthetic KHPROZ data
def seed_khproz_table(conn, rows: int = 500):
    cur = conn.cursor()

    PROZ_CODE_POOL = get_proz_code_pool(conn)
    # Reference base from existing patients
    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khdiag";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khproz.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)

        proz = random.choice(PROZ_CODE_POOL)  # remove dot for conformity
        prozdat = random_date_in_year(bjahr)
        prozlokal = random.choice(PROZLOKAL_POOL)

        datenmodell = 3

        cur.execute("""
            INSERT INTO "khproz" (
                "VSID", "PSID", "FALLIDKH",
                "PROZ", "PROZDAT", "PROZLOKAL",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            proz, prozdat, prozlokal,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khproz'.")

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432",
    )
    try:
        seed_khproz_table(conn, rows=1)
    finally:
        conn.close()
