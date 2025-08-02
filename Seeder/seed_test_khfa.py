import random
import psycopg2
from datetime import date, timedelta, datetime  
import string
from dotenv import load_dotenv
import os


load_dotenv()
# FA generator based on Schlüssel 6 or fallback codes
def generate_fa_hiv_enriched(hiv_positive=True) -> str: # [91] Deutsche AIDS-Hilfe (2021)
    """
    Generate HIV-enriched Fachabteilung (FA) codes.
    HIV+ patients are more likely to be admitted to internal medicine, dermatology, infectiology.
    """
    hiv_depts = ["0701", "0300", "0106"]  # Internal Medicine, Dermatology/Venereology, Infectiology
    fallback = ["0000", "0001", "0002"]
    
    if not hiv_positive:
        if random.random() < 0.1:
            return random.choice(fallback)
        return f"{random.randint(100, 999):04d}"  # Default random

    # HIV+ patients biased towards known departments
    if random.random() < 0.6:
        return random.choice(hiv_depts)
    elif random.random() < 0.1:
        return random.choice(fallback)
    else:
        return f"{random.randint(100, 999):04d}"

    
# Date generator reused

def random_date_in_year(year: int) -> str:
    """
    Returns a random date within the specified year in YYYYMMDD format.
    """
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    delta = timedelta(days=random.randint(0, (end - start).days))
    return (start + delta).strftime("%Y%m%d")

def generate_entlassdat_enriched(aufndat: str, max_days: int = 45) -> str:
    """
    Simulates longer inpatient stays for HIV+ patients with co-infections.
    ENTLASSDAT is calculated from AUFNDAT + [5–45] days.
    """
    start_date = datetime.strptime(aufndat, "%Y%m%d")
    delta_days = random.randint(5, max_days)
    entlass_date = start_date + timedelta(days=delta_days)
    return entlass_date.strftime("%Y%m%d")

# Main seeding function for KHFA
def seed_khfa_table(conn, rows: int = 1000):
    cur = conn.cursor()

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khfall";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khfa.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)
        fa = generate_fa_hiv_enriched() # [91] Deutsche AIDS-Hilfe (2021)
        aufndat = random_date_in_year(bjahr)
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)
        aufndat = random_date_in_year(bjahr) # [92] Buchacz, K., Baker, R. K., Palella, F. J., et al. (2010).
        entlassdat = generate_entlassdat_enriched(aufndat) # [92] Buchacz, K., Baker, R. K., Palella, F. J., et al. (2010).

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
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_khfa_table(conn)
    conn.close()
