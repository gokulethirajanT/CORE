import random
import psycopg2
from datetime import date, timedelta
import string
# FA generator based on Schlüssel 6 or fallback codes
def generate_fa() -> str:
    """
    Generates a valid 4-character Fachabteilung code.
    Uses synthetic Schlüssel 6 department codes (0100–0999) and fallback codes.
    """
    fallback = ["0000", "0001", "0002"]
    if random.random() < 0.1:
        return random.choice(fallback)
    return f"{random.randint(100, 999):04d}"  # e.g., 0100 to 0999
    
# Date generator reused
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")
# Main seeding function for KHFA
def seed_khfa_table(conn, rows: int = 500):
    cur = conn.cursor()

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khdiag";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khfa.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)
        fa = generate_fa()
        aufndat = random_date_in_year(bjahr)
        datenmodell = 3
        entlassdat = random_date_in_year(bjahr)
        if entlassdat < aufndat:
            aufndat, entlassdat = entlassdat, aufndat

        cur.execute("""
            INSERT INTO "khfa" (
                "VSID", "PSID", "FALLIDKH",
                "FA", "ENTLASSDAT", "BJAHR","BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            fa, entlassdat, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khfa'.")

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
        seed_khfa_table(conn, rows=1)
    finally:
        conn.close()
