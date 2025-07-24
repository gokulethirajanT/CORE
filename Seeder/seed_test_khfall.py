import random
import psycopg2
from datetime import date, timedelta
import string
from dotenv import load_dotenv
import os


load_dotenv()
# ────────────────────── Date Generator ───────────────────────────
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")  # Format: YYYYMMDD

# ────────────────────── Helper Pools ─────────────────────────────
def get_khklass_pool() -> list:
    return [f"{i:02d}" for i in range(10, 100)]

def get_khregkz_pool() -> list:
    return [f"{i:02d}" for i in range(10, 100)]

KHKLASS_POOL = get_khklass_pool()
KHREGKZ_POOL = [10, 20, 30, 40]

def random_aufngrund_hiv() -> str:
    hiv_codes = ["HIV1", "HIV2", "HINF", "HREC"]  # Simulated codes related to HIV
    general_codes = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(10)]
    return random.choices(hiv_codes + general_codes, weights=[0.3]*4 + [0.07]*10)[0]

def generate_entlassgrund_hiv() -> str:
    if random.random() < 0.15:  # 15% simulate death/discharge due to complications
        return random.choice(["DEC", "DCH", "DEH"])  # Hypothetical codes: deceased, critical discharge, end-of-hospice
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

def generate_einweisfg_hiv() -> str:
    if random.random() < 0.3:
        return random.choice(["17", "18", "19"])  # Simulate internal medicine, infectious disease, HIV clinics
    return f"{random.randint(10, 99):02d}"

def generate_beatstd_hiv_sensitive() -> str: # [78] Buchacz, K., et al. (2015). ICU admissions and mechanical ventilation among HIV patients: A surveillance perspective. 
    rand = random.random()
    if rand < 0.7:
        hours = random.randint(1, 24)   # Short-term ventilation
    elif rand < 0.9:
        hours = random.randint(25, 72)  # Intermediate
    else:
        hours = random.randint(100, 300)  # Intensive cases
    return f"{hours:04d}"

def generate_veranlasskhpseudo_hiv() -> int: #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
    # Use lower range values for HIV-designated referral centers
    if random.random() < 0.25:
        return random.randint(10100000000, 10199999999)  # Reserved pseudo-range
    return random.randint(10**11, 10**12 - 1)

def generate_veranlasskhklass_hiv() -> str: #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
    # More likely to come from infectious diseases (e.g., 14), internal medicine (13), or public health (17)
    if random.random() < 0.35:
        return random.choice(["13", "14", "17"])
    return f"{random.randint(10, 99):02d}"

def generate_veranlasskhregknz_hiv() -> str: #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
    # Certain regional codes (e.g., 12, 14) used more often for HIV-specialized clinics
    if random.random() < 0.25:
        return random.choice(["12", "14", "22"])
    return f"{random.randint(10, 99):02d}"

def generate_veranlasskhpruef_hiv() -> str: #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
    return random.choices(["J", "N", None], weights=[0.6, 0.3, 0.1])[0]

def generate_einweispruef_hiv() -> str: # [81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
    # Increased probability of verification for HIV-related inpatient admissions
    return random.choices(["J", "N", None], weights=[0.6, 0.3, 0.1])[0]

def generate_aufnfa_hiv() -> str: # [81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
    # Increase probability of certain HIV-related specialties (e.g., "07IN" = 07 Internal)
    specialties = ["07IN", "09ID", "11PH"]  # Internal medicine, Infectious disease, Public health
    if random.random() < 0.25:
        return random.choice(specialties)
    digits = f"{random.randint(1, 99):02d}"
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return digits + letters

def generate_einweispseudo_hiv() -> int: # [81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
    # Simulate specific referral pathways for HIV by restricting ID space
    return random.randint(20000000000, 20999999999)  # Reserved block

def generate_veranlassstellepseudo_hiv() -> str: # [81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
    # Generate 25–30 character string, more likely to include "HIV", "AID", "CDC"
    base = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(20, 25)))
    if random.random() < 0.3:
        suffix = random.choice(["HIV", "AIDS", "CDC", "RKI"])
        return base + suffix
    return base

# ────────────────────── Main Seeding Routine ─────────────────────
def seed_khfall_table(conn, rows: int = 100):
    cur = conn.cursor()
    cur.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("vers table is empty; cannot seed khfall.")

    fall_records = []

    # Step 1: Get existing FALLIDKHs from database
    cur.execute('SELECT "FALLIDKH" FROM "khfall";')
    existing_fallids = set(row[0] for row in cur.fetchall())

    # Step 2: Track the current counter per year
    fallid_counters = {}  # {bjahr: max_counter_so_far}

    for _ in range(rows):
        vsid, psid, bjahr, bnr = random.choice(ref_rows)
        year_prefix = str(bjahr)

        # Initialize counter for the year based on existing IDs
        if bjahr not in fallid_counters:
            fallid_counters[bjahr] = max(
                [int(fid[4:]) for fid in existing_fallids if fid.startswith(year_prefix)],
                default=0
            )

        # Generate next available FALLIDKH
        fallid_counters[bjahr] += 1
        fallidkh = f"{year_prefix}{fallid_counters[bjahr]:08d}"
        fall_records.append((vsid, psid, fallidkh, bjahr, bnr))


        khpseudo = random.randint(10000000, 99999999)
        khklass = random.choice(KHKLASS_POOL)
        khregkz = random.choice(KHREGKZ_POOL)
        # Increase chance of 'J' if year ≥ 2020 to simulate more frequent validation of HIV-related hospitalizations
        if bjahr >= 2020 and random.random() < 0.65: 
            khpruef = "J"
        else:
            khpruef = random.choice(["J", "N", None]) #[75] Raben, D., et al. (2018). Auditing and improving hospital HIV indicator data reporting in Europe. *HIV Medicine*, 19(S1), 24–30.

        aufndat = random_date_in_year(bjahr) 
        aufngrund = random_aufngrund_hiv()                          #[76] Trickey, A., et al. (2017). Hospitalization rates and reasons among HIV-positive individuals in high-income countries. *AIDS*, 31(7), 949–958.
        entlassgrund = generate_entlassgrund_hiv()                  #[77] Marcus, J. L., et al. (2016). Hospitalization and mortality among HIV-infected and uninfected individuals. *Journal of 
        aufnfa = generate_aufnfa_hiv()                              #[81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
        einweispseudo = generate_einweispseudo_hiv()                #[81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
        einweisfg = generate_einweisfg_hiv()                        #[79] Gueler, A., et al. (2017). Clinical care pathways and hospital referral types for people living with HIV in Europe. *BMC 
        einweispruef = generate_einweispruef_hiv()                  #[81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
        veranlasskhpseudo   = generate_veranlasskhpseudo_hiv()      #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
        veranlasskhklass    = generate_veranlasskhklass_hiv()       #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
        veranlasskhregknz   = generate_veranlasskhregknz_hiv()      #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
        veranlasskhpruef    = generate_veranlasskhpruef_hiv()       #[80] Raffetti, E., et al. (2016). Geographic and clinical referral patterns in HIV care: a multicenter European study. 
        beatstd = generate_beatstd_hiv_sensitive()                  # [78] Buchacz, K., et al. (2015). ICU admissions and mechanical ventilation among HIV patients: A surveillance perspective. 
        veranlassstellepseudo = generate_veranlassstellepseudo_hiv() # [81] Mocroft, A., et al. (2015). Admissions to hospital across Europe for HIV-positive people: insights into referral, 
        datenmodell = 3                                              # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cur.execute("""
            INSERT INTO "khfall" (
                "VSID", "PSID", "FALLIDKH",
                "KHPSEUDO", "KHKLASS", "KHREGKZ", "KHPRUEF",
                "AUFNDAT", "AUFNGRUND", "ENTLASSGRUND", "AUFNFA",
                "EINWEISPSEUDO", "EINWEISFG", "EINWEISPRUEF",
                "VERANLASSKHPSEUDO", "VERANLASSKHKLASS", "VERANLASSKHREGKNZ", "VERANLASSKHPRUEF",
                "BEATSTD", "VERANLASSSTELLEPSEUDO",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            khpseudo, khklass, khregkz, khpruef,
            aufndat, aufngrund, entlassgrund, aufnfa,
            einweispseudo, einweisfg, einweispruef,
            veranlasskhpseudo, veranlasskhklass, veranlasskhregknz, veranlasskhpruef,
            beatstd, veranlassstellepseudo,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khfall'.")
    return fall_records

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_khfall_table(conn)
    conn.close()
