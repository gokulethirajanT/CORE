from datetime import date, timedelta, datetime
import random
import string
import psycopg2

def random_date_in_year(year: int) -> str:
    """Returns a random date in YYYYMMDD format within the given year."""
    d = date(year, 1, 1) + timedelta(days=random.randint(0, 364))
    return d.strftime("%Y%m%d")

def generate_pznrez() -> str:
    """Generate a synthetic pharmaceutical number of 8 or 10 digits."""
    return ''.join(random.choices(string.digits, k=random.choice([8, 10])))

def generate_id(length: int = 9) -> str:
    """Generate a random numeric string of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def generate_amount(min_val=5.00, max_val=200.00) -> float:
    """Generate a random float rounded to 2 decimal places."""
    return round(random.uniform(min_val, max_val), 2)

def seed_rez_table(conn, rows: int = 500):
    cur = conn.cursor()
    cur.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("vers table is empty; cannot seed rez.")

    reznr_set = set()

    for _ in range(rows):
        vsid, psid, bjahr, bnr = random.choice(ref_rows)
        datenmodell = 3

        # Ensure unique REZNR
        while True:
            reznr = random.randint(100_000_000, 999_999_999)
            if reznr not in reznr_set:
                reznr_set.add(reznr)
                break

        pznrez = generate_pznrez()

        # Date handling
        vodat_str = random_date_in_year(bjahr)
        abgabedat_str = random_date_in_year(bjahr)
        vodat = datetime.strptime(vodat_str, "%Y%m%d").date()
        abgabedat = datetime.strptime(abgabedat_str, "%Y%m%d").date()
        if abgabedat < vodat:
            vodat, abgabedat = abgabedat, vodat
        vodat_int = int(vodat.strftime("%Y%m%d"))
        abgabedat_int = int(abgabedat.strftime("%Y%m%d"))

        # Field values
        bsnrvopseudo = generate_id(12)
        bsnrvovb = random.randint(10, 99)
        bsnrvoregknz = random.randint(10, 99)
        lenrvopseudo = generate_id(12)
        lenrvofg = random.randint(10, 99)
        vertragskz = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(10, 25)))
        apopseudo = generate_id(12)
        apoklass = f"{random.randint(10, 99)}"
        aporegknz = f"{random.randint(1, 16):02d}"
        apositz = random.choice(["1", "2"])
        menge = random.randint(1, 500)
        noctu = random.choice(["", "1", "2"])
        autidem = random.choice(["0", "1"])
        wirkstoffvo = random.choice(["", "0", "1"])
        ambetrag = generate_amount(10, 150)
        abschlaege = generate_amount(0, 10)
        zuzahlkz = random.choice(["0", "1", "2"])
        zuzahlges = generate_amount(5, 20)
        eigenbet = generate_amount(0, 15)

        # Insert statement
        cur.execute("""
            INSERT INTO rez (
                "VSID", "PSID", "REZNR", "PZNREZ", "VODAT",
                "BSNRVOPSEUDO", "BSNRVOVB", "BSNRVOREGKNZ",
                "LENRVOPSEUDO", "LENRVOFG",
                "ABGABEDAT", "VERTRAGSKZ",
                "APOPSEUDO", "APOKLASS", "APOREGKNZ", "APOSITZ", 
                "MENGE", "NOCTU", "AUTIDEM", "WIRKSTOFFVO",
                "AMBETRAG", "ABSCHLAEGE", "ZUZAHLKZ", "ZUZAHLGES", "EIGENBET",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            );
        """, (
            vsid, psid, reznr, pznrez, vodat_int,
            bsnrvopseudo, bsnrvovb, bsnrvoregknz,
            lenrvopseudo, lenrvofg,
            abgabedat_int, vertragskz,
            apopseudo, apoklass, aporegknz, apositz,
            menge, noctu, autidem, wirkstoffvo,
            ambetrag, abschlaege, zuzahlkz, zuzahlges, eigenbet,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f" Inserted {rows} rows into 'rez'.")

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    try:
        conn = psycopg2.connect(
            dbname="CORE_MASTER_THESIS",
            user="postgres",
            password="London@123",
            host="localhost",
            port="5432",
        )
        seed_rez_table(conn, rows=500)
    except Exception as e:
        print(f" Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
