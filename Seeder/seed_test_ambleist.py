#!/usr/bin/env python3
"""
Seed the DM-3 table AMBLEIST with realistic synthetic data.
"""
import random
import string
from datetime import date, timedelta
import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()
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


def generate_tsvg_bsnr(skewed=True) -> int: # [41] Wirtz et al. (2023)
    """Generate BSNR pseudonym with skewed distribution for HIV/PrEP clustering."""
    if skewed:
        # 60% from a small set of HIV centers (e.g., 20 IDs), 40% from wider pool
        if random.random() < 0.6:
            hiv_bsnr_pool = [int(f"99{random.randint(10000000, 99999999)}") for _ in range(20)]
            return random.choice(hiv_bsnr_pool)
    return random.randint(100_000_000_000, 999_999_999_999)

def generate_tsvg_kv_code(as_int: bool = True): #[1] Marcus et al. (2024) # [2] Robert Koch-Institut (2024)
    """
    Generate a KV code (01–17) with higher weight on urban regions
    where PrEP/HIV services are concentrated.
    """
    kv_codes = [f"{i:02d}" for i in range(1, 18)]
    weights = [
        1,  # 01 = Schleswig-Holstein
        6,  # 02 = Hamburg
        2,  # 03 = Lower Saxony
        1,  # 04 = Bremen
        5,  # 05 = North Rhine
        2,  # 06 = Westphalia-Lippe
        1,  # 07 = Rhineland-Palatinate
        1,  # 08 = Baden-Württemberg
        2,  # 09 = Bavaria
        1,  # 10 = Saarland
        8,  # 11 = Berlin
        2,  # 12 = Brandenburg
        2,  # 13 = Mecklenburg-Vorpommern
        2,  # 14 = Saxony
        1,  # 15 = Saxony-Anhalt
        1,  # 16 = Thuringia
        2   # 17 = Hesse
    ]
    code = random.choices(kv_codes, weights=weights, k=1)[0]
    return int(code) if as_int else code

def make_tsvgdat(tsvgart: int, service_dt: date) -> int | None: # [45] Zi – Zentralinstitut der kassenärztlichen Versorgung (2023)
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

def generate_gonr(): 
    """
    Generate EBM GOP code, enriched for HIV/PrEP services.
    Ref: KBV (2023) PrEP EBM Abrechnung
    """
    hiv_gonrs = ['01920', '01921', '32820', '32811', '32881', '01821']
    suffixes = ['', 'A', 'B', 'E']
    
    if random.random() < 0.7:
        # 70% chance of choosing from HIV-relevant codes
        return random.choice(hiv_gonrs) + random.choice(suffixes)
    else:
        # 30% random 5-digit fallback code with optional suffix
        return f"{random.randint(10000, 99999)}{random.choice(suffixes)}"

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

def generate_lanr_fg() -> int:
    """
    Return LANR Fachgruppencode, enriched for HIV/PrEP-relevant specialties.
    Based on Hoffmann et al. (2021) distribution.
    """
    codes = [14, 15, 27, 42]  # General Practice, Internal, Dermatology, Urology
    weights = [5, 4, 3, 2]    # Higher preference for GP and Internal
    other_codes = [i for i in range(10, 100) if i not in codes]

    if random.random() < 0.75:
        return random.choices(codes, weights=weights, k=1)[0]
    else:
        return random.choice(other_codes)

def generate_tsvgart():
    """
    Generate TSVGART code, enriched for PrEP-relevant service pathways.
    Ref: Deutsche Aidshilfe & Zi (2022)
    """
    tsvg_values = [1, 2, 3, 4, 5]
    weights     = [1, 1, 4, 6, 2]  # Emphasis on types 3 (referral) and 4 (open hours)
    return random.choices(tsvg_values, weights=weights, k=1)[0]

def generate_tsvgarzt(): # [46] KBV – PrEP Leistungsstatistik (2022)
    """
    Skew TSVGARZT toward HIV/PrEP-relevant specialties.
    Ref: KBV PrEP Leistungsstatistik (2022)
    """
    hiv_codes = [1301, 1401, 1600, 1801]
    other_codes = [code for code in TSVG_GROUP_CODES if code not in hiv_codes]

    if random.random() < 0.8:
        return random.choice(hiv_codes)
    else:
        return random.choice(other_codes)


def generate_zweitmein_code(service_dt: date, prob: float = 0.03): # [47] Gemeinsamer Bundesausschuss (G-BA) (2023)
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
        nbsnr_pseudo = generate_tsvg_bsnr() # [41] Wirtz et al. (2023)
        nbsnr_kv     = generate_tsvg_kv_code(True) # [1] Marcus et al. (2024) # [2] Robert Koch-Institut (2024)
        lanr_pseudo  = generate_tsvg_bsnr() # [41] Wirtz et al. (2023)
        lanr_fg = generate_lanr_fg() # [42] Hoffmann et al. (2021)

        # EBM item
        gonr = generate_gonr() # [43] Kassenärztliche Bundesvereinigung (2023)

        # dates & numeric fields
        service_dt    = random_service_date() 
        gonr_dat      = yyyymmdd_int(service_dt)
        multiplikator = round(random.uniform(1.0, 3.5), 2)
        ambleistzeit  = generate_ambleistzeit(True)

        # TSVG pathway
        tsvgart = generate_tsvgart() # [44] Deutsche Aidshilfe & Zi (2022)
        tsvgdat  = make_tsvgdat(tsvgart, service_dt) # [45] Zi – Zentralinstitut der kassenärztlichen Versorgung (2023)
        tsvgarzt = generate_tsvgarzt() # [46] KBV – PrEP Leistungsstatistik (2022)
        if tsvgart in (1, 2, 4):
            tsvgbsnr_pseudo = generate_tsvg_bsnr()
            tsvgbsnr_kv     = generate_tsvg_kv_code(True)
        else:
            tsvgbsnr_pseudo = tsvgbsnr_kv = None
        # Zweitmeinung & valuation
        zweitmein_code = generate_zweitmein_code(service_dt) # [47] Gemeinsamer Bundesausschuss (G-BA) (2023)
        gonr_bewert    = generate_gonr_bewert() # [48] Kassenärztliche Bundesvereinigung (KBV) (2023)
        datenmodell    = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

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
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_ambleist_table(conn)
    conn.close()
