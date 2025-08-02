import random
import psycopg2
from datetime import datetime, timedelta
import string
from dotenv import load_dotenv
import os

load_dotenv()


def generate_diaglokal() -> str:
    """
    Return a completely random diagnosis laterality (DIAGLOKAL) with no enrichment.
    """
    return random.choice(['-', 'L', 'R', 'B'])

def get_weighted_icd_pool(conn, sti_ratio=0.5, total=1000):  # [51] WHO/CDC (2014); RKI Catalogue Crosscheck
    cur = conn.cursor()
    cur.execute('SELECT "SCHLÜSSELNUMMER", "TITEL_LANG" FROM "icd10_catalogue";')
    rows = cur.fetchall()

    #  ICD-10 codes confirmed to exist in your icd10_catalogue table (from WHO HIV surveillance guide)
    confirmed_sti_codes = {
        "B20", "B21", "B22", "B23", "B24",  # HIV disease codes
        "Z21",                             # Asymptomatic HIV
        "R75"                              # Inconclusive lab evidence of HIV
    }

    sti_icd = []
    non_sti_icd = []

    for code, title in rows:
        if not code:
            continue
        code_clean = code.strip().upper()
        if code_clean in confirmed_sti_codes:
            sti_icd.append(code_clean)
        else:
            non_sti_icd.append(code_clean)

    if not sti_icd or not non_sti_icd:
        raise ValueError("Could not find both STI and non-STI ICD codes.")

    sti_count = int(total * sti_ratio)
    non_sti_count = total - sti_count

    return random.choices(sti_icd, k=sti_count) + random.choices(non_sti_icd, k=non_sti_count)


def extract_icd_parts(code: str): 
    """Splits an ICD code into cleaned code and Zusatz (e.g. '.', '-', '!')."""
    if not code:
        return None, None
    for symbol in ['.', '-', '!']:
        if symbol in code:
            return code.replace(symbol, ''), symbol
    return code, None

def generate_diag_date(hiv_positive: bool = True) -> int:  # [50] BZgA – PrEP Monitoring Report (2023)
    """
    Return enriched diagnosis date (DIAGDAT) as YYYYMMDD integer.
    PrEP patients typically receive quarterly screenings, especially in Q2–Q4,
    and more frequently between 2020–2023 following TSVG regulations.
    """
    if hiv_positive:
        # Years reflect post-TSVG monitoring intensity
        year = random.choices([2019, 2020, 2021, 2022, 2023], weights=[2, 10, 20, 30, 38])[0]
        # Quarterly distribution favors Q2–Q4 for routine testing
        month = random.choices([3, 6, 9, 12], weights=[1, 3, 3, 3])[0]  # Q2–Q4 emphasis
    else:
        # Uniform random for non-HIV patients
        year = random.randint(2019, 2023)
        month = random.randint(1, 12)
    
    day = random.randint(1, 28)  # Safe for all months
    return int(f"{year}{month:02d}{day:02d}")


def seed_ambdiag_table(conn, row_count=1000):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT "VSID", "PSID", "FALLIDAMB", "BJAHR", "BNR"
        FROM "ambfall"
    """)
    ambfall_rows = cursor.fetchall()

    if not ambfall_rows:
        raise ValueError("No data found in 'ambfall'. Cannot seed 'ambdiag'.")

    fallid_tracker = {}

    ICD_POOL = get_weighted_icd_pool(conn, sti_ratio=0.6, total=1000)

    for _ in range(row_count):
        vsid, psid, fallidamb, bjahr, bnr = random.choice(ambfall_rows)

        diagsich = random.choice(['A', 'G', 'V', 'Z'])  
        diaglokal = generate_diaglokal()  
        diagdat = generate_diag_date()                      
        raw_icdamb_code = random.choice(ICD_POOL)
        icdamb_code, icdamb_zusatz = extract_icd_parts(raw_icdamb_code)# [51] Robert Koch-Institut (2023) #referenced from the TABLE icd10_catalogue
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cursor.execute("""
            INSERT INTO "ambdiag" (
                "FALLIDAMB", "VSID", "PSID", "DIAGSICH", "DIAGLOKAL", 
                "DIAGDAT", "ICDAMB_CODE", "ICDAMB_ZUSATZ", 
                "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            fallidamb, vsid, psid, diagsich, diaglokal,
            diagdat, icdamb_code, icdamb_zusatz,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {row_count} rows into 'ambdiag'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_ambdiag_table(conn)
    conn.close()
