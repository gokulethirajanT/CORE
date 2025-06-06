import random
import psycopg2
from datetime import datetime, timedelta
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def generate_random_date_yyyymmdd(start_year=2019, end_year=2023):
    from datetime import datetime, timedelta
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    random_date = start + timedelta(days=random.randint(0, (end - start).days))
    return int(random_date.strftime('%Y%m%d'))  # ✅ returns 8-digit integer


def generate_end_date(beginn_yyyymmdd: int) -> int:
    beginn_date = datetime.strptime(str(beginn_yyyymmdd), "%Y%m%d")
    end_date = beginn_date + timedelta(days=random.randint(0, 30))  # within ~1 month
    return int(end_date.strftime('%Y%m%d'))

def seed_zahnfall_table(conn, row_count=100):
    cursor = conn.cursor()
    
    # 🔁 Fetch required join values from vers
    cursor.execute("""
        SELECT "VSID", "PSID", "BJAHR", "BNR"
        FROM "vers"
    """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'zahnfall'.")

    fallid_tracker = {}

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        key = (vsid, bjahr)
        fallid = fallid_tracker.get(key, 0) + 1
        fallid_tracker[key] = fallid
        fallid_str = str(fallid)

        zanr_pseudo = random.randint(1, 999)
        zanr_abr_pseudo = random.randint(1, 999)
        zakzv = random.choice([None] + list(range(1, 100)))  # includes NULL and valid values 1–99

        behandart = random.choice(['KC', 'KB', 'KF', 'PA', 'ZE'])


        beginn = generate_random_date_yyyymmdd()
        ende = generate_end_date(beginn)

        fallkost = round(random.uniform(100.00, 9000.00), 2)
        eigenlabor = round(random.uniform(0.00, 1.2 * fallkost), 2)
        # Fremdlabor: realistic range between 0 and 80% of fall cost
        fremdlabor = round(random.uniform(0.00, 0.8 * fallkost), 2)

        inanspruch = random.choice(['L', 'A', 'R', 'N', 'D', 'F'])
        datenmodell = 3

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
    print(f" Inserted {row_count} synthetic rows into 'zahnfall'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_zahnfall_table(conn)
    conn.close()
