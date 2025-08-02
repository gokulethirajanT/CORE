import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

def get_fixed_prep_pzns() -> list:
    df = pd.read_csv("seeder/reference/fixed_prep_pzns.csv", dtype={"PZN": str})
    return df[df["TYPE"] == "PREP"]["PZN"].astype(str).tolist()

def calculate_prep_core_indicators():
    # Connect to PUF DB
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
    twelve_months_ago = int((today - timedelta(days=365)).strftime("%Y%m%d"))
    start_of_year = int(datetime(today.year, 1, 1).strftime("%Y%m%d"))
    end_of_year = int(datetime(today.year, 12, 31).strftime("%Y%m%d"))

    # Load the 10 fixed PrEP PZNs
    prep_pzns = get_fixed_prep_pzns()

    # 1. Current PrEP users (prescribed in last 12 months)
    cursor.execute("""
        SELECT COUNT(DISTINCT "PSID")
        FROM rez_puf
        WHERE "PZNREZ" IN %s
        AND "ABGABEDAT" >= %s;
    """, (tuple(prep_pzns), twelve_months_ago))
    current_users = cursor.fetchone()[0]
    print(f"1️ Current PrEP users (last 12 months): {current_users}")

    # 2. New PrEP users (first PrEP prescription in current year)
    cursor.execute("""
        WITH first_use AS (
            SELECT "PSID", MIN("ABGABEDAT") AS first_date
            FROM rez_puf
            WHERE "PZNREZ" IN %s
            GROUP BY "PSID"
        )
        SELECT COUNT(*)
        FROM first_use
        WHERE first_date BETWEEN %s AND %s;
    """, (tuple(prep_pzns), start_of_year, end_of_year))
    new_users = cursor.fetchone()[0]
    print(f"2️ New PrEP users (first time this year): {new_users}")


def calculate_recent_prep_before_hiv(prep_pzns: list, conn):
    """
    Calculates the proportion of individuals newly diagnosed with HIV this year
    who were prescribed PrEP in the 12 months prior to diagnosis.
    """
    cursor = conn.cursor()

    # Define year boundaries
    today = datetime.today()
    start_of_year = int(datetime(today.year, 1, 1).strftime("%Y%m%d"))
    end_of_year = int(datetime(today.year, 12, 31).strftime("%Y%m%d"))

    # Step 1: Get all HIV diagnoses this year (using khdiag_puf + khfall_puf join)
    cursor.execute("""
        SELECT d."PSID", MIN(f."AUFNDAT") AS hiv_diag_date
        FROM khdiag_puf d
        JOIN khfall_puf f ON d."FALLIDKH" = f."FALLIDKH"
        WHERE d."ICDKH_CODE" LIKE 'B20%%' OR d."ICDKH_CODE" LIKE 'Z21%%'
        GROUP BY d."PSID"
        HAVING MIN(f."AUFNDAT")::INTEGER BETWEEN %s AND %s;
    """, (start_of_year, end_of_year))
    hiv_cases = cursor.fetchall()  # List of (PSID, hiv_diag_date)

    if not hiv_cases:
        print("⚠️ No HIV diagnoses found in current year.")
        return

    # Step 2: For each person, check if PrEP was prescribed within 12 months before HIV diagnosis
    psids_with_recent_prep = set()
    for psid, hiv_date in hiv_cases:
        hiv_date = int(hiv_date)
        one_year_before = hiv_date - 10000  # crude yyyyMMdd math

        cursor.execute("""
            SELECT 1 FROM rez_puf
            WHERE "PSID" = %s
            AND "PZNREZ" IN %s
            AND "ABGABEDAT" BETWEEN %s AND %s
            LIMIT 1;
        """, (psid, tuple(prep_pzns), one_year_before, hiv_date))
        if cursor.fetchone():
            psids_with_recent_prep.add(psid)

    # Step 3: Print the result
    numerator = len(psids_with_recent_prep)
    denominator = len(hiv_cases)
    print(f"3️ Recent PrEP use before HIV diagnosis:")
    print(f"   Numerator: {numerator}")
    print(f"   Denominator (total new HIV cases): {denominator}")
    print(f"   Percentage: {round((numerator / denominator) * 100, 2) if denominator else 0.0}%")


    conn.close()

if __name__ == "__main__":
    calculate_prep_core_indicators()

    conn = psycopg2.connect(
        dbname=os.getenv("PUF_DB_NAME"),
        user=os.getenv("PUF_DB_USER"),
        password=os.getenv("PUF_DB_PASSWORD"),
        host=os.getenv("PUF_DB_HOST", "localhost"),
        port=os.getenv("PUF_DB_PORT", "5432")
    )
    prep_pzns = get_fixed_prep_pzns()
    calculate_recent_prep_before_hiv(prep_pzns, conn)

