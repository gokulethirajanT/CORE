import random
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


load_dotenv()
def generate_enriched_leistungsdatum():
    # More weight toward recent years (esp. 2022–2023)
    year = random.choices([2019, 2020, 2021, 2022, 2023], weights=[1, 2, 3, 6, 8])[0]

    # Q2 and Q4 visits more common in HIV follow-up
    month_weights = [1, 2, 4, 6, 3, 2, 1, 2, 4, 6, 3, 2]  # Higher for Apr-Jun, Oct-Dec
    month = random.choices(range(1, 13), weights=month_weights)[0]

    # Choose random day in that month
    day = random.randint(1, 28)  # Simplification: avoid month-end issues
    return int(datetime(year, month, day).strftime("%Y%m%d"))  # YYYYMMDD

def seed_zahnleist_table(conn, row_count=1000):
    cursor = conn.cursor()

    # Pull valid combinations from zahnfall (since FALLIDZAHN must exist)
    cursor.execute("""
        SELECT "VSID", "PSID", "FALLIDZAHN", "BJAHR", "BNR"
        FROM "zahnfall"
    """)
    zahnfall_rows = cursor.fetchall()

    if not zahnfall_rows:
        raise ValueError("No rows found in 'zahnfall'. Cannot seed 'zahnleist'.")

    for _ in range(row_count):
        vsid, psid, fallid_str, bjahr, bnr = random.choice(zahnfall_rows)

        leistungsdatum = generate_enriched_leistungsdatum() # Based on [27] Meurer et al. (2021)

        tooth_id = str(random.choice(
            list(range(11, 49)) +   # Permanent
            list(range(51, 56)) +   # Primary upper right
            list(range(61, 66)) +   # Primary upper left
            list(range(71, 76)) +   # Primary lower left
            list(range(81, 86))     # Primary lower right
        ))

        gebnr = random.choice(['0099Ä', '7326Ä', '25z', '34k', '88x', '1234A', '876B'])
        gebpos = str(random.randint(100, 999)).zfill(3)
        gebnrzahl = random.randint(1, 4)
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        cursor.execute("""
            INSERT INTO "zahnleist" (
                "VSID", "PSID", "FALLIDZAHN", "LEISTDAT", "ZAHN", "GEBNR",
                "GEBPOS", "GEBNRZAHL", "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, fallid_str, leistungsdatum, tooth_id, gebnr,
            gebpos, gebnrzahl, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {row_count} rows into 'zahnleist'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_zahnleist_table(conn)
    conn.close()
