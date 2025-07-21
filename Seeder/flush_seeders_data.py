import psycopg2

TABLES = [
    "zahnleist", "zahnbef", "zahnfall",
    "khentg", "khproz", "khfa", "khdiag", "khfall",
    "ezd", "rez",
    "ambops", "ambleist", "ambdiag", "ambfall",
    "versqdmp", "versq", "vers"
]

conn = psycopg2.connect(
    dbname="DM3_SEEDER",
    user="postgres",
    password="London@123",
    host="localhost",
    port="5432"
)

cur = conn.cursor()
cur.execute(f'TRUNCATE TABLE {", ".join(TABLES)} RESTART IDENTITY CASCADE;')
conn.commit()
cur.close()
conn.close()

print("✅ All data flushed successfully.")
