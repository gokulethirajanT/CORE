from datetime import date, timedelta, datetime
import random
import string
import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

# ───── Load environment variables ─────
load_dotenv()

def random_date_in_year(year: int) -> str:
    """Returns a random date in YYYYMMDD format within the given year."""
    d = date(year, 1, 1) + timedelta(days=random.randint(0, 364))
    return d.strftime("%Y%m%d")

def select_and_store_fixed_prep_pzns() -> list:
    """Pull 103 PrEP PZNs from DB, select 10, add 5 other meds, and store locally."""
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT pzn FROM pzn_prep_j05ar03;")
    full_pzns = [row[0].zfill(8) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Sample 10 PrEP PZNs
    fixed_prep_10 = random.sample(full_pzns, 10)

    # Fixed non-PrEP PZNs (simulated)
    other_pzn_pool = [
        "04567891",  # Simvastatin
        "05678912",  # Amoxicillin
        "06789123",  # Ibuprofen 600mg
        "07891234",  # Metformin
        "08912345",  # Ramipril
    ]

    # Save to CSV (force all to str)
    combined_df = pd.DataFrame({
        "PZN": [str(p) for p in fixed_prep_10 + other_pzn_pool],
        "TYPE": ["PREP"] * 10 + ["OTHER"] * 5
    })

    os.makedirs("reference", exist_ok=True)
    combined_df.to_csv("reference/fixed_prep_pzns.csv", index=False)
    print(" Saved 10 PREP + 5 OTHER PZNs to reference/fixed_prep_pzns.csv")
    return fixed_prep_10


def generate_pznrez() -> str:
    """Return a random PZN code from both PrEP and other medications."""
    df = pd.read_csv("reference/fixed_prep_pzns.csv")
    prep = df[df["TYPE"] == "PREP"]["PZN"].tolist()
    other = df[df["TYPE"] == "OTHER"]["PZN"].tolist()
    return random.choice(prep if random.random() < 0.5 else other)

def random_abgabedat() -> str: # [11] IFA GmbH (2025) – PZN Code Structure
    """Generate a prescription date within the past 12 months in YYYYMMDD format."""
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    delta_days = (end_date - start_date).days
    d = start_date + timedelta(days=random.randint(0, delta_days))
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
    #Remove the old pzn values
    pzn_file_path = "reference/fixed_prep_pzns.csv"
    if os.path.exists(pzn_file_path):
        os.remove(pzn_file_path)
        print(f"🧹 Removed old {pzn_file_path}")

    if not os.path.exists("reference/fixed_prep_pzns.csv"):
        select_and_store_fixed_prep_pzns()

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_rez_table(conn)
    conn.close()
