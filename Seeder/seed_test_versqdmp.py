import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale
from dotenv import load_dotenv
import os

load_dotenv()
g = Generic(locale=Locale.DE)

def get_existing_versqdmp_keys(cursor):
    cursor.execute('SELECT "PSID", "VERSQ" FROM versqdmp')
    return set(cursor.fetchall())

def get_existing_versqdmp_keys(cursor):
    cursor.execute('SELECT "PSID", "VERSQ" FROM versqdmp')
    return set(cursor.fetchall())

def seed_versqdmp_table(conn, row_count=100):
    cursor = conn.cursor()

    # Step 1: Get deduplicated FK-valid keys from versq
    cursor.execute("""
        SELECT DISTINCT ON ("PSID", "VERSQ")
            "VSID", "PSID", "VERSQ", "BJAHR", "BNR"
        FROM versq
        ORDER BY "PSID", "VERSQ", "VSID"
    """)
    all_possible = cursor.fetchall()
    all_possible_keys = {(psid, versq) for _, psid, versq, _, _ in all_possible}

    # Step 2: Get existing keys from versqdmp
    existing_keys = get_existing_versqdmp_keys(cursor)

    # Step 3: Determine new rows to insert
    to_insert_keys = list(all_possible_keys - existing_keys)
    random.shuffle(to_insert_keys)
    # ✅ Add this debug line here:
    print(f"🔍 Available keys: {len(all_possible_keys)}, Already in versqdmp: {len(existing_keys)}, Usable now: {len(to_insert_keys)}")
    selected_keys = to_insert_keys[:row_count]

    inserted = 0
    for key in selected_keys:
        psid, versq = key
        match = next(row for row in all_possible if row[1] == psid and row[2] == versq)
        vsid, psid, versq, bjahr, bnr = match

        # Assign HIV-relevant DMP programs with skewed probabilities
        dmpprog = random.choices(['DM', 'CH', 'KO', 'AS', 'BP'], weights=[5, 2, 1, 2, 3])[0]  # [16] Nash et al. (2018), [17] Sax et al. (2012), [21] Schmidt et al. (2020)

        # Enrich DMPTAGE based on chosen program
        if dmpprog in ['DM', 'CH', 'BP']: 
            dmptage = random.randint(40, 99)  # [17] Sax et al. (2012), [18] EACS Guidelines (2023), [20] Barrett et al. (2019)
        else:
            dmptage = random.randint(10, 60)  # Less intense DMP involvement

        datenmodell = 3  # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # [19] BMG (2021)

        cursor.execute("""
            INSERT INTO versqdmp (
                "VSID", "PSID", "VERSQ", "DMPPROG", "DMPTAGE",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (vsid, psid, versq, dmpprog, dmptage, bjahr, bnr, datenmodell))
        inserted += 1

    conn.commit()
    print(f" Inserted {inserted} new versqdmp rows")

if __name__ == '__main__':
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_versqdmp_table(conn)
    conn.close()