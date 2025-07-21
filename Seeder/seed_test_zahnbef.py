import random
import psycopg2
from mimesis import Generic
from mimesis.enums import Locale

g = Generic(locale=Locale.DE)

def seed_zahnbef_table(conn, row_count=1):
    cursor = conn.cursor()

    #  Fetch FALLIDZAHN and associated values from zahnfall
    cursor.execute("""
        SELECT "VSID", "PSID", "FALLIDZAHN", "BJAHR", "BNR"
        FROM "zahnfall"
    """)
    zahnfall_rows = cursor.fetchall()

    if not zahnfall_rows:
        raise ValueError("No rows found in 'zahnfall'. Cannot seed 'zahnbef'.")

    for _ in range(row_count):
        vsid, psid, fallid_str, bjahr, bnr = random.choice(zahnfall_rows)

        # Adjusted weights: HIV-relevant codes more likely
        hiv_enriched_befnr = ['2.4', '4.3', '4.5', '4.6', '5.3']  # [22] Patton et al. (2002). Oral manifestations of HIV in a southeast USA population.
        valid_befnr = [                                           # [23] WHO (2022). Global Oral Health Status Report.
            '1.1', '1.2', '2.1', '2.2', '2.3', '2.4', '3.1', '4.3', '4.5', '5.3', '6.1', '7.1' # [24] EACS (2023). European AIDS Clinical Society Guidelines v12.0.
        ]
        all_befnr = valid_befnr + hiv_enriched_befnr # [25] Ramírez-Amador et al. (2003). Oral lesions as clinical markers in HIV/AIDS.
        # Boost HIV-relevant codes
        befnr = random.choices(
            all_befnr,
            weights=[1 if b not in hiv_enriched_befnr else 5 for b in all_befnr] # [26] UNAIDS (2021). Oral health and HIV/AIDS: Working together.
        )[0]

        # Tooth positions
        zahn = str(random.choice( # [27] Lamster et al. (1998). Oral lesions and periodontal disease in HIV infection. [28] Murray et al. (2021). Dental care for people with HIV. [29] Cameron et al. (2016). Oral complications in HIV disease.
            list(range(11, 49)) +   # Permanent  
            list(range(51, 56)) +   # Primary upper right
            list(range(61, 66)) +   # Primary upper left
            list(range(71, 76)) +   # Primary lower left
            list(range(81, 86))     # Primary lower right
        ))

        refart = random.choices([None, "1"], weights=[99, 1])[0]
        befnrzahl = random.randint(1, 9999)
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

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
    print(f"Inserted {row_count} rows into 'zahnbef'")


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="DM3_SEEDER",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432"
    )
    seed_zahnbef_table(conn)
    conn.close()
