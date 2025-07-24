#!/usr/bin/env python3
"""
Seed DM-8 table EZD with realistic prescription data.
"""
import random
import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()
# ─────────────── PZN checksum ────────────────
_PZN_W = [3, 1, 9, 7, 3, 1]

def pzn_checksum(body: str) -> str:
    s = sum(int(d) * w for d, w in zip(reversed(body), _PZN_W))
    return str((10 - (s % 10)) % 10)

def random_pzn_hiv() -> str: # [70] Sax et al. (2012) 
    prefix = str(random.choice([3, 7])) + f"{random.randint(10000, 99999)}"  # simulate HIV med block
    body = prefix[:6]
    return body + pzn_checksum(body) + str(random.randint(0, 9))  # final digit is random

# ─────────────── Helpers ────────────────
EINHEIT_POOL_HIV = ["St"] * 60 + ["mg"] * 30 + ["ml"] * 5 + ["g"] * 3 + ["mc"] * 2 # [74] Clay et al. (2015)

FAKTOR_KENN_POOL_HIV = ["N3"] * 40 + ["N2"] * 25 + ["N1"] * 20 + ["P"] * 10 + ["F"] * 5 # [71] Cotte et al. (2023)


def random_faktor_hiv(fkenn: str) -> int:
    if fkenn in ("N1", "N2", "N3", "F", "P"):
        return random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
    if fkenn in ("mg", "g"):
        return random.randint(100, 400)  # lower dose ranges for tablets
    if fkenn == "ml":
        return random.randint(1, 30)     # injectable volumes
    return 1


# ─────────────── Seeding Function ────────────────
def seed_ezd_table(conn, rows: int = 100):
    cur = conn.cursor()

    cur.execute('SELECT "REZNR", "VSID", "PSID", "BJAHR", "BNR" FROM "rez";')
    rez_rows = cur.fetchall()
    if not rez_rows:
        raise ValueError("No rows in 'rez'. Cannot seed 'ezd'.")

    for _ in range(rows):
        reznr, vsid, psid, bjahr, bnr = random.choice(rez_rows)

        pzn     = random_pzn_hiv() # [70] Sax et al. (2012)
        fkenn = random.choice(FAKTOR_KENN_POOL_HIV) # [72] Mantsios et al. (2020)
        faktor  = random_faktor_hiv(fkenn) # [71] Cotte et al. (2023)
        zaehler = None if random.random() < 0.95 else random.choice([1, 2]) # [73] Gandhi et al. (2018)
        einheit = random.choice(EINHEIT_POOL_HIV) # [74] Clay et al. (2015)
        datenmodell = 3 # [9] Forschungsdatenzentrum Gesundheit. (2023). Datenmodell 3: Datenstruktur und Variablenbeschreibung. BfArM. https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/ # FDZ Data Model 3 — see [19] BMG (2021)

        params = (
            vsid, psid, reznr, pzn, zaehler, einheit,
            faktor, fkenn, bjahr, bnr, datenmodell
        )

        cur.execute(
            """
            INSERT INTO "ezd" (
              "VSID","PSID","REZNR",
              "PZNEZD","ZAEHLER","EINHEIT",
              "FAKTOR","FAKTORKENNZEICHEN",
              "BJAHR","BNR","DATENMODELL"
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """,
            params
        )

    conn.commit()
    print(f"Inserted {rows}  rows into 'ezd'.")

# ─────────────── Entrypoint ────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    seed_ezd_table(conn)
    conn.close()
