import random
import psycopg2
from datetime import datetime
from mimesis import Generic
from mimesis.enums import Locale

# Use German locale for realistic PLZ, dates, etc.
g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # ✅ binary format

def seed_vers_table(conn, row_count=100):
    cursor = conn.cursor()

    for _ in range(row_count):
        vsid = random.randint(1000000, 9999999)  # 7-digit unique ID
        psid = generate_psid()
        gebjahr = random.randint(1920, 2005)
        plz = g.address.postal_code()
        vitalstatus = random.choices([0, 1], weights=[95, 5])[0]  # 95% alive, 5% dead
        sterbedat = (
            int(g.datetime.date(start=2000, end=2022).strftime('%Y%m%d'))
            if vitalstatus == 1 else None
        )
        bjahr = random.choice([2019, 2020, 2021, 2022, 2023])
        bnr = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
        datenmodell = 3

        cursor.execute("""
            INSERT INTO "vers" ("VSID", "PSID", "GEBJAHR", "PLZ", "VITALSTATUS", "STERBEDAT", "BJAHR", "BNR", "DATENMODELL")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (vsid, psid, gebjahr, plz, vitalstatus, sterbedat, bjahr, bnr, datenmodell))

    conn.commit()
    print(f"✅ Inserted {row_count} synthetic rows into 'vers'")


if __name__ == "__main__":
    # Update credentials as needed
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_vers_table(conn)
    conn.close()
