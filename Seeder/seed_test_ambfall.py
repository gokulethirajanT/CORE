import random
import psycopg2
from datetime import datetime, timedelta
import string
import uuid
from dotenv import load_dotenv
import os

load_dotenv()

def generate_random_date_int(start_year=2019, end_year=2023):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return int((start + timedelta(days=random.randint(0, (end - start).days))).strftime('%Y%m%d'))

def generate_punktzahl():
    # Tiered random generation for HIV outpatient billing
    category = random.choices(
        ['low', 'medium', 'high'],
        weights=[1, 3, 2]  # Most PrEP visits fall into medium–high zone
    )[0]

    if category == 'low':
        value = random.uniform(50, 200)
    elif category == 'medium':
        value = random.gauss(440, 80)
    else:  # high
        value = random.gauss(700, 100)

    value = max(4.4, min(value, 900))  # Clamp to FDZ bounds
    return round(value, 1)

def generate_fallkoamb(): 
    # Simulate total cost of outpatient case with HIV-specific enrichments
    category = random.choices(
        ['low', 'medium', 'high', 'very_high'], # [39] Damm et al. (2021)
        weights=[1, 5, 3, 1]
    )[0]

    if category == 'low':
        value = random.uniform(50, 500)  # Simple test visit
    elif category == 'medium':
        value = random.gauss(3000, 500)  # Typical PrEP or HIV outpatient care
    elif category == 'high':
        value = random.gauss(7000, 1000)  # Bundled lab + multiple consults
    else:  # very high
        value = random.gauss(15000, 3000)  # Rare but possible high complexity

    value = max(50.0, min(value, 25000.0))
    return round(value, 2)

def generate_dialyse_cost(): # [40] Bundesministerium für Gesundheit (2022)
    # Simulate dialysis Sachkosten only in rare HIV comorbid cases
    include_dialysis = random.choices([True, False], weights=[2, 98])[0]

    if include_dialysis:
        value = random.gauss(mu=30000, sigma=10000)  # Typical range €20k–40k
        value = max(5000, min(value, 60000))          # Clamp to real-world costs
        return round(value, 2)
    else:
        return 0.0  # No dialysis billed in majority of cases

def seed_ambfall_table(conn, row_count=100):
    cursor = conn.cursor()

    cursor.execute("""SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers" """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'ambfall'.")

    fallid_tracker = {}

    for _ in range(row_count):
        # Inherit ID values from 'vers' parent table
        vsid, psid, bjahr, bnr = random.choice(vers_rows)

        # Generate unique 11-char outpatient case ID
        fallid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))

        # Create quarter (ABRQ) based on year and quarter
        year = random.randint(2019, 2023)         # Valid years from the dataset
        quarter = random.randint(1, 4)            # Valid quarters: 1 to 4
        abrq = int(f"{year}{quarter}")            # Combine as YYYYQ

        # Random pseudonym contract number
        svnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=11)) # https://www.bundesgesundheitsministerium.de/service/begriffe-von-a-z/s/selektivvertrag.html

        # Contract type: more weight on PrEP-relevant types
        svtyp = random.choices([1, 2], weights=[2, 5])[0] # [32] German Federal Ministry of Health (2020)

        # Pseudonymized practice number
        bsnrpseudo = random.randint(1, 9999)

        # KV region code for billing — skewed toward HIV-capable practices
        bsnrkv = random.choices([1, 2, 3, 6, 8, 9], weights=[5, 4, 3, 3, 2, 3])[0] # [33] Kassenärztliche Vereinigung Berlin (2023) 

        # Referral practice pseudonym
        bsnruebpseudo = random.randint(100, 999)

        # Referral region — enriched to urban HIV networks
        bsnruebkv = random.choices([1, 2, 3, 5, 6, 8, 9, 11], weights=[5, 4, 3, 1, 2, 2, 3, 1])[0] #[34] European Centre for Disease Prevention and Control (2023)

        # Referring physician pseudonym
        lanruebpseudo = random.randint(100000000000, 999999999999)  # 12-digit pseudonym

        # Physician specialty group — skewed toward HIV-relevant fields
        lanruebfg = random.choices([1, 5, 7, 13, 17, 23, 40], weights=[6, 4, 3, 3, 2, 2, 1])[0] # [35] Oppong et al. (2019)

        # Ambulatory care type — weighted toward STI/HIV types
        inansprartamb = random.choices(
            ['O', 'V', 'K', 'M', 'Z', '7', '8', '0', 'N'], # [36] Reuter et al. (2023)
            weights=[4, 4, 3, 3, 2, 1, 1, 1, 1]
        )[0]

        # Very few HIV outpatient visits are trauma-related
        unfall = random.choices([0, 2], weights=[98, 2])[0] # [37] Burch et al. (2020)

        # Treatment type, weighted to favor structured STI/PrEP codes
        behandartamb = random.choices([1, 2], weights=[3, 7])[0] # 1 = unspecified treatment type A, 2 = treatment type B

        # Randomized obstetric date for edge-case scenarios
        entbindungsdat = generate_random_date_int() # [3] Marcus et al. (2023)

        # PrEP-specific outpatient billing code enrichment
        punktzahl = generate_punktzahl() # [38] PrEP Monitoring Team, BZgA (2023)

        # Total case-level euro cost with Gaussian enrichment
        fallkoamb = generate_fallkoamb() # [39] Damm et al. (2021)

        # Inject dialysis cost in rare comorbidity edge cases
        dialysesachko = generate_dialyse_cost() # [40] Bundesministerium für Gesundheit (2022)

        # Randomize service start date
        beginndatamb = generate_random_date_int()

        # Randomize service end date and fix temporal order if needed
        endedatamb = generate_random_date_int()
        if endedatamb < beginndatamb:
            beginndatamb, endedatamb = endedatamb, beginndatamb

        # Mark as part of FDZ Data Model 3
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cursor.execute("""
            INSERT INTO "ambfall" (
                "VSID", "PSID", "ABRQ", "FALLIDAMB", "SVNR", "SVTYP",
                "BSNRPSEUDO", "BSNRKV", "BSNRUEBPSEUDO", "BSNRUEBKV",
                "LANRUEBPSEUDO", "LANRUEBFG", "INANSPRARTAMB", "UNFALL",
                "BEHANDARTAMB", "ENTBINDUNGSDAT", "PUNKTZAHL", "FALLKOAMB",
                "DIALYSESACHKO", "BEGINNDATAMB", "ENDEDATAMB",
                "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, abrq, fallid, svnr, svtyp,
            bsnrpseudo, bsnrkv, bsnruebpseudo, bsnruebkv,
            lanruebpseudo, lanruebfg, inansprartamb, unfall,
            behandartamb, entbindungsdat, punktzahl, fallkoamb,
            dialysesachko, beginndatamb, endedatamb,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {row_count}  rows into 'ambfall'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_ambfall_table(conn)
    conn.close()
