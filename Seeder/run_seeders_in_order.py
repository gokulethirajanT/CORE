# This script runs all synthetic data seeder scripts (`seed_test_<table>.py`) in the correct dependency order.
# Find the attached documentation below 
import subprocess
import time

# Seeder files listed in the correct order: parent tables first
SEEDER_FILES = [
    "seed_test_vers.py",        # parent of almost all tables
    "seed_test_versq.py",       # FK → vers
    "seed_test_versqdmp.py",    # FK → versq
    "seed_test_ambfall.py",     # FK → vers
    "seed_test_ambdiag.py",     # FK → ambfall
    "seed_test_ambleist.py",    # FK → ambfall
    "seed_test_ambops.py",      # FK → ambfall
    "seed_test_rez.py",         # FK → vers
    "seed_test_ezd.py",         # FK → rez
    "seed_test_khfall.py",      # FK → vers
    "seed_test_khdiag.py",      # FK → khfall
    "seed_test_khfa.py",        # FK → khfall
    "seed_test_khproz.py",      # FK → khfall
    "seed_test_khentg.py",      # FK → khfall
    "seed_test_zahnfall.py",    # FK → vers
    "seed_test_zahnbef.py",     # FK → zahnfall
    "seed_test_zahnleist.py",   # FK → zahnfall
]

# Run each seeder script in order
for file in SEEDER_FILES:
    print(f"\n▶ Running: {file}")
    try:
        subprocess.run(["python3", file], check=True)
        time.sleep(0.5)  # Add delay to allow DB to fully flush writes
    except subprocess.CalledProcessError as e:
        print(f" Error while running {file}:")
        print(e)
        break  # Stop further execution if any seeder fails

"""
Seeder Execution Script for Data Model 3 (DM3)
──────────────────────────────────────────────

Purpose:
--------
This script runs all synthetic data seeder scripts (`seed_test_<table>.py`) in the correct 
dependency order. It ensures that parent tables (those without foreign key dependencies) 
are seeded first, followed by child tables (which depend on parent data).

Use Case:
---------
This script is designed to automate the population of a PostgreSQL database with synthetic 
data for testing, research, or development environments involving German healthcare data.

Execution Order:
----------------
- The script follows the hierarchy of foreign key relationships as defined in the DM3 schema.
- Tables like `vers`, `versq`, and `ambfall` are seeded first.
- Dependent tables such as `ambdiag`, `khfall`, `zahnfall`, etc., are seeded afterward.

Usage:
------
Run the script from the command line:

    python3 run_seeders_in_order.py

Requirements:
-------------
- All `seed_test_<table>.py` files must exist in the same directory.
- Each script must be executable independently (with `if __name__ == "__main__":` block).
- Python 3 must be installed.
- The `psycopg2` and `mimesis` libraries must be available.

Behavior:
---------
- Each file is executed using `subprocess.run()` with `check=True`, which ensures that 
  execution stops if any seeder script fails.
- Standard output and errors are displayed in the terminal to assist in debugging.

Extension:
----------
You may modify the `SEEDER_FILES` list to add/remove scripts or implement dynamic scanning
for *.py files based on filename patterns.

Author:
-------
This script was generated for the CORE_MASTER_THESIS PostgreSQL setup.

"""
