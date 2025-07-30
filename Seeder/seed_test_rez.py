from datetime import date, timedelta, datetime
import random
import string
import psycopg2
from dotenv import load_dotenv
import os

# ───── Load environment variables ─────
load_dotenv()


def random_date_in_year(year: int) -> str:
    """Returns a random date in YYYYMMDD format within the given year."""
    d = date(year, 1, 1) + timedelta(days=random.randint(0, 364))
    return d.strftime("%Y%m%d")

def generate_pznrez() -> str: # [11] IFA GmbH (2025) – PZN Code Structure 
    """Return a random PZN code from both PrEP and non-PrEP medications with equal probability."""

    # PrEP-related PZNs (real and simulated generics)
    prep_pzn_pool = [
        "01380424",  # Truvada https://www.apotheken-umschau.de/medikamente/beipackzettel/truvada-200-mg245-mg-filmtabletten-1380424.html
        "12724393",  # FTC/TDF - ratiopharm https://www.shop-apotheke.com/arzneimittel/12724393/emtricitabin-tenofovirdisoproxil-ratiopharm-200-mg-245-mg.htm
        "12546796",  # FTC/TDF - Mylan                              ----- Generic Versions https://investor.mylan.com/news-releases/news-release-details/mylan-receives-tentative-approval-combination-hiv-treatment
        "12457896",  # FTC/TDF - AbZ Pharma (simulated)             ----- Generic Versions
        "12634597",  # FTC/TDF - TAD Pharma (simulated)     ---------
    ]

    # Non-PrEP medications (simulated co-treatments)
    other_pzn_pool = [
        "04567891",  # Simvastatin
        "05678912",  # Amoxicillin
        "06789123",  # Ibuprofen 600mg
        "07891234",  # Metformin
        "08912345",  # Ramipril
    ]

    # Combine both pools and randomly select one
    all_pzn_pool = prep_pzn_pool + other_pzn_pool
    return random.choice(all_pzn_pool)

def random_abgabedat(start_year=2019, end_year=2025, end_quarter=1) -> str: # [11] IFA GmbH (2025) – PZN Code Structure
    """Returns a random date between 01.01.2019 and end of Q1 2025 in YYYYMMDD format."""
    start_date = date(2019, 1, 1)
    if end_quarter == 1:
        end_date = date(2025, 3, 31)
    elif end_quarter == 2:
        end_date = date(2025, 6, 30)
    elif end_quarter == 3:
        end_date = date(2025, 9, 30)
    else:
        end_date = date(2025, 12, 31)
    
    delta_days = (end_date - start_date).days
    rand_day = random.randint(0, delta_days)
    d = start_date + timedelta(days=rand_day)
    return d.strftime("%Y%m%d")

def generate_bsnrvovb() -> int:
    """Generate a BSNR contractual area code with no bias (completely random)."""
    return random.randint(10, 99)

def generate_lenrvofg() -> int:
    """Return a Fachgruppenschlüssel code with no bias (completely random)."""
    return random.randint(1, 99)

def generate_apoklass() -> str:
    """Return a completely random pharmacy classification code as a 2-digit string."""
    return f"{random.randint(10, 99)}"

def generate_apositz() -> str:
    """Return a completely random pharmacy location type."""
    return random.choice(["1", "2"])  # 1 = urban, 2 = mail-order
 
def generate_amount(min_val=5.00, max_val=200.00) -> float:
    """Generate a random float rounded to 2 decimal places."""
    return round(random.uniform(min_val, max_val), 2)

def generate_id(length: int = 9) -> str:
    """Generate a random numeric string of specified length."""
    return ''.join(random.choices(string.digits, k=length))
    
def generate_bsnrvoregknz() -> int:
    """Return a REGKNZ code with no regional bias (completely random)."""
    return random.randint(10, 99)

def generate_aporegknz() -> str:
    """Return a REGKNZ code for pharmacy region with no bias (completely random)."""
    return f"{random.randint(1, 16):02d}"

def generate_menge() -> int: # Skew toward 85-90
    """Return dispensed quantity (completely random)."""
    return random.randint(1, 200)

def generate_noctu() -> str:  
    """Return NOCTU code (completely random emergency dispensing indicator)."""
    return random.choice(["", "1", "2"])

def generate_autidem() -> str:  
    """Return 'Aut-idem' substitution flag (completely random)."""
    return random.choice(["0", "1"])

def generate_wirkstoffvo() -> str:  
    """Return 'Wirkstoffverordnung' flag (completely random)."""
    return random.choice(["", "0", "1"])

def generate_ambetrag() -> float:  
    """Return reimbursed amount (completely random float between €10 and €200)."""
    return round(random.uniform(10.0, 200.0), 2)

def generate_abschlaege() -> float:  
    """Return discount value (completely random float between €1 and €10)."""
    return round(random.uniform(1.0, 10.0), 2)

def generate_zuzahlkz() -> str:  
    """Return co-payment category code (completely random)."""
    return random.choice(["0", "1", "2"])

def generate_zuzahlges(zuzahlkz: str) -> float:  # [68] ABDA – Bundesvereinigung Deutscher Apothekerverbände (2023)
    """Generate total co-payment (completely random, not based on exemption logic)."""
    return round(random.uniform(0.0, 10.0), 2)

def generate_eigenbet() -> float:
    """Return additional patient cost (Eigenbeteiligung) with no bias."""
    return round(random.uniform(0.0, 20.0), 2)

def seed_rez_table(conn, rows: int = 1000):
    cur = conn.cursor()
    cur.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("vers table is empty; cannot seed rez.")

    reznr_set = set()

    for _ in range(rows):
        vsid, psid, bjahr, bnr = random.choice(ref_rows)
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        while True:
            reznr = random.randint(100_000_000, 999_999_999) # [54] Des Jarlais et al. (2019)
            if reznr not in reznr_set:
                reznr_set.add(reznr)
                break

        pznrez = generate_pznrez() # [11] IFA GmbH (2025) – PZN Code Structure 
        abgabedat_str = random_abgabedat()  # Always between 2019 and 2025 Q1 # [1] Valbert et al. (2024) 
        vodat_str = random_abgabedat()      # Use same logic for VoDat if needed # [1] Valbert et al. (2024) 
        vodat = datetime.strptime(vodat_str, "%Y%m%d").date()
        abgabedat = datetime.strptime(abgabedat_str, "%Y%m%d").date()

        if abgabedat < vodat:
            vodat, abgabedat = abgabedat, vodat  # Ensure VoDat ≤ AbgabeDat

        vodat_int = int(vodat.strftime("%Y%m%d"))
        abgabedat_int = int(abgabedat.strftime("%Y%m%d"))


        bsnrvopseudo = generate_id(12)
        bsnrvovb = generate_bsnrvovb()
        bsnrvoregknz = generate_bsnrvoregknz() 
        lenrvopseudo = generate_id(12)  
        lenrvofg = generate_lenrvofg() 
        vertragskz = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(10, 25)))
        apopseudo = generate_id(12)
        apoklass = generate_apoklass()
        aporegknz = generate_aporegknz()
        apositz = generate_apositz()
        menge = generate_menge()
        noctu = generate_noctu()
        autidem = generate_autidem()
        wirkstoffvo = generate_wirkstoffvo()
        ambetrag = generate_ambetrag()
        abschlaege = generate_abschlaege()
        zuzahlkz = generate_zuzahlkz()
        zuzahlges = generate_zuzahlges(zuzahlkz)
        eigenbet = generate_eigenbet()

 
        cur.execute("""
            INSERT INTO rez (
                "VSID", "PSID", "REZNR", "PZNREZ", "VODAT",
                "BSNRVOPSEUDO", "BSNRVOVB", "BSNRVOREGKNZ",
                "LENRVOPSEUDO", "LENRVOFG",
                "ABGABEDAT", "VERTRAGSKZ",
                "APOPSEUDO", "APOKLASS", "APOREGKNZ", "APOSITZ", 
                "MENGE", "NOCTU", "AUTIDEM", "WIRKSTOFFVO",
                "AMBETRAG", "ABSCHLAEGE", "ZUZAHLKZ", "ZUZAHLGES", "EIGENBET",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            );
        """, (
            vsid, psid, reznr, pznrez, vodat_int,
            bsnrvopseudo, bsnrvovb, bsnrvoregknz,
            lenrvopseudo, lenrvofg,
            abgabedat_int, vertragskz,
            apopseudo, apoklass, aporegknz, apositz,
            menge, noctu, autidem, wirkstoffvo,
            ambetrag, abschlaege, zuzahlkz, zuzahlges, eigenbet,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'rez'.")

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_rez_table(conn)
    conn.close()
