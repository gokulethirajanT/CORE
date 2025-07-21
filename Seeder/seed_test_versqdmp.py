import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # RAW(32) format for PSID

def generate_versq():
    year = random.choice([2019, 2020, 2021, 2022, 2023])  # Valid FDZ years
    quarter = random.randint(1, 4)
    return int(f"{year}{quarter}")  # Format: YYYYQ

def seed_versqdmp_table(conn, row_count=1):
    cursor = conn.cursor()

    # Get valid FK combinations from versq
    cursor.execute('SELECT "VSID", "PSID", "VERSQ", "BJAHR", "BNR" FROM "versq";')
    versq_rows = cursor.fetchall()

    if not versq_rows:
        raise ValueError("versq table is empty; cannot seed versqdmp.")

    for _ in range(row_count):
        vsid, psid, versq, bjahr, bnr = random.choice(versq_rows)

        # Assign HIV-relevant DMP programs with skewed probabilities
        dmpprog = random.choices(['DM', 'CH', 'KO', 'AS', 'BP'], weights=[5, 2, 1, 2, 3])[0]  # DM = Diabetes, CH = CHD, etc. [16] Nash et al. (2018), [17] Sax et al. (2012), [21] Schmidt et al. (2020)

        # Enrich DMPTAGE based on chosen program
        if dmpprog in ['DM', 'CH', 'BP']: 
            dmptage = random.randint(40, 99)  #[17] Sax et al. (2012), [18] EACS Guidelines (2023), [20] Barrett et al. (2019)
        else:
            dmptage = random.randint(10, 60)  # Less intense DMP involvement

        datenmodell = 3  # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)


        cursor.execute("""
            INSERT INTO "versqdmp" (
                "VSID", "PSID", "VERSQ", "DMPPROG", "DMPTAGE",
                "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, versq, dmpprog, dmptage,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {row_count} synthetic rows into 'versqdmp'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="DM3_SEEDER",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_versqdmp_table(conn)
    conn.close()
