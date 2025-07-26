import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale
from dotenv import load_dotenv
import os
from itertools import product

load_dotenv()
g = Generic(locale=Locale.DE)

def choose_geschlecht():        
    return random.choices(
        population=[1, 2, 3, 4],  # Male-Dominated Gender Distribution
        weights=[75, 20, 3, 2],   # [7] BZgA (2023) - PrEP Monitoring
        k=1
    )[0]

def seed_versq_table(conn, row_count=100):
    cursor = conn.cursor()

    # Get existing VSID, PSID, BJAHR, BNR from the vers table
    cursor.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    vers_rows = cursor.fetchall()
    if not vers_rows:
        raise ValueError("vers table is empty; seed 'vers' first before 'versq'.")

    # Load already-used (PSID, VERSQ) combinations in versq
    cursor.execute('SELECT "PSID", "VERSQ" FROM "versq";')
    used_combinations = set(cursor.fetchall())

    # Generate all possible VERSQ values (20 total)
    valid_versq = [int(f"{year}{q}") for year in range(2019, 2024) for q in range(1, 5)]

    # Build all unique (PSID, VERSQ) pairs, skip already used
    all_combinations = [
        (vsid, psid, bjahr, bnr, versq)
        for vsid, psid, bjahr, bnr in vers_rows
        for versq in valid_versq
        if (psid, versq) not in used_combinations
    ]

    # Shuffle and slice
    random.shuffle(all_combinations)
    selected_rows = all_combinations[:row_count]

    seen = set(used_combinations)
    inserted = 0

    for vsid, psid, bjahr, bnr, versq in selected_rows:
        if (psid, versq) not in seen:
            seen.add((psid, versq))

            geschlecht = choose_geschlecht()

            if geschlecht == 1 and 1975 <= bjahr <= 2003:
                verstage = random.randint(180, 365)
            else:
                verstage = random.randint(30, 180)

            verstageausl = random.randint(1, verstage // 4) if random.random() < 0.15 else 0

            versstatus = random.choices(
                population=[10001, 10002, 10003, 99999],
                weights=[83, 10, 5, 2],
                k=1
            )[0]

            verstagekg = random.randint(0, verstage // 2)
            verstagekosterstwahlt = random.randint(0, verstage // 2)
            datenmodell = 3

            cursor.execute("""
                INSERT INTO "versq" (
                    "VSID", "PSID", "VERSQ", "GESCHLECHT", "VERSTAGE", "VERSTAGEAUSL",
                    "VERSSTATUS", "VERSTAGEKG", "VERSTAGEKOSTERSTWAHLT", "BJAHR", "BNR", "DATENMODELL"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                vsid, psid, versq, geschlecht, verstage, verstageausl,
                versstatus, verstagekg, verstagekosterstwahlt, bjahr, bnr, datenmodell
            ))

            inserted += 1

    conn.commit()
    print(f" Inserted {inserted} rows into 'versq'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_versq_table(conn)
    conn.close()
