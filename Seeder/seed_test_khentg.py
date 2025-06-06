import random
import psycopg2
from datetime import date, timedelta
import string

# Date generator reused
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")

# Synthetic ENTGART pool (can be replaced with real Schlüssel 4 values)
def generate_entgart() -> str:
    """
    Generates a synthetic ENTGART value (billing type), 8-character alphanumeric.
    In practice, should be replaced by official Schlüssel 4 codes.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Billing amount generator
def generate_entgbetrag() -> float:
    """Generates a realistic billing amount between 100 and 20000 euros."""
    return round(random.uniform(100, 20000), 2)

# Number of billed items
def generate_entgzahl() -> str:
    """Returns a realistic 1–3 digit count of billed items."""
    return f"{random.randint(1, 120):03d}"

# Days above threshold
def generate_tageobe() -> str:
    """
    Generates a realistic 1–3 digit string for unbilled days (TAGEOBE).
    Most common values are 0 to 30.
    """
    return str(random.randint(0, 30))


# Main seeding function
def seed_khentg_table(conn, rows: int = 500):
    cur = conn.cursor()

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khdiag";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khentg.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)

        entgart = generate_entgart()
        entgbetrag = generate_entgbetrag()
        abrvondat = random_date_in_year(bjahr)
        abrbisdat = random_date_in_year(bjahr)
        entgzahl = generate_entgzahl()
        tageobe = generate_tageobe()
        datenmodell = 3

        # Ensure ABRBISDAT is not before ABRVONDAT
        if abrbisdat < abrvondat:
            abrvondat, abrbisdat = abrbisdat, abrvondat

        cur.execute("""
            INSERT INTO "khentg" (
                "VSID", "PSID", "FALLIDKH",
                "ENTGART", "ENTGBETRAG", "ABRVONDAT", "ABRBISDAT",
                "ENTGZAHL", "TAGEOBE", "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            entgart, entgbetrag, abrvondat, abrbisdat,
            entgzahl, tageobe, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khentg'.")

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
        seed_khentg_table(conn, rows=500)
    finally:
        conn.close()
