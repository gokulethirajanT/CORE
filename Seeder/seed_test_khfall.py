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
    """Returns a broader range of realistic KHKLASS values (2-digit codes)."""
    return [f"{i:02d}" for i in range(10, 100)]  # e.g., '10' to '99'
def get_khregkz_pool() -> list:
    """Returns a broader range of realistic KHKLASS values (2-digit codes)."""
    return [f"{i:02d}" for i in range(10, 100)]  # e.g., '10' to '99'


# Call the function to create the pool
KHKLASS_POOL = get_khklass_pool()
KHREGKZ_POOL = get_khregkz_pool()

KHREGKZ_POOL = [10, 20, 30, 40]

def random_aufngrund() -> str:
    """Generate a realistic 4-character alphanumeric AUFNGRUND code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

AUFNGRUND_POOL = random_aufngrund() 
def generate_entlassgrund() -> str:
    """Generates a synthetic 3-character alphanumeric ENTGLASSGRUND code as defined by Schlüssel 5."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

def generate_aufnfa() -> str:
    """
    Generates a synthetic 4-character alphanumeric AUFNFA code,
    matching the format defined in Schlüssel 6 (e.g., '01AB', '12CD').
    """
    digits = f"{random.randint(1, 99):02d}"                      # 2-digit numeric prefix: '01' to '99'
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))  # 2 uppercase letters
    return digits + letters  # e.g., '01AB'

def generate_einweispseudo() -> int:
    """Generates a 12-digit numeric pseudonym for the referring physician (EINWEISPSEUDO)."""
    return random.randint(10**11, 10**12 - 1)  # ensures 12-digit number


def generate_einweisfg() -> str:
    """Generate a 2-digit numeric code representing the medical specialty of the referring physician."""
    return f"{random.randint(10, 99):02d}"  # Format: '10' to '99'

def generate_veranlasskhpseudo() -> int:
    """Generates a 12-digit numeric pseudonym for the referring hospital (VERANLASSKHPSEUDO)."""
    return random.randint(10**11, 10**12 - 1)

def generate_veranlasskhklass() -> str:
    """Generates a 2-digit numeric code for the classification of the referring hospital."""
    return f"{random.randint(10, 99):02d}"

def generate_veranlasskhregknz() -> str:
    """Generates a 2-digit numeric regional code (e.g., Bundesland code)."""
    return f"{random.randint(10, 99):02d}"  # '10' to '99' placeholder range

def generate_beatstd() -> str:
    """
    Generates a realistic 4-digit string for ventilation hours.
    Most values range between 2 and 96 hours, with rare cases up to 999.
    """

def generate_veranlassstellepseudo() -> str:
    """
    Generates a realistic alphanumeric pseudonym (up to 30 characters)
    for the referring entity (e.g., hospital, emergency service).
    """
    length = random.randint(20, 30)  # Keep variability between 20 and 30 characters
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # Weighted distribution: short-term (2–12), moderate (24–96), rare long (97–999)
    rand = random.random()
    if rand < 0.6:
        hours = random.randint(2, 12)         # short ventilation
    elif rand < 0.95:
        hours = random.randint(24, 96)        # ICU-like ventilation
    else:
        hours = random.randint(97, 999)       # rare long-term cases
    return f"{hours:04d}"


# ────────────────────── Main Seeding Routine ─────────────────────
def seed_khfall_table(conn, rows: int = 500):
    cur = conn.cursor()

    cur.execute('SELECT "VSID", "PSID", "FALLIDKH", "BJAHR", "BNR" FROM "khdiag";')
    ref_rows = cur.fetchall()
    if not ref_rows:
        raise ValueError("khdiag table is empty; cannot seed khfall.")

    for _ in range(rows):
        vsid, psid, fallidkh, bjahr, bnr = random.choice(ref_rows)

        khpseudo = random.randint(10000000, 99999999)  # 8-digit pseudonym
        khklass = random.choice(KHKLASS_POOL)
        khregkz = random.choice(KHREGKZ_POOL)
        khpruef = random.choice(["J", "N", None])
        aufndat = random_date_in_year(bjahr)
        aufngrund = random.choice(AUFNGRUND_POOL)
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
    print(f" Inserted {rows} rows into 'khfall'.")

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