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

def choose_geschlecht():        
    return random.choices(
        population=[1, 2, 3, 4],  # Male-Dominated Gender Distribution: Target distribution: Male > Female > Unknown > Diverse      
        weights=[75, 20, 3, 2],   # [7] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023). Monitoring der HIV-Präexpositionsprophylaxe (PrEP) in Deutschland: Jahresbericht 2023. Köln: BZgA. https://www.bzga.de/forschung/studien/hivundprep/ 
        k=1
    )[0]


def seed_versq_table(conn, row_count=1):
    cursor = conn.cursor()

    # Get existing VSID, PSID, BJAHR, BNR from the vers table
    cursor.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    vers_rows = cursor.fetchall()

    if not vers_rows:
        raise ValueError("vers table is empty; seed 'vers' first before 'versq'.")

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)
        versq = generate_versq()
        geschlecht = choose_geschlecht()
        # Enrichment for VERSTAGE: Higher duration for stable PrEP-related coverage
        if geschlecht == 1 and 1975 <= bjahr <= 2003:
            verstage = random.randint(180, 365)  # Simulate full-year coverage for likely PrEP users  
        else:                                    # [10] Spinner, C. D., Boesecke, C., Zink, A., Jessen, H., Stellbrink, H.-J., & Rockstroh, J. K. (2018). [11] World Health Organization (2015). [12] Grant, R. M., Lama, J. R., Anderson, P. L., et al. (2010). 
            verstage = random.randint(30, 180)   # Less stable or short-term coverage 
        # VERSTAGEAUSL enrichment: Assign foreign care days to 10–15% of cases. Increased Cross-Border Treatment Days
        if random.random() < 0.12:
            verstageausl = random.randint(1, verstage // 4)  # [14] European Centre for Disease Prevention and Control (ECDC). (2023). https://www.ecdc.europa.eu/en/publications-data/hiv-prevention-and-care-among-migrants-europe
        else:
            verstageausl = 0  # [15] GKV-Spitzenverband. Grenzüberschreitende Gesundheitsversorgung: https://www.gkv-spitzenverband.de/krankenversicherung/ausland/ausland.jsp

        # Enrichment for VERSSTATUS: Stable insurance bias for HIV/PrEP-relevant population
        versstatus = random.choices(
            population=[10001, 10002, 10003, 99999], # [13] GKV-Spitzenverband (2022). https://www.gkv-datenaustausch.de/media/dokumente/leistungserbringer/ambulanter_bereich/Verzeichnis_Schluesselzahlen.pdf
            weights=[70, 20, 8, 2],  # [3] Marcus, U., Kollan, C., Bremer, V., & Zimmermann, R. (2023). HIV-Präexpositionsprophylaxe (PrEP) in Deutschland – Eine Analyse der Versorgungsdaten und Nutzungscharakteristika. Bundesgesundheitsblatt – Gesundheitsforschung – Gesundheitsschutz, 66(10), 1081–1091. https://doi.org/10.1007/s00103-023-03733-0  & [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/
            k=1                       
        )[0]
        # Enrichment for specialized care days (PrEP users may use clinics, STI centers, etc.), Higher for PrEP patients
        if geschlecht == 1 and 1975 <= bjahr <= 2003:
            verstagekg = random.randint(15, verstage // 2)              # [3] Marcus et al. (2023). https://doi.org/10.1007/s00103-023-03733-0
            verstagekosterstwahlt = random.randint(10, verstage // 2)   # [10] Spinner et al. (2018). https://doi.org/10.1007/s15010-018-1185-5
        else:
            verstagekg = random.randint(0, verstage // 4)
            verstagekosterstwahlt = random.randint(0, verstage // 4)

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
