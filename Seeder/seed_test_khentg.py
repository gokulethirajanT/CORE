import random
import psycopg2
from datetime import date, timedelta
import string

# Date generator: specific to HIV enrichment
def generate_billing_dates(bjahr: int, hiv_positive: bool = True) -> tuple[str, str]: # [89] Sabin, C. A., et al. (2021). "Time on ART and frequency of outpatient visits in HIV cohorts.
    """
    HIV+ treatments usually span longer periods per billing cycle.
    """
    start_day_offset = random.randint(0, 300)
    duration_days = random.randint(15, 90) if hiv_positive else random.randint(1, 30)

    abrvondat = date(bjahr, 1, 1) + timedelta(days=start_day_offset)
    abrbisdat = abrvondat + timedelta(days=duration_days)
    return abrvondat.strftime("%Y%m%d"), abrbisdat.strftime("%Y%m%d")


# Synthetic ENTGART pool (can be replaced with real Schlüssel 4 values)
def generate_entgart(hiv_positive: bool = True) -> str:
    if hiv_positive:
        pool = ["HIVMED01", "ARTCOST2", "ANTIVIR3", "LABBILL4", "ADHERNC5"]
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
    else:
        pool = ["STDGEN01", "ACUTEC02", "ROUTINE3", "LABGEN04", "OTHRGEN5"]
        weights = [0.2, 0.2, 0.2, 0.2, 0.2]
    return random.choices(pool, weights=weights)[0][:8]  # ← this part is critical

# Billing amount generator
def generate_entgbetrag(hiv_positive: bool = True) -> float: # [86] Kuhlmann, A., et al. (2017). "Cost of HIV treatment in Germany: Drivers and policy implications."
    """
    ART and HIV care have higher average reimbursement.
    HIV+ values lean toward upper half of range.
    """
    if hiv_positive:
        return round(random.uniform(3000, 20000), 2)
    else:
        return round(random.uniform(100, 8000), 2)


# Number of billed items
def generate_entgzahl(hiv_positive: bool = True) -> str: # [77] Altice, F. L., et al. (2016). "Expanded HIV care requires increased diagnostic and monitoring frequency." *Journal of Acquired Immune Deficiency Syndromes*, 72(3), e59–e65.

    """
    HIV patients often require multiple lab tests and medication units per encounter.
    """
    if hiv_positive:
        return f"{random.randint(10, 120):03d}"
    else:
        return f"{random.randint(1, 50):03d}"


# Days above threshold
def generate_tageobe(hiv_positive: bool = True) -> str: # [88] Shubber, Z., et al. (2016). "Barriers to HIV treatment adherence: A global systematic review." *AIDS Care*, 28(2), 132–138. https://doi.org/10.1080/09540121.2016.1179717
    """
    HIV-positive patients may have longer treatment delays, follow-ups, or billing reconciliation.
    """
    if hiv_positive: 
        return str(random.randint(5, 30))
    else:
        return str(random.randint(0, 10))



# Main seeding function
def seed_khentg_table(conn, rows: int = 500):
    cur = conn.cursor()

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khfall";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khentg.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)

        entgart = generate_entgart()[:8] # [85] Becker, A. C., et al. (2020). "Healthcare costs associated with HIV treatment in Germany: A retrospective analysis." 
        entgbetrag = generate_entgbetrag() # [86] Kuhlmann, A., et al. (2017). "Cost of HIV treatment in Germany: Drivers and policy implications."
        abrvondat, abrbisdat = generate_billing_dates(bjahr)  # [90] Sabin, C. A., et al. (2021). "Time on ART and frequency of outpatient visits in HIV cohorts.
        entgzahl = generate_entgzahl() # [77] Altice, F. L., et al. (2016). "Expanded HIV care requires increased diagnostic and monitoring frequency." *Journal of Acquired Immune Deficiency Syndromes*, 72(3), e59–e65.
        tageobe = generate_tageobe() # [88] Shubber, Z., et al. (2016). "Barriers to HIV treatment adherence: A global systematic review." *AIDS Care*, 28(2), 132–138. https://doi.org/10.1080/09540121.2016.1179717
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        # Ensure ABRBISDAT is not before ABRVONDAT
        if abrbisdat < abrvondat:
            abrvondat, abrbisdat = abrbisdat, abrvondat

        cur.execute("""
            INSERT INTO "khentg" (
                "VSID", "PSID", "FALLIDKH",
                "ENTGART", "ENTGBETRAG", "ABRVONDAT", "ABRBISDAT",
                "ENTGZAHL", "TAGEOBE", "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            entgart, entgbetrag, abrvondat, abrbisdat,
            entgzahl, tageobe, bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khentg'.")

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="DM3_SEEDER",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432",
    )
    try:
        seed_khentg_table(conn, rows=1)
    finally:
        conn.close()
