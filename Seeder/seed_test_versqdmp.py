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

def seed_versqdmp_table(conn, row_count=100):
    cursor = conn.cursor()

    #  Step 1: Get deduplicated FK-valid keys from versq
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

    #  Step 3: Filter for only FK-valid, non-duplicate keys
    to_insert_keys = list(all_possible_keys - existing_keys)
    random.shuffle(to_insert_keys)
    print(f"🔍 Available keys: {len(all_possible_keys)}, Already used: {len(existing_keys)}, Usable: {len(to_insert_keys)}")

    selected_keys = to_insert_keys[:row_count]

    inserted = 0
    for psid, versq in selected_keys:
        #  Match (PSID, VERSQ) to full row
        match = next((row for row in all_possible if row[1] == psid and row[2] == versq), None)
        if not match:
            continue
        vsid, psid, versq, bjahr, bnr = match

        dmpprog = random.choice(['DM', 'CH', 'KO', 'AS', 'BP'])  

        if dmpprog in ['DM', 'CH', 'BP']: 
            dmptage = random.randint(40, 99)  
        else:
            dmptage = random.randint(10, 60)  

        datenmodell = 3   

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
