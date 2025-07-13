import random
import psycopg2
from datetime import date, timedelta

# Define function to generate OPS Codes from the ops_catalogue  
# HIV-specific enrichment for PROZ field using known frequent OPS procedures
def get_hiv_enriched_proz_pool(conn, limit=500):  # [75] Marcus et al. (2021)
    """
    Return HIV-enriched OPS codes from the ops_catalogue.
    Codes include infectious disease monitoring, biopsies, lumbar puncture, etc.
    """
    hiv_keywords = [
        "immunsystem", "virus", "infektion", "lymphknoten",
        "rückenmark", "biopsie", "lungen", "leber", "haut", "abstrich"
    ]
    cur = conn.cursor()
    cur.execute('SELECT "SCHLUESSELNUMMER", "TITEL_LANG" FROM "ops_catalogue";')
    rows = cur.fetchall()
    
    filtered = [
        code.replace("-", "").replace(".", "")
        for code, title in rows
        if isinstance(code, str) and any(k in title.lower() for k in hiv_keywords)
    ]
    if not filtered:
        raise ValueError("No HIV-enriched OPS codes found.")
    return random.sample(filtered, min(limit, len(filtered)))


# Define static helper pools
# HIV-specific enrichment for PROZLOKAL (procedure laterality/site)
def generate_prozlokal(hiv_positive=True) -> str:  # [76] Bicanic et al. (2009)
    """
    Enrich procedure location for HIV-positive patients.
    HIV+ patients more likely to undergo procedures in bilateral or systemic locations.
    """
    if hiv_positive:
        return random.choices(["B", "L", "R", None], weights=[0.5, 0.2, 0.2, 0.1])[0]  # Bilateral bias
    else:
        return random.choices(["R", "L", "B", None], weights=[0.4, 0.4, 0.1, 0.1])[0]


# Random date generator
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")  # JJJJMMTT

# Generate synthetic KHPROZ data
def seed_khproz_table(conn, rows: int = 500):
    cur = conn.cursor()

    PROZ_CODE_POOL = get_hiv_enriched_proz_pool(conn)
    # Reference base from existing patients
    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khfall";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khproz.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)

        PROZ_CODE_POOL = get_hiv_enriched_proz_pool(conn) ## [94] Bicanic et al. (2009)
        proz = random.choice(PROZ_CODE_POOL) ## [94] Bicanic et al. (2009)
        prozdat = random_date_in_year(bjahr)
        prozlokal = generate_prozlokal(hiv_positive=True) ## [94] Bicanic et al. (2009)


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
