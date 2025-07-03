import random
import psycopg2
from datetime import datetime, timedelta
import string

def generate_icd_code():
    length = random.randint(3, 12)
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_diag_date(start_year=2019, end_year=2023):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return int((start + timedelta(days=random.randint(0, (end - start).days))).strftime('%Y%m%d'))

def seed_ambdiag_table(conn, row_count=1):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT "VSID", "PSID", "FALLIDAMB", "BJAHR", "BNR"
        FROM "ambfall"
    """)
    ambfall_rows = cursor.fetchall()

    if not ambfall_rows:
        raise ValueError("No data found in 'ambfall'. Cannot seed 'ambdiag'.")

    fallid_tracker = {}

    for _ in range(row_count):
        vsid, psid, fallidamb, bjahr, bnr = random.choice(ambfall_rows)

        diagsich = random.choice(['V', 'G', 'Z', 'A'])       # Diagnosis certainty (unspecified made-up values)
        diaglokal = random.choice(['L', 'R', 'B'])                # Left or Right
        diagdat = generate_diag_date()                      # Diagnosis date
        icdamb_code = generate_icd_code()                   # ICD-10 Code
        icdamb_zusatz = None                                # Optional field, so NULL
        datenmodell = 3

        cursor.execute("""
            INSERT INTO "ambdiag" (
                "FALLIDAMB", "VSID", "PSID", "DIAGSICH", "DIAGLOKAL", 
                "DIAGDAT", "ICDAMB_CODE", "ICDAMB_ZUSATZ", 
                "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            fallidamb, vsid, psid, diagsich, diaglokal,
            diagdat, icdamb_code, icdamb_zusatz,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {row_count} synthetic rows into 'ambdiag'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_ambdiag_table(conn)
    conn.close()
