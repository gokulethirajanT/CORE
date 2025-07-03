import random
import psycopg2
from datetime import datetime, timedelta
import string
import uuid

def generate_random_date_int(start_year=2019, end_year=2023):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return int((start + timedelta(days=random.randint(0, (end - start).days))).strftime('%Y%m%d'))

def generate_punktzahl():
    # Fit within observed FDZ test dataset distribution
    value = random.gauss(mu=440, sigma=150)
    value = max(4.4, min(value, 900))  # match min/max bounds
    return round(value, 1)

def generate_fallkoamb():
    # Simulate skewed outpatient cost range, center around ~3000 EUR
    value = random.gauss(mu=4000, sigma=3000)
    value = max(50.0, min(value, 25000.0))  # Clamp between 50–25,000 EUR
    return round(value, 2)

def generate_dialyse_cost():
    value = random.gauss(mu=95000000, sigma=7000000)  # Mean ~95M EUR
    value = max(80000000, min(value, 110000000))       # Clamp to 80M–110M EUR
    return round(value, 2)

def seed_ambfall_table(conn, row_count=1):
    cursor = conn.cursor()

    cursor.execute("""SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers" """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'ambfall'.")

    fallid_tracker = {}

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        key = (vsid, bjahr)
        fallid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))

        year = random.randint(2019, 2023)         # Valid years from the dataset
        quarter = random.randint(1, 4)            # Valid quarters: 1 to 4
        abrq = int(f"{year}{quarter}")            # Combine as YYYYQ

        svnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=11)) # https://www.bundesgesundheitsministerium.de/service/begriffe-von-a-z/s/selektivvertrag.html
        svtyp = random.choice([1, 2])  
        bsnrpseudo = random.randint(1, 9999)
        bsnrkv = random.randint(1, 99)
        bsnruebpseudo = random.randint(100, 999)
        bsnruebkv = random.randint(1, 99)
        lanruebpseudo = random.randint(100000000000, 999999999999)  # 12-digit pseudonym
        lanruebfg = random.randint(1, 99)
        inansprartamb = random.choice(['0', 'O', 'V', 'N', 'Z', 'K', 'M', '7', '8'])
        unfall = random.choice([0, 2, 3])
        behandartamb = random.choice([1, 2]) # 1 = unspecified treatment type A, 2 = treatment type B
        entbindungsdat = generate_random_date_int()
        punktzahl = generate_punktzahl()
        fallkoamb = generate_fallkoamb()
        dialysesachko = generate_dialyse_cost()
        beginndatamb = generate_random_date_int()
        endedatamb = generate_random_date_int()
        if endedatamb < beginndatamb:
            beginndatamb, endedatamb = endedatamb, beginndatamb
        datenmodell = 3

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
    print(f"Inserted {row_count} synthetic rows into 'ambfall'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_ambfall_table(conn)
    conn.close()
