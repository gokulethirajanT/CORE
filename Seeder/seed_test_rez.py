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


def generate_pznrez_hiv_enriched() -> str:
    """Return a realistic PZN for HIV-related prescriptions (ART/PrEP) with some noise.""" # [56] Cotte et al. (2022)
    # Common HIV-related drug PZNs (Truvada, Descovy, Biktarvy, etc. — fictitious/simulated PZNs)  
    hiv_pzn_pool = [
        "12345678",  # Truvada (simulated)
        "23456789",  # Descovy
        "34567890",  # Biktarvy
        "45678901",  # Tivicay
        "56789012",  # Isentress
        "67890123",  # Genvoya
        "78901234",  # Symtuza
        "89012345",  # Atripla
        "90123456",  # Dovato
        "01234567",  # Juluca
    ]
    # ~90% HIV-relevant meds, ~10% other to simulate co-prescriptions
    if random.random() < 0.9:
        return random.choice(hiv_pzn_pool)
    else:
        return ''.join(random.choices(string.digits, k=random.choice([8, 10])))


def generate_bsnrvovb_hiv_enriched() -> int:
    """Generate a BSNR contractual area with HIV-specific skew toward urban care centers."""
    hiv_hotspot_regions = [11, 20, 21, 30, 31, 40, 50]  # Berlin, Hamburg, Munich, Cologne, Düsseldorf, etc.
    if random.random() < 0.85:
        return random.choice(hiv_hotspot_regions)
    return random.randint(10, 99)  # fallback: rest of Germany

def generate_lenrvofg_hiv_enriched() -> int:  # [59] Deutsche AIDS-Hilfe (2022)
    """Return a Fachgruppenschlüssel code with HIV-relevant specialty skew."""
    hiv_specialty_codes = [
        1,  # General Practice
        3,  # Internal Medicine
        14,  # Infectious Disease Specialist (simulated)
        18,  # Dermatology/Venereology
        20,  # Gynecology/Urology
        27,  # Psychiatry/Addiction
    ]
    if random.random() < 0.85:
        return random.choice(hiv_specialty_codes)
    return random.randint(10, 99)

def generate_apoklass_hiv_enriched() -> str: # [58] BKK Dachverband (2021)
    """Return pharmacy classification code with bias toward HIV-dispensing centers."""
    hiv_apothekentypen = [
        "10",  # Öffentliche Apotheke – Public pharmacy
        "11",  # Schwerpunktapotheke – HIV-focused public pharmacy
        "20",  # Krankenhausapotheke – Hospital pharmacy
        "25",  # DMP-/Vertragsapotheke – Disease Management / rebate program pharmacy
    ]
    if random.random() < 0.9:
        return random.choice(hiv_apothekentypen)
    return f"{random.randint(10, 99)}"

def generate_apositz_hiv_enriched() -> str: # [61] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023)
    """Return pharmacy location type with HIV-aware probability."""
    return random.choices(["1", "2"], weights=[75, 25])[0]  # 75% urban, 25% mail-order

def generate_amount(min_val=5.00, max_val=200.00) -> float:
    """Generate a random float rounded to 2 decimal places."""
    return round(random.uniform(min_val, max_val), 2)

def generate_id(length: int = 9) -> str:
    """Generate a random numeric string of specified length."""
    return ''.join(random.choices(string.digits, k=length))
    
def generate_bsnrvoregknz_hiv_enriched() -> int:
    """Return a REGKNZ with HIV-aware regional bias."""
    hiv_kv_regions = [9, 11, 15, 17, 23]  # Bayern, Berlin, Hamburg, NRW
    if random.random() < 0.8:
        return random.choice(hiv_kv_regions)
    return random.randint(10, 99)

def generate_aporegknz_hiv_enriched() -> str: # [60] Barmer Arzneimittelreport (2023)
    """Return a REGKNZ with bias toward urban HIV-dense pharmacy regions."""
    hiv_pharmacy_regions = [11, 12, 13, 15, 17, 23]  # Simulated: Berlin, Hamburg, Munich, Cologne, Frankfurt, Düsseldorf
    if random.random() < 0.85:
        return f"{random.choice(hiv_pharmacy_regions):02d}"
    return f"{random.randint(1, 16):02d}"

def generate_menge_hiv_enriched() -> int: # [62] Robert Koch-Institut & Deutsche AIDS-Hilfe (2024)
    """Return dispensed quantity with HIV-aware clustering."""
    roll = random.random()
    if roll < 0.70:
        return random.choice([30, 60, 90])  # 70% of cases: standard monthly/multi-month prescriptions
    elif roll < 0.90:
        return random.randint(10, 29)       # 20% smaller packs
    else:
        return random.randint(91, 180)      # 10% large bulk prescriptions

def generate_noctu_hiv_enriched() -> str: # [63] Deutsche AIDS-Hilfe (2023)
    """Return NOCTU code with rare but realistic emergency dispensing in HIV/PrEP context."""
    return random.choices(["", "1", "2"], weights=[90, 6, 4])[0]

def generate_autidem_hiv_enriched() -> str: # Deutsche AIDS-Hilfe. (2022). *Aut idem bei HIV-Medikation: Warum die genaue Substanz zählt*
    """Return 'Aut-idem' substitution flag with HIV-specific probability."""
    return random.choices(["0", "1"], weights=[25, 75])[0]  # 75% → substitution not allowed

def generate_wirkstoffvo_hiv_enriched() -> str: # [65] Wissenschaftliches Institut der AOK (WIdO). (2023)
    """Return 'Wirkstoffverordnung' flag with HIV-aware behavior."""
    return random.choices(["", "0", "1"], weights=[10, 75, 15])[0]

def generate_ambetrag_hiv_enriched() -> float: # [66] GKV Spitzenverband (2023)
    """Return reimbursed amount biased toward high ART/PrEP costs."""
    base = random.gauss(mu=125, sigma=15)
    return round(max(80.0, min(base, 150.0)), 2)  # Clamp between €80–150

def generate_abschlaege_hiv_enriched() -> float: # [67] Deutsches Ärzteblatt (2022)
    """Return discount value with ART/PrEP rebate structure."""
    base = random.choices(
        population=[round(random.uniform(1.5, 4.0), 2), round(random.uniform(4.01, 10.0), 2)],
        weights=[85, 15]
    )[0]
    return round(base, 2)

def generate_zuzahlkz_hiv_enriched() -> str: # [66] GKV Spitzenverband (2023)
    """Return co-payment category code with HIV-specific exemption logic."""
    return random.choices(["0", "1", "2"], weights=[20, 30, 50])[0]  # 50% exempt, 30% reduced, 20% full

def generate_zuzahlges_hiv_enriched(zuzahlkz: str) -> float: # [68] ABDA – Bundesvereinigung Deutscher Apothekerverbände (2023)
    """Generate total co-payment based on HIV-specific exemption rules."""
    if zuzahlkz == "2":
        return 0.00  # Fully exempt
    elif zuzahlkz == "1":
        return round(random.choice([5.00, 7.50]), 2)  # Reduced
    else:
        return round(random.uniform(8.00, 10.00), 2)  # Full co-payment

def generate_eigenbet_hiv_enriched() -> float:
    """Return additional patient cost (Eigenbeteiligung) with HIV-specific logic."""
    if random.random() < 0.9:
        return 0.00
    return round(random.uniform(1.00, 15.00), 2)
def seed_rez_table(conn, rows: int = 100):
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

        pznrez = generate_pznrez_hiv_enriched() #[56] Cotte et al. (2022)
        vodat_str = random_date_in_year(bjahr)
        abgabedat_str = random_date_in_year(bjahr)
        vodat = datetime.strptime(vodat_str, "%Y%m%d").date()
        abgabedat = datetime.strptime(abgabedat_str, "%Y%m%d").date()
        if abgabedat < vodat:
            vodat, abgabedat = abgabedat, vodat
        vodat_int = int(vodat.strftime("%Y%m%d"))
        abgabedat_int = int(abgabedat.strftime("%Y%m%d"))

        bsnrvopseudo = generate_id(12)
        bsnrvovb = generate_bsnrvovb_hiv_enriched() # [1] Marcus et al. (2024)
        bsnrvoregknz = generate_bsnrvoregknz_hiv_enriched() # [57] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023)
        lenrvopseudo = generate_id(12)  
        lenrvofg = generate_lenrvofg_hiv_enriched() # [35] Deutsche AIDS-Hilfe (2022)
        vertragskz = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(10, 25)))
        apopseudo = generate_id(12)
        apoklass = generate_apoklass_hiv_enriched() # [58] BKK Dachverband (2021)
        aporegknz = generate_aporegknz_hiv_enriched() # [60] Barmer Arzneimittelreport (2023)
        apositz = generate_apositz_hiv_enriched() # [61] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023)
        menge = generate_menge_hiv_enriched() # [62] Robert Koch-Institut & Deutsche AIDS-Hilfe (2024)
        noctu = generate_noctu_hiv_enriched() # [63] Deutsche AIDS-Hilfe (2023)
        autidem = generate_autidem_hiv_enriched() # Deutsche AIDS-Hilfe. (2022). *Aut idem bei HIV-Medikation: Warum die genaue Substanz zählt*
        wirkstoffvo = generate_wirkstoffvo_hiv_enriched() # [65] Wissenschaftliches Institut der AOK (WIdO). (2023)
        ambetrag = generate_ambetrag_hiv_enriched() # [66] GKV Spitzenverband (2023)
        abschlaege = generate_abschlaege_hiv_enriched() # [67] Deutsches Ärzteblatt (2022) 
        zuzahlkz = generate_zuzahlkz_hiv_enriched() # [66] GKV Spitzenverband (2023)
        zuzahlges = generate_zuzahlges_hiv_enriched(zuzahlkz) # [68] ABDA – Bundesvereinigung Deutscher Apothekerverbände (2023) 
        eigenbet = generate_eigenbet_hiv_enriched() # [69] AOK Bundesverband (2022)
 
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
