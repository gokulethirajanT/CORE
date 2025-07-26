import psycopg2

# List of DM3_PUF_1 tables with _puf suffix
TABLES = [
    "zahnleist_puf", "zahnbef_puf", "zahnfall_puf",
    "khentg_puf", "khproz_puf", "khfa_puf", "khdiag_puf", "khfall_puf",
    "ezd_puf", "rez_puf",
    "ambops_puf", "ambleist_puf", "ambdiag_puf", "ambfall_puf",
    "versqdmp_puf", "versq_puf", "vers_puf"
]

# Connect to the DM3_PUF_1 database
conn = psycopg2.connect(
    dbname="DM3_PUF_1",
    user="postgres",
    password="London@123",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Truncate all PUF tables and reset identity counters
cur.execute(f'TRUNCATE TABLE {", ".join(TABLES)} RESTART IDENTITY CASCADE;')
conn.commit()

cur.close()
conn.close()

print("✅ All _puf tables flushed successfully from DM3_PUF_1.")
