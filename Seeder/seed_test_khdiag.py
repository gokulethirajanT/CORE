import random
import psycopg2
from datetime import date, timedelta

# ────────────────────── ICD Extraction Function ──────────────────────
def extract_icd_parts(code: str):
    """Splits an ICD code into cleaned code and Zusatz (e.g. '.', '-', '!')."""
    if not code:
        return None, None
    for symbol in ['.', '-', '!']:
        if symbol in code:
            return code.replace(symbol, ''), symbol
    return code, None

# ────────────────────── Extraction function for SEKICD_CODE ──────────
def get_secondary_icd_pool(conn, total=500):  # [84] Mocroft, A., Reiss, P., Gasiorowski, J., et al. (2014)
    """
    Return a pool of ICD codes for SEKICD_CODE enriched with common HIV co-infections.
    """
    cur = conn.cursor()
    cur.execute('SELECT "SCHLÜSSELNUMMER", "TITEL_LANG" FROM "icd10_catalogue";')
    rows = cur.fetchall()

    hiv_co_keywords = [
        "candidiasis", "tuberkulose", "hepatitis", "pneumocystis", "malnutrition",
        "dementia", "syphilis", "chlamydien", "mycobacterium", "cmv", "toxoplasm"
    ]

    hiv_related = []
    general = []

    for code, title in rows:
        if not code:
            continue
        title_lower = (title or "").lower()
        if any(kw in title_lower for kw in hiv_co_keywords):
            hiv_related.append(code)
        else:
            general.append(code)

    if not hiv_related or not general:
        raise ValueError("Insufficient ICD codes for secondary diagnosis enrichment.")

    hiv_ratio = 0.7  # 70% of secondary diagnoses are HIV-related
    return (
        random.choices(hiv_related, k=int(total * hiv_ratio)) +
        random.choices(general, k=total - int(total * hiv_ratio))
    )


# ────────────────────── Static Helper Pools ──────────────────────────
def generate_icd_lokal(hiv_positive: bool = True) -> str: # [83] Riedel, D. J., Gebo, K. A., Moore, R. D., & Lucas, G. M. (2005)
    """
    Enriched laterality for ICDLOKAL in HIV+ patients.
    Bilateral findings are more likely in HIV-related complications.
    """
    if hiv_positive:
        return random.choices([None, "B", "R", "L"], weights=[0.9, 0.05, 0.025, 0.025])[0]
    else:
        return random.choices([None, "R", "L", "B"], weights=[0.95, 0.02, 0.02, 0.01])[0]


def generate_diagart(): # [82] Flemming, T., Witte, J., Marcus, U. (2020).
    # Increased chance of 'A' (admission diagnosis) in context of HIV/STI hospitalizations
    return random.choices(
        population=["A", "H", "N"],
        weights=[0.5, 0.3, 0.2],  # Admission > Main > Secondary
        k=1
    )[0]

# ────────────────────── Date Generator ───────────────────────────────
def random_date_in_year(year: int) -> int:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return int(d.strftime("%Y%m%d"))

# ────────────────────── ICD Code Pool from DB ───────────────────────
def get_weighted_icd_pool(conn, sti_ratio=0.6, total=1000):
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

# ────────────────────── Zusatz Pool (Optional) ──────────────────────
def get_icd_extra_pool(conn, limit=20):
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "VIERSTELLER_MIT_PUNKT" FROM "icd10_catalogue" WHERE "VIERSTELLER_MIT_PUNKT" IS NOT NULL;')
    codes = [row[0] for row in cur.fetchall()]
    return [None] + random.sample(codes, min(limit, len(codes)))

# ────────────────────── Main Seeding Routine ────────────────────────
def seed_khdiag_table(conn, rows: int = 500):
    cur = conn.cursor()

    ICD_MAIN_POOL = get_weighted_icd_pool(conn, sti_ratio=0.6, total=1000)
    SEK_ICD_POOL = get_secondary_icd_pool(conn, total=500)

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khfall";')
    person_rows = cur.fetchall()
    if not person_rows:
        raise ValueError("khfall table is empty; cannot seed khdiag.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(person_rows)

        diagart = generate_diagart() #[82] Flemming, T., Witte, J., Marcus, U. (2020).

        raw_icd_main = random.choice(ICD_MAIN_POOL)
        icd_main, icd_zus = extract_icd_parts(raw_icd_main)
        icd_lok = generate_icd_lokal(hiv_positive=True) # [83] Riedel, D. J., Gebo, K. A., Moore, R. D., & Lucas, G. M. (2005)

        raw_sek_icd = random.choice(SEK_ICD_POOL) # [84] Mocroft, A., Reiss, P., Gasiorowski, J., et al. (2014)
        sek_icd, sek_zus = extract_icd_parts(raw_sek_icd) if raw_sek_icd else (None, None)
        sek_lok = None if sek_icd is None else generate_icd_lokal(hiv_positive=True)

        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cur.execute(
            """
            INSERT INTO "khdiag" (
              "VSID", "PSID", "FALLIDKH",
              "DIAGART", "ICDKH_CODE", "ICDKH_ZUSATZ", "ICDLOKAL",
              "SEKICD_CODE", "SEKICD_ZUSATZ", "SEKICDLOKAL",
              "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s
            );""",
            (
                vsid, psid, fallidkh,
                diagart, icd_main, icd_zus, icd_lok,
                sek_icd, sek_zus, sek_lok,
                bjahr, bnr, datenmodell
            )
        )

    conn.commit()
    print(f"Inserted {rows} rows into 'khdiag'")

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
        seed_khdiag_table(conn, rows=1)
    finally:
        conn.close()
