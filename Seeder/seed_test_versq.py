import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale
from dotenv import load_dotenv
import os
from itertools import product

load_dotenv()
g = Generic(locale=Locale.DE)
used_versqs = set()
 
def generate_valid_versq():
    year = random.choice([2021, 2022, 2023])
    quarter = random.randint(1, 4)
    return int(f"{year}{quarter}")  # e.g., 20231, 20234

def choose_geschlecht():  # [10] Schmidt et al. (2020) – The NEPOS Study Group
    return random.choices(
        population=[2, 1, 3, 4],  # 2 = male, 1 = female, 3 = unknown, 4 = diverse
        weights=[98.6, 0.8, 0.4, 0.2],  # Based on NEPOS 2020 proportions
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

    # Fill the global used_versqs set
    used_versqs.update(vq for _, vq in used_combinations)

    # Ensure each PSID gets exactly one unique VERSQ
    generated_versqs = {}

    # Build (VSID, PSID, BJAHR, BNR, VERSQ) tuples
    all_combinations = []
    for vsid, psid, bjahr, bnr in vers_rows:
        if psid not in generated_versqs:
            generated_versqs[psid] = generate_valid_versq()
        versq = generated_versqs[psid]
        if (psid, versq) not in used_combinations:
            all_combinations.append((vsid, psid, bjahr, bnr, versq))

    # Shuffle and slice
    random.shuffle(all_combinations)
    selected_rows = all_combinations[:row_count]

    seen = set(used_combinations)
    inserted = 0

    for vsid, psid, bjahr, bnr, versq in selected_rows:
        if (psid, versq) not in seen:
            seen.add((psid, versq))

            geschlecht = choose_geschlecht()

            if geschlecht == 1 and 1975 <= bjahr <= 2003: # [10] Schmidt et al. (2020) – The NEPOS Study Group
                verstage = random.randint(360, 500)  # centered around 451 days
            else:
                verstage = random.randint(30, 180)   # lower retention group


            verstageausl = random.randint(1, verstage // 4) if random.random() < 0.15 else 0
            versstatus = random.choices(
                population=[ # [8] Insurance Status Code Source Germany
                    10001,  # Member of statutory insurance (GKV) – most common among PrEP users [8]
                    10002,  # Retired/disabled – less common in PrEP cohort due to younger age profile [8]
                    10003,  # Dependent/family-insured – some younger or migrant users fall under this [8]
                    99999   # Placeholder for unknown/undocumented status (e.g., asylum seekers, irregular access) [9]
                ],
                weights=[ # [9] Müllerschön J., Koschollek C., Santos-Hövener C., et al. (2019). Migrants from sub-Saharan Africa on access to health care and HIV testing in Germany 
                    83,     # Majority are full GKV members (working adults, students, etc.)
                    10,     # Retired/disabled – small portion
                    5,      # Family-insured partners or dependents – minority
                    2       # No valid insurance/unknown – aligns with vulnerability data from migrant PrEP access studies [9]
                ],
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