import random
import psycopg2
from datetime import datetime
from mimesis import Generic
from mimesis.enums import Locale
from dotenv import load_dotenv
import os


load_dotenv()
# Use German locale for realistic PLZ, dates, etc.
g = Generic(locale=Locale.DE)

def seed_vers_table(conn, row_count=1):
    cursor = conn.cursor()

    # Fetch existing PSIDs from the database
    cursor.execute('SELECT "PSID" FROM "vers";')
    existing_psids = {row[0] for row in cursor.fetchall()}
    generated_psids = set()

    # ───────────── Ensure PSID uniqueness ─────────────
    # According to ECDC PrEP monitoring standards [97],
    # each individual must be counted only once — even if they receive PrEP in multiple settings or time periods.
    # Duplicated PSIDs can inflate cohort size, distort retention indicators, and bias continuation tracking.
    # This logic checks both: 
    #    1. Previously inserted PSIDs in the database (existing_psids)
    #    2. PSIDs generated during this current run (generated_psids)

    def generate_unique_psid(): # [6] European Centre for Disease Prevention and Control (2023)
        while True:
            psid = bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))
            if psid not in existing_psids and psid not in generated_psids:
                generated_psids.add(psid)
                return psid

    for _ in range(row_count):
        vsid = random.randint(1000000, 9999999)  # 7-digit unique ID
        psid = generate_unique_psid() # [6] European Centre for Disease Prevention and Control (2023)

        # GEBJAHR skew: Most PrEP users are aged ~27–47 (Mean: 37.4, SD: 9.6) → birth years ~1977–1997
        # Reference: [1] Valbert et al. (2024), Table 2. Mean age 37.4 ± 9.6 → 80% distribution ≈ 27–47 years
        gebjahr = random.choices(
            population=list(range(1950, 2006)),
            weights=[1 if 1977 <= y <= 1997 else 0.2 for y in range(1950, 2006)],
            k=1
        )[0]

        # National PrEP usage concentrates in Berlin, Hamburg, Cologne, Munich, Frankfurt, Nuremberg
        # Reference: [1]Valbert et al. (2024), Table 2 — ~88.6% of PrEP users lived in Berlin, Cologne, Munich, Hamburg, or Frankfurt
        # DOI: https://doi.org/10.1007/s10508-024-02922-5
        urban_plz_pool = ["10115", "20095", "50667", "80331", "60594", "90402"]  # Berlin, Hamburg, Cologne, Munich, Frankfurt, Nuremberg
        plz = random.choices(
            [random.choice(urban_plz_pool), g.address.postal_code()],
            weights=[88.6, 11.4]
        )[0]

        # Vitalstatus Bias [To simulate mortality realistically in a synthetic PrEP cohort, while reflecting real-world low death rates among PrEP users.]
        vitalstatus = random.choices([0, 1], weights=[99, 1])[0]  # [2] Bremer et al. (2022)

        # Generates a date of death between 2000 and 2022, formatted as an 8-digit integer (e.g., 20171209)
        sterbedat = (
            int(g.datetime.date(start=2000, end=2024).strftime('%Y%m%d'))
            if vitalstatus == 1 else None
        )

        # BJAHR skew based on rollout + pandemic impact
        # Ref: # [4] Schmidt et al. (2024) – COVID-19 suppressed 2020 uptake; ~26k users by end of 2021
        bjahr = random.choices(
            [2019, 2020, 2021, 2022, 2023], #[3] Deutscher Bundestag(2019). https://dserver.bundestag.de/btd/19/118/1911892.pdf: Justification of Lower boundaries of PrEP coverge
            weights=[1, 1, 3, 4, 4]
        )[0]

        bnr = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8)) 
        datenmodell = 3 # [5] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cursor.execute("""
            INSERT INTO "vers" ("VSID", "PSID", "GEBJAHR", "PLZ", "VITALSTATUS", "STERBEDAT", "BJAHR", "BNR", "DATENMODELL")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (vsid, psid, gebjahr, plz, vitalstatus, sterbedat, bjahr, bnr, datenmodell))

    conn.commit()
    print(f"Inserted {row_count} rows into 'vers'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_vers_table(conn)
    conn.close()
