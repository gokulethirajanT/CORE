import random
import psycopg2
from datetime import date, timedelta
import string

# ────────────────────── Date Generator ───────────────────────────
def random_date_in_year(year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%Y%m%d")  # Format: YYYYMMDD

# ────────────────────── Helper Pools ─────────────────────────────
def get_khklass_pool() -> list:
    return [f"{i:02d}" for i in range(10, 100)]

def get_khregkz_pool() -> list:
    return [f"{i:02d}" for i in range(10, 100)]

KHKLASS_POOL = get_khklass_pool()
KHREGKZ_POOL = [10, 20, 30, 40]

def random_aufngrund() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def generate_entlassgrund() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

def generate_aufnfa() -> str:
    digits = f"{random.randint(1, 99):02d}"
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return digits + letters

def generate_einweispseudo() -> int:
    return random.randint(10**11, 10**12 - 1)

def generate_einweisfg() -> str:
    return f"{random.randint(10, 99):02d}"

def generate_veranlasskhpseudo() -> int:
    return random.randint(10**11, 10**12 - 1)

def generate_veranlasskhklass() -> str:
    return f"{random.randint(10, 99):02d}"

def generate_veranlasskhregknz() -> str:
    return f"{random.randint(10, 99):02d}"

def generate_beatstd() -> str:
    rand = random.random()
    if rand < 0.6:
        hours = random.randint(2, 12)
    elif rand < 0.95:
        hours = random.randint(24, 96)
    else:
        hours = random.randint(97, 999)
    return f"{hours:04d}"

def generate_veranlassstellepseudo() -> str:
    length = random.randint(20, 30)
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ────────────────────── Main Seeding Routine ─────────────────────
def seed_khfall_table(conn, rows: int = 1):
    cur = conn.cursor()
    cur.execute('SELECT "VSID", "PSID", "BJAHR", "BNR" FROM "vers";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("vers table is empty; cannot seed khfall.")

    fall_records = []

    # Step 1: Get existing FALLIDKHs from database
    cur.execute('SELECT "FALLIDKH" FROM "khfall";')
    existing_fallids = set(row[0] for row in cur.fetchall())

    # Step 2: Track the current counter per year
    fallid_counters = {}  # {bjahr: max_counter_so_far}

    for _ in range(rows):
        vsid, psid, bjahr, bnr = random.choice(ref_rows)
        year_prefix = str(bjahr)

        # Initialize counter for the year based on existing IDs
        if bjahr not in fallid_counters:
            fallid_counters[bjahr] = max(
                [int(fid[4:]) for fid in existing_fallids if fid.startswith(year_prefix)],
                default=0
            )

        # Generate next available FALLIDKH
        fallid_counters[bjahr] += 1
        fallidkh = f"{year_prefix}{fallid_counters[bjahr]:08d}"
        fall_records.append((vsid, psid, fallidkh, bjahr, bnr))


        khpseudo = random.randint(10000000, 99999999)
        khklass = random.choice(KHKLASS_POOL)
        khregkz = random.choice(KHREGKZ_POOL)
        khpruef = random.choice(["J", "N", None])
        aufndat = random_date_in_year(bjahr)
        aufngrund = random_aufngrund()
        entlassgrund = generate_entlassgrund()
        aufnfa = generate_aufnfa()
        einweispseudo = generate_einweispseudo()
        einweisfg = generate_einweisfg()
        einweispruef = random.choice(["J", "N", None])
        veranlasskhpseudo = generate_veranlasskhpseudo()
        veranlasskhklass = generate_veranlasskhklass()
        veranlasskhregknz = generate_veranlasskhregknz()
        veranlasskhpruef = random.choice(["J", "N", None])
        beatstd = generate_beatstd()
        veranlassstellepseudo = generate_veranlassstellepseudo()
        datenmodell = 3

        cur.execute("""
            INSERT INTO "khfall" (
                "VSID", "PSID", "FALLIDKH",
                "KHPSEUDO", "KHKLASS", "KHREGKZ", "KHPRUEF",
                "AUFNDAT", "AUFNGRUND", "ENTLASSGRUND", "AUFNFA",
                "EINWEISPSEUDO", "EINWEISFG", "EINWEISPRUEF",
                "VERANLASSKHPSEUDO", "VERANLASSKHKLASS", "VERANLASSKHREGKNZ", "VERANLASSKHPRUEF",
                "BEATSTD", "VERANLASSSTELLEPSEUDO",
                "BJAHR", "BNR", "DATENMODELL"
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s
            );
        """, (
            vsid, psid, fallidkh,
            khpseudo, khklass, khregkz, khpruef,
            aufndat, aufngrund, entlassgrund, aufnfa,
            einweispseudo, einweisfg, einweispruef,
            veranlasskhpseudo, veranlasskhklass, veranlasskhregknz, veranlasskhpruef,
            beatstd, veranlassstellepseudo,
            bjahr, bnr, datenmodell
        ))

    conn.commit()
    print(f"Inserted {rows} rows into 'khfall'.")
    return fall_records

# ────────────────────── Entrypoint ───────────────────────────────
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="CORE_MASTER_THESIS",
        user="postgres",
        password="London@123",
        host="localhost",
        port="5432",
    )
    try:
        seed_khfall_table(conn, rows=500)
    finally:
        conn.close()
