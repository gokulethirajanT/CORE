import random
import psycopg2
from datetime import datetime, timedelta
import string

# HIV-specific enrichment for DIAGSICH
def generate_diagsich(hiv_positive: bool = True) -> str: # [33] Kojic et al. (2011) – HIV+ patients may receive 'probable' or 'suspected' diagnoses more often due to co-infections and overlapping symptoms.
    """
    Return enriched diagnosis certainty (DIAGSICH) based on HIV status.
    HIV+ patients more likely to receive 'V' (suspected) or 'G' (probable) codes.
    """
    if hiv_positive:
        return random.choices(['V', 'G', 'Z', 'A'], weights=[0.45, 0.35, 0.15, 0.05])[0]  # More uncertainty
    else:
        return random.choices(['A', 'G', 'V', 'Z'], weights=[0.5, 0.3, 0.15, 0.05])[0]  # More confirmed diagnoses

def generate_diaglokal(hiv_positive: bool = True) -> str:  # [48] Riedel et al. (2005) – Bilateral symptoms more common in HIV+ due to symmetrical or systemic manifestations
    """
    Return enriched diagnosis laterality (DIAGLOKAL) based on HIV status.
    HIV+ patients more likely to show bilateral findings (e.g., lymphadenopathy).
    """
    if hiv_positive:
        return random.choices(['-', 'B', 'L', 'R'], weights=[0.95, 0.025, 0.0125, 0.0125])[0]  # 5% total with laterality
    else:
        return random.choices(['-', 'L', 'R', 'B'], weights=[0.95, 0.02, 0.02, 0.01])[0]

def get_weighted_icd_pool(conn, sti_ratio=0.6, total=1000): # [51] Robert Koch-Institut (2023) #referenced from the TABLE icd10_catalogue
    cur = conn.cursor()
    cur.execute('SELECT "SCHLÜSSELNUMMER", "TITEL_LANG" FROM "icd10_catalogue";')
    rows = cur.fetchall()

    sti_keywords = [
        "hiv", "syphilis", "gonorrhoe", "chlamydien", "genital",
        "herpes", "trichomon", "urethritis", "vaginitis"
    ]

    sti_icd = []
    non_sti_icd = []

    for code, title in rows:
        if not code:
            continue
        title_lower = (title or "").lower()
        if any(kw in title_lower for kw in sti_keywords):
            sti_icd.append(code)
        else:
            non_sti_icd.append(code)

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
    HIV+ patients have clustered diagnosis events, especially post-enrollment.
    """
    if hiv_positive:
        year = random.choices([2019, 2020, 2021, 2022, 2023], weights=[5, 10, 15, 30, 40])[0]
        month = random.choices([3, 6, 9, 12], weights=[1, 3, 3, 3])[0]  # Screening in Q2–Q4
        day = random.randint(1, 28)  # avoid invalid dates
    else:   
        year = random.randint(2019, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
    
    return int(f"{year}{month:02d}{day:02d}")

def seed_ambdiag_table(conn, row_count=1):
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

        diagsich = generate_diagsich(hiv_positive=True)  # [47] Kojic et al. (2011) – Enriched for HIV+ diagnosis certainty
        diaglokal = generate_diaglokal(hiv_positive=True)  # [48] Riedel et al. (2005) – Bilateral symptoms in HIV+
        diagdat = generate_diag_date()                      # [50] BZgA – PrEP Monitoring Report (2023)
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
    print(f" Inserted {row_count} synthetic rows into 'ambdiag'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="DM3_SEEDER",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_ambdiag_table(conn)
    conn.close()
