import random
import psycopg2
from datetime import date, timedelta

# ────────────────────── Static Helper Pools ──────────────────────
LOKAL_POOL = [None, "R", "L", "B"]
SEK_ICD_POOL = [None, "I10.90", "E66.9", "N39.0", "F17.2"]
DIAGART_POOL = ["H", "N", "A"]

# ────────────────────── Date Generator ───────────────────────────
def random_date_in_year(year: int) -> int:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return int(d.strftime("%Y%m%d"))

# ────────────────────── FALLID Generator ─────────────────────────
fall_counter: dict[tuple[int, int], int] = {}

def next_fallid(vsid: int, year: int) -> str:
    key = (vsid, year)
    fall_counter[key] = fall_counter.get(key, 0) + 1
    return f"{year}-{fall_counter[key]:08d}"

# ────────────────────── ICD Code Pool from DB ────────────────────
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

# ────────────────────── ICD Zusatz Pool from DB ──────────────────
def get_icd_extra_pool(conn, limit=20):
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "VIERSTELLER_MIT_PUNKT" FROM "icd10_catalogue" WHERE "VIERSTELLER_MIT_PUNKT" IS NOT NULL;')
    codes = [row[0] for row in cur.fetchall()]
    return [None] + random.sample(codes, min(limit, len(codes)))

# ────────────────────── Main Seeding Routine ─────────────────────
def seed_khdiag_table(conn, rows: int = 500):
    cur = conn.cursor()

    ICD_MAIN_POOL = get_weighted_icd_pool(conn, sti_ratio=0.6, total=1000)
    ICD_EXTRA_POOL = get_icd_extra_pool(conn, limit=20)

    cur.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    person_rows = cur.fetchall()
    if not person_rows:
        raise ValueError("vers table empty, cannot seed khdiag")

    for _ in range(rows):
        vsid, psid, bjahr, bnr = random.choice(person_rows)
        fallidkh = next_fallid(vsid, bjahr)

        diagart = random.choice(DIAGART_POOL)
        icd_main = random.choice(ICD_MAIN_POOL)
        icd_zus = random.choice(ICD_EXTRA_POOL)
        icd_lok = random.choice(LOKAL_POOL)

        sek_icd = random.choice(SEK_ICD_POOL)
        sek_zus = None if sek_icd is None else random.choice(ICD_EXTRA_POOL)
        sek_lok = None if sek_icd is None else random.choice(LOKAL_POOL)

        datenmodell = 4

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

# ────────────────────── Script Entrypoint ────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432",
    )
    try:
        seed_khdiag_table(conn, rows=500)
    finally:
        conn.close()
