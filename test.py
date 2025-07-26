from helpers import connect_to_database

conn, cur = connect_to_database(puf=True)
cur.execute("SELECT COUNT(*) FROM vers_puf")
print("Rows in PUF vers table:", cur.fetchone())
conn.close()