import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

def calculate_prep_core_indicators():
    # Establish DB connection
    conn = psycopg2.connect(
        dbname=os.getenv("PUF_DB_NAME"),
        user=os.getenv("PUF_DB_USER"),
        password=os.getenv("PUF_DB_PASSWORD"),
        host=os.getenv("PUF_DB_HOST", "localhost"),
        port=os.getenv("PUF_DB_PORT", "5432")
    )
    cursor = conn.cursor()

    # Define time windows
    today = datetime.today()
    three_months_ago = int((today - timedelta(days=90)).strftime("%Y%m%d"))
    start_of_year = int(datetime(today.year, 1, 1).strftime("%Y%m%d"))
    six_months_ago = int((today - timedelta(days=180)).strftime("%Y%m%d"))

    # 1. Current PrEP users (received prescription in last 3 months)
    cursor.execute("""
        SELECT COUNT(DISTINCT "PSID")
        FROM rez_puf
        WHERE "PZNREZ" IN ('01380424', '12724393', '12546796', '12457896', '12634597')
        AND "ABGABEDAT" >= %s;
    """, (three_months_ago,))
    current_users = cursor.fetchone()[0]

    conn.close()
    print(f"1️⃣ Current PrEP users (last 3 months): {current_users}")


if __name__ == "__main__":
    calculate_prep_core_indicators()
