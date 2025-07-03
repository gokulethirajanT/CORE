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
def get_secondary_icd_pool(conn, total=500):
    cur = conn.cursor()
    cur.execute('SELECT "SCHLÜSSELNUMMER" FROM "icd10_catalogue" WHERE "SCHLÜSSELNUMMER" IS NOT NULL;')
    all_codes = [row[0] for row in cur.fetchall()]
    return [None] + random.sample(all_codes, min(total, len(all_codes)))

# ────────────────────── Static Helper Pools ──────────────────────────
LOKAL_POOL = [None, "R", "L", "B"]
DIAGART_POOL = ["H", "N", "A"]

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

        diagart = random.choice(DIAGART_POOL)

        raw_icd_main = random.choice(ICD_MAIN_POOL)
        icd_main, icd_zus = extract_icd_parts(raw_icd_main)
        icd_lok = random.choice(LOKAL_POOL)

        raw_sek_icd = random.choice(SEK_ICD_POOL)
        sek_icd, sek_zus = extract_icd_parts(raw_sek_icd) if raw_sek_icd else (None, None)
        sek_lok = None if sek_icd is None else random.choice(LOKAL_POOL)

        datenmodell = 3

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
