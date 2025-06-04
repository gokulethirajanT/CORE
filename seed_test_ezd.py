#!/usr/bin/env python3
"""
Seed DM-8 table EZD with realistic prescription data.

• REZNR unique per (BJAHR, fund) and always tied to exactly one VSID
• PZNEZD = numeric 8-digit PZN (Mod-11 checksum)
• FAKTOR ranges depend on FAKTORKENNZEICHEN
"""

import random
import psycopg2
from datetime import date

# ───────────────── PZN helpers ──────────────────────────────────────────────
_PZN_W = [3, 1, 9, 7, 3, 1]                         # weights

def pzn_checksum(body: str) -> str:
    s = sum(int(d) * w for d, w in zip(reversed(body), _PZN_W))
    return str((10 - (s % 10)) % 10)

def random_pzn() -> str:
    body = f"{random.randint(100000, 999999)}"       # 6-digit body
    return body + pzn_checksum(body) + str(random.randint(0, 9))

# ───────────────── factor helpers ───────────────────────────────────────────
EINHEIT_POOL     = ["mg", "ml", "St", "g", "mc"]        # Health_Lab description not available
FAKTOR_KENN_POOL = ["N1", "N2", "N3", "P", "F"]

def random_faktor(fkenn: str) -> int:
    if fkenn in ("N1", "N2", "N3", "F", "P"):
        return random.randint(1, 4)          # packs / split packs
    if fkenn in ("mg", "g"):
        return random.randint(100, 800)      # mg or g
    if fkenn == "ml":
        return random.randint(5, 250)        # ml
    return 1

# ───────────────── REZNR helpers (Mod-97) ───────────────────────────────────
def mod97(body: str) -> str:
    return f"{98 - (int(body) * 100) % 97:02d}"

def generate_reznr() -> int:
    body = f"{random.randint(10_000_000, 99_999_999)}"   # 8-digit body
    return int(body + mod97(body))                       # 10-digit Rx number

# ───────────────── main routine ─────────────────────────────────────────────
def seed_ezd_table(conn, row_count: int = 1000):
    cur = conn.cursor()

    cur.execute('SELECT "VSID","PSID","BJAHR","BNR" FROM "vers";')
    vers_rows = cur.fetchall()
    if not vers_rows:
        raise ValueError("No rows in table 'vers'.")

    reznr_pool: dict[int, list[tuple[int, int]]] = {}    # year → [(REZNR, VSID)]

    for _ in range(row_count):
        vsid, psid, bjahr, bnr = random.choice(vers_rows)

        # reuse logic
        reuse = random.random() < 0.40 and bjahr in reznr_pool
        if reuse:
            cand = [r for r, v in reznr_pool[bjahr] if v == vsid]
            if cand:
                reznr = random.choice(cand)
            else:
                reuse = False
        if not reuse:
            while True:
                reznr = generate_reznr()
                if all(r != reznr for r, _ in reznr_pool.get(bjahr, [])):
                    break
            reznr_pool.setdefault(bjahr, []).append((reznr, vsid))

        # synthetic cols
        pzn     = random_pzn()
        fkenn   = random.choice(FAKTOR_KENN_POOL)
        faktor  = random_faktor(fkenn)
        zaehler = None if random.random() < 0.9 else 1
        einheit = random.choice(EINHEIT_POOL)
        datenmodell = 3

        params = (
            vsid, psid, reznr,          # 1-3
            pzn,  zaehler, einheit,     # 4-6
            faktor, fkenn,              # 7-8
            bjahr, bnr,                 # 9-10
            datenmodell                 # 11
        )
        assert len(params) == 11, "parameter tuple must have 11 items"

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
    print(f"Inserted {row_count} rows into 'ezd'")

# ───────────────── run script ───────────────────────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname   = "CORE_MASTER_THESIS",
        user     = "postgres",
        password = "London@123",
        host     = "localhost",
        port     = "5432"
    )
    try:
        seed_ezd_table(conn, row_count=1000)
    finally:
        conn.close()
