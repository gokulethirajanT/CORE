import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def seed_zahnbef_table(conn, row_count=100):
    cursor = conn.cursor()

    # 🔁 Fetch required join values from vers
    cursor.execute("""
        SELECT "VSID", "PSID", "BJAHR", "BNR"
        FROM "vers"
    """)
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("No rows found in 'vers'. Cannot seed 'zahnbef'.")

    fallid_tracker = {}

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        key = (vsid, bjahr)
        fallid = fallid_tracker.get(key, 0) + 1
        fallid_tracker[key] = fallid

        fallid_str = str(fallid)  # VARCHAR(11)
        valid_befnr = [
            '1.1', '1.2', '1.3', '1.4', '1.5',
            '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
            '3.1', '3.2',
            '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9',
            '5.1', '5.2', '5.3', '5.4',
            '6.1', '6.2', '6.3',
            '7.1', '7.2', '7.5', '7.6', '7.7',
            '8.1']
        befnr = random.choice(valid_befnr)

        # Permanent: 11–48, Primary: 51–55, 61–65, 71–75, 81–85
        zahn = str(random.choice(
            list(range(11, 49)) +   # Permanent
            list(range(51, 56)) +   # Primary upper right
            list(range(61, 66)) +   # Primary upper left
            list(range(71, 76)) +   # Primary lower left
            list(range(81, 86))     # Primary lower right
        ))

        # 1% of rows will be retrospective findings
        refart = random.choices([None, "1"], weights=[99, 1])[0]
        befnrzahl = random.randint(1, 9999)  # 0.01 to 99.99
        datenmodell = 3

        cursor.execute("""
            INSERT INTO "zahnbef" (
                "VSID", "PSID", "FALLIDZAHN", "BEFNR", "ZAHN", "REFART",
                "BEFNRZAHL", "BJAHR", "BNR", "DATENMODELL"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vsid, psid, fallid_str, befnr, zahn, refart,
            befnrzahl, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {row_count} complete rows into 'zahnbef'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_zahnbef_table(conn)
    conn.close()
