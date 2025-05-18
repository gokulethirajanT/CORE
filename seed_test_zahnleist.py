import random
import psycopg2
from datetime import datetime, timedelta

def generate_random_date(start_year=2019, end_year=2023):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    random_date = start + timedelta(days=random.randint(0, (end - start).days))
    return int(random_date.strftime("%Y%m%d"))  # returns YYYYMMDD as integer

def seed_zahnleist_table(conn, row_count=100):
    cursor = conn.cursor()

    # 🧩 Join data from `vers`
    cursor.execute("""
        SELECT "VSID", "PSID", "BJAHR", "BNR"
        FROM "vers"
    """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'zahnleist'.")

    fallid_tracker = {}

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        key = (vsid, bjahr)
        fallid = fallid_tracker.get(key, 0) + 1
        fallid_tracker[key] = fallid
        fallid_str = str(fallid)

        leistungsdatum = generate_random_date()

        # Tooth positions: use adult + child mixed
        # Permanent: 11–48, Primary: 51–55, 61–65, 71–75, 81–85
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
        datenmodell = 3

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
    print(f"Inserted {row_count} synthetic rows into 'zahnleist'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_zahnleist_table(conn)
    conn.close()
