#!/usr/bin/env python3
"""
Seed DM-8 table EZD with realistic prescription data.
"""
import random
import psycopg2

# ─────────────── PZN checksum ────────────────
_PZN_W = [3, 1, 9, 7, 3, 1]

def pzn_checksum(body: str) -> str:
    s = sum(int(d) * w for d, w in zip(reversed(body), _PZN_W))
    return str((10 - (s % 10)) % 10)

def random_pzn() -> str:
    body = f"{random.randint(100000, 999999)}"
    return body + pzn_checksum(body) + str(random.randint(0, 9))

# ─────────────── Helpers ────────────────
EINHEIT_POOL     = ["mg", "ml", "St", "g", "mc"]
FAKTOR_KENN_POOL = ["N1", "N2", "N3", "P", "F"]

def random_faktor(fkenn: str) -> int:
    if fkenn in ("N1", "N2", "N3", "F", "P"):
        return random.randint(1, 4)
    if fkenn in ("mg", "g"):
        return random.randint(100, 800)
    if fkenn == "ml":
        return random.randint(5, 250)
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

        pzn     = random_pzn()
        fkenn   = random.choice(FAKTOR_KENN_POOL)
        faktor  = random_faktor(fkenn)
        zaehler = None if random.random() < 0.9 else 1
        einheit = random.choice(EINHEIT_POOL)
        datenmodell = 3

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
    print(f"Inserted {rows} synthetic rows into 'ezd'.")

# ─────────────── Entrypoint ────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname   = "CORE_MASTER_THESIS",
        user     = "postgres",
        password = "London@123",
        host     = "localhost",
        port     = "5432"
    )
    try:
        seed_ezd_table(conn, rows=1)  # ← this is where row count is defined
    finally:
        conn.close()
