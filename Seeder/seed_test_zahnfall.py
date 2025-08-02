import random
import psycopg2
from datetime import datetime, timedelta
from mimesis import Generic
from mimesis.enums import Locale
from dotenv import load_dotenv
import os


load_dotenv()
g = Generic(locale=Locale.DE)

def generate_random_date_yyyymmdd(start_year=2019, end_year=2023):
    from datetime import datetime, timedelta
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    random_date = start + timedelta(days=random.randint(0, (end - start).days))
    return int(random_date.strftime('%Y%m%d'))  #  returns 8-digit integer

def generate_end_date(beginn_yyyymmdd: int) -> int:
    beginn_date = datetime.strptime(str(beginn_yyyymmdd), "%Y%m%d")
    end_date = beginn_date + timedelta(days=random.randint(0, 30))  # within ~1 month
    return int(end_date.strftime('%Y%m%d'))

def seed_zahnfall_table(conn, row_count=1000):
    cursor = conn.cursor()
    
    #  Fetch required join values from vers
    cursor.execute("""
        SELECT "VSID", "PSID", "BJAHR", "BNR"
        FROM "vers"
    """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'zahnfall'.")

    # Step 1: Fetch all existing FALLIDZAHN values
    cursor.execute('SELECT "FALLIDZAHN" FROM "zahnfall";')
    existing_ids = set(row[0] for row in cursor.fetchall())

    # Step 2: Track counters based on vsid+bjahr to prevent duplicates
    fallid_counters = {}  # key: (vsid, bjahr) → int

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        key = (vsid, bjahr)

        if key not in fallid_counters:
            # Find max fallid so far for this person-year
            prefix = f"{str(bjahr)[-2:]}{vsid % 100000:05d}"
            max_suffix = max(
                [int(fid[-2:]) for fid in existing_ids if fid.startswith(prefix)],
                default=0
            )
            fallid_counters[key] = max_suffix

        fallid_counters[key] += 1
        fallid_str = f"{str(bjahr)[-2:]}{vsid % 100000:05d}{fallid_counters[key]:02d}"


        zanr_pseudo = random.randint(1, 999)
        zanr_abr_pseudo = random.randint(1, 999)
        zakzv = random.choices( # [30] Lodi et al. (2014)
            population=[None] + list(range(1, 100)),
            weights=[1] + [5] * 99,  # NULL has low weight, valid values favored
            k=1
        )[0]

        
        behandart = random.choices( # [30] Lodi et al. (2014) – Enrichment for PA and ZE due to HIV-associated dental risks
            population=['KC', 'KB', 'KF', 'PA', 'ZE'],
            weights=[1, 1, 1, 4, 4],  # PA and ZE favored
            k=1
        )[0]

        beginn = generate_random_date_yyyymmdd()
        ende = generate_end_date(beginn)

        fallkost = round(random.uniform(300.00, 12000.00), 2)
        eigenlabor = round(random.uniform(0.00, 1.2 * fallkost), 2)
        # Fremdlabor: realistic range between 0 and 80% of fall cost
        fremdlabor = round(random.uniform(0.00, 0.8 * fallkost), 2)

        inanspruch = random.choice(['L', 'A', 'R', 'N', 'D', 'F'])
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cursor.execute("""
            INSERT INTO "zahnfall" (
                "VSID", "PSID", "FALLIDZAHN", "ZANRPSEUDO", "ZANRABRPSEUDO", "ZAKZV",
                "BEHANDARTZAHN", "BEGINNDATZAHN", "ENDEDATZAHN", "FALLKOZAHN",
                "EIGENLABOR", "FREMDLABOR", "INANSPRARTZAHN", "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, fallid_str, zanr_pseudo, zanr_abr_pseudo, zakzv,
            behandart, beginn, ende, fallkost,
            eigenlabor, fremdlabor, inanspruch, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {row_count} rows into 'zahnfall'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_zahnfall_table(conn)
    conn.close()
