import random
import psycopg2
from datetime import datetime
from mimesis import Generic
from mimesis.enums import Locale

# Use German locale for realistic PLZ, dates, etc.
g = Generic(locale=Locale.DE)

def generate_psid():
    return bytes.fromhex(''.join(random.choices('0123456789ABCDEF', k=32)))  # binary format

def seed_vers_table(conn, row_count=1):
    cursor = conn.cursor()

    for _ in range(row_count):
        vsid = random.randint(1000000, 9999999)  # 7-digit unique ID
        psid = generate_psid()

        # Age Distribution Enrichment (GEBJAHR): 70% from HIV-PrEP active group (1980–2000), 30% from general adult pool , Aligning GEBJAHR with the real-world PrEP user base — predominantly aged 25 to 45, i.e., birth years between 1980 and 2000 [Find References Below]
        gebjahr = random.choices(
            population = list(range(1950, 2006)),                                         #[1] Marcus, U., Zimmermann, R., Kollan, C., & Bremer, V. (2024). HIV and PrEP in Germany: Characteristics of PrEP users and their HIV-related behaviors. Archives of Sexual Behavior. https://doi.org/10.1007/s10508-024-02922-5
            weights = [1 if 1980 <= y <= 2000 else 0.3 for y in range(1950, 2006)],       #[2] Robert Koch-Institut. (2024). Schätzung der Anzahl der HIV-Neuinfektionen in den Jahren 2022 und 2023 sowie der Gesamtzahl der Menschen, die Ende 2023 mit HIV in Deutschland leben (Epidemiologisches Bulletin 28/2024). https://www.rki.de/DE/Aktuelles/Publikationen/Epidemiologisches-Bulletin/2024/28_24.pdf?__blob=publicationFile&v=2
            k = 1                                                                         #[3] Marcus, U., Kollan, C., Bremer, V., & Zimmermann, R. (2023). HIV-Präexpositionsprophylaxe (PrEP) in Deutschland – Eine Analyse der Versorgungsdaten und Nutzungscharakteristika. Bundesgesundheitsblatt – Gesundheitsforschung – Gesundheitsschutz, 66(10), 1081–1091. https://doi.org/10.1007/s00103-023-03733-0  
        )[0]

        # National PrEP usage concentrates in Berlin, Hamburg, Cologne, Munich, Frankfurt, Nuremberg
        urban_plz_pool = ["10115", "20095", "50667", "80331", "60594", "90402"]  # major PrEP cities
        plz = random.choices(                                                             #[1] Marcus et al. (2024);[2] RKI Bulletin 28/2024;[3] BZgA PrEP Monitoring (2023)
            [random.choice(urban_plz_pool), g.address.postal_code()],                     #[4] Cordioli M, Gios L, Huber JW, et alEstimating the percentage of European MSM eligible for PrEP: insights from a bio-behavioural survey in thirteen citiesSexually Transmitted Infections 2021;97:534-540.
            weights=[70, 30]
        )[0]  

        # Vitalstatus Bias [To simulate mortality realistically in a synthetic PrEP cohort, while reflecting real-world low death rates among PrEP users.]
        vitalstatus = random.choices([0, 1], weights=[98, 2])[0]  # 0 = alive, 1 = dead   #[5] Klein, H., Bräunig, J., Jansen, K., Funke, J., Drewes, J., & Burchard, G. D. (2022). PrEP adherence and retention in Germany: A cohort study among men who have sex with men. AIDS and Behavior, 26(3), 847–858. https://doi.org/10.1007/s10461-021-03537-3
        
        # Generates a date of death between 2000 and 2022, formatted as an 8-digit integer (e.g., 20171209)
        sterbedat = (
            int(g.datetime.date(start=2000, end=2022).strftime('%Y%m%d'))
            if vitalstatus == 1 else None
        )

        # Sets the range of possible reporting years, corresponding to the period after PrEP became reimbursable by GKV (statutory health insurance).
        bjahr = random.choices(
        [2019, 2020, 2021, 2022, 2023], #[6] Deutscher Bundestag(2019). https://dserver.bundestag.de/btd/19/118/1911892.pdf
        weights=[1, 2, 3, 3, 3]         #[7] Bundeszentrale für gesundheitliche Aufklärung (BZgA). (2023). Monitoring der HIV-Präexpositionsprophylaxe (PrEP) in Deutschland: Jahresbericht 2023. Köln: BZgA. https://www.bzga.de/forschung/studien/hivundprep/ 
        )[0]

        bnr = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8)) #[8] GKV-Spitzenverband. (2023). Betriebsnummern und Vertragspartnerkennzeichen. https://www.gkv-datenaustausch.de
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/

        cursor.execute("""
            INSERT INTO "vers" ("VSID", "PSID", "GEBJAHR", "PLZ", "VITALSTATUS", "STERBEDAT", "BJAHR", "BNR", "DATENMODELL")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (vsid, psid, gebjahr, plz, vitalstatus, sterbedat, bjahr, bnr, datenmodell))

    conn.commit()
    print(f"Inserted {row_count} rows into 'vers'")


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
