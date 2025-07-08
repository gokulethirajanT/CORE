#!/usr/bin/env python3
"""
Seed the DM-3 table AMBLEIST with realistic synthetic data.
"""

import random
import string
from datetime import date, timedelta
import psycopg2

# ─────────────────── helper functions ────────────────────────────────────────
def random_service_date(start_year: int = 2019,
                        end_year:   int | None = None) -> date:
    """Return a random date between 1 Jan <start_year> and 31 Dec <end_year>."""
    if end_year is None:
        end_year = date.today().year
    start = date(start_year, 1, 1)
    end   = date(end_year,   12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def yyyymmdd_int(d: date) -> int:
    """YYYYMMDD → int (e.g. 20250307)."""
    return int(d.strftime("%Y%m%d"))


def generate_ambleistzeit(as_int: bool = True):
    """Return SSMM as int (935 → 09 : 35) or string ('0935')."""
    val = f"{random.randint(0,23):02d}{random.randint(0,59):02d}"
    return int(val) if as_int else val


def generate_tsvg_bsnr() -> int:
    """12-digit pseudonymised BSNR."""
    return random.randint(100_000_000_000, 999_999_999_999)


KV_CODES = [f"{i:02d}" for i in range(1, 18)]          # 01 … 17

def generate_tsvg_kv_code(as_int: bool = True):
    code = random.choice(KV_CODES)
    return int(code) if as_int else code


def make_tsvgdat(tsvgart: int, service_dt: date) -> int | None:
    """
    • codes 1/2 → always contact date (2019–today)
    • code 4    → only if service_dt ∈ Q3 2020
    • else      → None
    """
    if tsvgart in (1, 2):
        return yyyymmdd_int(random_service_date(2019))
    if tsvgart == 4 and date(2020,7,1) <= service_dt <= date(2020,9,30):
        first_visit = date(2020,7,1) + timedelta(days=random.randint(0, 91))
        return yyyymmdd_int(first_visit)
    return None


# Zweitmeinungsverfahren (code → valid-from)
ZWEITMEIN_OPTIONS = [
    ("01", date(2019,1,1)),   # Tonsillectomy
    ("02", date(2019,1,1)),   # Hysterectomy
    ("03", date(2019,1,1)),   # Shoulder arthroscopy
    ("04", date(2019,1,1)),   # Diabetic-foot surgery
    ("05", date(2021,1,1)),   # Knee endoprosthesis
    ("06", date(2021,10,1)),  # Spine surgery
    ("07", date(2022,4,1)),   # Heart surgery
]

def generate_zweitmein_code(service_dt: date, prob: float = 0.03):
    """Return a 2-digit Zweitmein code with ~prob probability or None."""
    if random.random() >= prob:
        return None
    valid = [code for code, start in ZWEITMEIN_OPTIONS if service_dt >= start]
    return random.choice(valid) if valid else None


def generate_gonr_bewert() -> float:
    """EBM-like valuation: 70 % 25-250 P, 25 % 250-1000 P, 5 % 1000-6000 P."""
    r = random.random()
    if r < 0.70:
        val = random.uniform(25, 250)
    elif r < 0.95:
        val = random.uniform(250, 1000)
    else:
        val = random.uniform(1000, 6000)
    return round(val, 1)


TSVG_GROUP_CODES = [
    300,401,501,601,701,801,901,1001,
    1301,1311,1312,1313,1314,1315,1316,1317,1318,
    1351,1401,1600,1801,2001,2101,2200,2300,2601,2701,
    9305,9306,9307,9991,
]

# ─────────────────── main seeding routine ────────────────────────────────────
def seed_ambleist_table(conn, row_count: int = 100):
    cur = conn.cursor()

    # reference patients
    cur.execute('SELECT "VSID", "PSID", "FALLIDAMB", "BJAHR", "BNR" FROM "ambfall";')
    ambfall_rows = cur.fetchall()
    if not ambfall_rows:
        raise ValueError("Table 'ambfall' is empty – nothing to link to.")

    fallid_tracker: dict[tuple[int,int],int] = {}

    for _ in range(row_count):
        vsid, psid, fallidamb, bjahr, bnr = random.choice(ambfall_rows)

        # identifiers
        nbsnr_pseudo = generate_tsvg_bsnr()
        nbsnr_kv     = generate_tsvg_kv_code(True)
        lanr_pseudo  = generate_tsvg_bsnr()
        lanr_fg      = random.randint(10, 99)

        # EBM item
        gonr = f"{random.randint(10000,99999)}{random.choice(['','A','B','E'])}"

        # dates & numeric fields
        service_dt    = random_service_date()
        gonr_dat      = yyyymmdd_int(service_dt)
        multiplikator = round(random.uniform(1.0, 3.5), 2)
        ambleistzeit  = generate_ambleistzeit(True)

        # TSVG pathway
        tsvgart  = random.randint(1, 5)
        tsvgdat  = make_tsvgdat(tsvgart, service_dt)
        tsvgarzt = random.choice(TSVG_GROUP_CODES)
        if tsvgart in (1,2,4):
            tsvgbsnr_pseudo = generate_tsvg_bsnr()
            tsvgbsnr_kv     = generate_tsvg_kv_code(True)
        else:
            tsvgbsnr_pseudo = tsvgbsnr_kv = None

        # Zweitmeinung & valuation
        zweitmein_code = generate_zweitmein_code(service_dt)
        gonr_bewert    = generate_gonr_bewert()
        datenmodell    = 3

        cur.execute(
            """
            INSERT INTO "ambleist" (
              "VSID","PSID","FALLIDAMB",
              "NBSNRPSEUDO","NBSNRKV",
              "LANRPSEUDO","LANRFG",
              "GONR","GONRDAT",
              "MULTIPLIKATOR","AMBLEISTZEIT",
              "TSVGART","TSVGDAT","TSVGARZT",
              "TSVGBSNRPSEUDO","TSVGBSNRKV",
              "ZWEITMEIN","GONRBEWERT",
              "BJAHR","BNR","DATENMODELL"
            ) VALUES (
              %s,%s,%s,%s,%s,%s,%s,%s,%s,
              %s,%s,%s,%s,%s,%s,%s,%s,%s,
              %s,%s,%s
            );""",
            (
              vsid, psid, fallidamb,
              nbsnr_pseudo, nbsnr_kv,
              lanr_pseudo, lanr_fg,
              gonr, gonr_dat,
              multiplikator, ambleistzeit,
              tsvgart, tsvgdat, tsvgarzt,
              tsvgbsnr_pseudo, tsvgbsnr_kv,
              zweitmein_code, gonr_bewert,
              bjahr, bnr, datenmodell
            )
        )

    conn.commit()
    print(f" Inserted {row_count} synthetic rows into 'ambleist'")

# ─────────────────── run as script ───────────────────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname   = "CORE_MASTER_THESIS",
        user     = "postgres",
        password = "London@123",
        host     = "localhost",
        port     = "5432"
    )
    try:
        seed_ambleist_table(conn, row_count=1)
    finally:
        conn.close()
