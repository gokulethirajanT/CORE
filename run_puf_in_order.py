"""
Run this script to anonymize all DM3 tables in dependency-respecting order.
Reads from DM3_SEEDER and pushes anonymized results into DM3_PUF_1.
"""

import subprocess
import time
import os
from dotenv import load_dotenv

# ─── Load credentials from .env ─────────────────────────────────────
load_dotenv()

SOURCE_DB = os.getenv("DB_NAME")
SOURCE_USER = os.getenv("DB_USER")
SOURCE_PASS = os.getenv("DB_PASSWORD")

TARGET_DB = os.getenv("PUF_DB_NAME")
TARGET_USER = os.getenv("PUF_DB_USER")
TARGET_PASS = os.getenv("PUF_DB_PASSWORD")

if not all([SOURCE_USER, SOURCE_PASS, TARGET_USER, TARGET_PASS]):
    raise EnvironmentError(" Missing credentials in .env file for source or target DB")

DSN = "postgres"

TABLES_IN_ORDER = [
    "vers", "versq", "versqdmp",             # Insurance core
    "ambfall", "ambdiag", "ambleist", "ambops",  # Outpatient
    "rez", "ezd",                            # Prescriptions
    "khfall", "khdiag", "khfa", "khproz", "khentg",  # Inpatient
    "zahnfall", "zahnbef", "zahnleist"       # Dental
]

# ─── Run generate_puf.py table by table ────────────────────────────
for table in TABLES_IN_ORDER:
    print(f"\n🔐 Anonymizing table: {table}")
    try:
        subprocess.run([
            "python", "generate_puf.py",
            "--dsn", DSN,
            "--source_db", SOURCE_DB,
            "--target_db", TARGET_DB,
            "--source_username", SOURCE_USER,
            "--source_password", SOURCE_PASS,
            "--target_username", TARGET_USER,
            "--target_password", TARGET_PASS,
            "--tables", table
        ], check=True)
        time.sleep(0.5)  # Delay to prevent FK race
    except subprocess.CalledProcessError as e:
        print(f"❌ Error while anonymizing {table}:")
        print(e)
        break

print("\n✅ All PUF tables processed successfully (in dependency order).")
