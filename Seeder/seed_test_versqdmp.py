import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # RAW(32) format for PSID

def generate_versq():
    year = random.choice([2019, 2020, 2021, 2022, 2023])  # Valid FDZ years
    quarter = random.randint(1, 4)
    return int(f"{year}{quarter}")  # Format: YYYYQ

def seed_versqdmp_table(conn, row_count=100):
    cursor = conn.cursor()

    for _ in range(row_count):
        vsid = random.randint(1_000_000, 9_999_999)  # 7-digit pseudonym
        psid = generate_psid()                       # 32-byte pseudonym (as bytea)
        versq = generate_versq()                     # YYYYQ
        dmpprog = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=2))  # varchar(2)
        dmptage = random.randint(1, 99)                        # duration of program in days
        bjahr = random.choice([2019, 2020, 2021, 2022, 2023])
        bnr = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
        datenmodell = 3                              # fixed value

        cursor.execute("""
            INSERT INTO "versqdmp" (
                "VSID", "PSID", "VERSQ", "DMPPROG", "DMPTAGE",
                "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, versq, dmpprog, dmptage,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {row_count} synthetic rows into 'versqdmp'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_versqdmp_table(conn)
    conn.close()
