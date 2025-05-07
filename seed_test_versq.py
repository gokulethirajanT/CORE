import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # ✅ binary format

def generate_versq():
    year = random.choice([2019, 2020, 2021, 2022, 2023])  # Only valid FDZ years
    quarter = random.randint(1, 4)                        # Quarters 1 to 4
    return int(f"{year}{quarter}")

def seed_versq_table(conn, row_count=100):
    cursor = conn.cursor()

    for _ in range(row_count):
        vsid = random.randint(1000000, 9999999)
        psid = generate_psid()
        versq = generate_versq()
        geschlecht = random.choice([1, 2, 3, 4])  # 1=F, 2=M, 3=Unknown, 4=Diverse (per FDZ)
        verstage = random.randint(1, 99)  # full technical range, even rare edge cases
        verstageausl = random.randint(0, verstage // 4)
        versstatus = random.choice([10001, 10002, 10003, 99999])
        verstagekg = random.randint(0, verstage)
        verstagekosterstwahlt = random.randint(0, verstage)
        bjahr = random.choice([2019, 2020, 2021, 2022, 2023])
        bnr = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
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

    conn.commit()
    print(f"Inserted {row_count} synthetic rows into 'versq'")

if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_versq_table(conn)
    conn.close()
