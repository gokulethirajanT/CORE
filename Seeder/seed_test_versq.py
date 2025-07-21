import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # binary format

def generate_versq():
    year = random.choice([2019, 2020, 2021, 2022, 2023])  # Only valid FDZ years
    quarter = random.randint(1, 4)                        # Quarters 1 to 4
    return int(f"{year}{quarter}")

def choose_geschlecht():        
    return random.choices(
        population=[1, 2, 3, 4],  # Male-Dominated Gender Distribution: Target distribution: Male > Female > Unknown > Diverse      
        weights=[75, 20, 3, 2],   # [7] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023). Monitoring der HIV-Präexpositionsprophylaxe (PrEP) in Deutschland: Jahresbericht 2023. Köln: BZgA. https://www.bzga.de/forschung/studien/hivundprep/ 
        k=1
    )[0]

def seed_versq_table(conn, row_count=1):
    cursor = conn.cursor()

    # Get existing VSID, PSID, BJAHR, BNR from the vers table
    cursor.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("vers table is empty; seed 'vers' first before 'versq'.")

    cursor.execute('SELECT "PSID", "VERSQ" FROM "versq";')
    used_combinations = set(cursor.fetchall())


    if not vers_rows:
        raise ValueError("vers table is empty; seed 'vers' first before 'versq'.")

    inserted = 0
    attempts = 0
    max_attempts = row_count * 10

    while inserted < row_count and attempts < max_attempts:
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        versq = generate_versq()
        key = (psid, versq)

        if key in used_combinations:
            attempts += 1
            continue

        used_combinations.add(key)

        geschlecht = choose_geschlecht()

        # Enrichment for VERSTAGE: Higher duration for stable PrEP-related coverage
        if geschlecht == 1 and 1975 <= bjahr <= 2003:
            verstage = random.randint(180, 365)  
        else:                                    
            verstage = random.randint(30, 180)   

        # VERSTAGEAUSL enrichment: Assign foreign care days to 10–15% of cases
        if random.random() < 0.15:
            verstageausl = random.randint(1, verstage // 4)  ## [7] ECDC (2023)
        else:
            verstageausl = 0  

        # Enrichment for VERSSTATUS: Stable insurance bias for HIV/PrEP-relevant population
        versstatus = random.choices(
            population=[10001, 10002, 10003, 99999], ## [8] Insurance Status Code Source Germany 
            weights=[83, 10, 5, 2],  # [8] Müllerschön J., Koschollek C., Santos-Hövener C., et al. (2019).
            k=1                       
        )[0]

        # Randomized care days without HIV-/PrEP-specific bias
        verstagekg = random.randint(0, verstage // 2)
        verstagekosterstwahlt = random.randint(0, verstage // 2)


        datenmodell = 3  # [9] FDZ Datenmodell 3

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
    print(f"Inserted {inserted} rows into 'versq'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="DM3_SEEDER",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_versq_table(conn)
    conn.close()