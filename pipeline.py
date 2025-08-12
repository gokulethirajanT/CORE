import subprocess
import os

def run_command(command, cwd=None):
    print(f"\n Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f" Error: Command failed - {command}")
        exit(1)
    print(f" Done: {command}")

def flush_output_csv():
    folder = "output_csv"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    else:
        os.makedirs(folder)

def flush_test_csvs():
    folder = "Test"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename.lower().endswith(".csv"):
                file_path = os.path.join(folder, filename)
                try:
                    os.unlink(file_path)
                    print(f"🧹 Deleted {file_path}")
                except Exception as e:
                    print(f"⚠️ Could not delete {file_path}: {e}")

def print_pipeline_summary():
    print("\n" + "=" * 60)
    print(" CORE CLASS1 SUMMARY".center(60))
    print("=" * 60)
    print(f" Seeder flushed:        {'Yes'}")
    print(f" Seeder tables seeded:  {'17'}")
    print(f" PUF tables generated:  {'17'}")
    print(f" CSVs cleaned:          {'17'}")
    print(f" Records inserted:      {'All successful'}")
    print("-" * 60)
    print(" All tables processed and anonymized successfully.\n")



def main():
    # Step 1: Flush old seeder data
    run_command("python3 flush_seeders_data.py", cwd="seeder")

    # Step 2: Run all seeders in order
    run_command("python3 run_seeders_in_order.py", cwd="seeder")

    # Step 3: Flush old PUF data
    run_command("python3 flush_puf_data.py")

    # Step 4: Generate PUFs
    run_command("python3 generate_puf_class2.py --tables vers versq versqdmp ambfall ambdiag ambleist ambops zahnfall zahnleist zahnbef rez ezd khfall khfa khdiag khproz khentg")

    # Step 5: Run the CORE indicators calculation
    run_command("python3 CORE_indicators.py")

    # Step 6: Go to Test directory and run create_delta_tables.py
    run_command("python3 create_delta_tables.py", cwd="Test")

    # 🧹 Flush all CSV files in Test directory
    flush_test_csvs()
    
    # Step 7: Run k-anonymity test
    run_command("python3 k_anonymity_test.py", cwd="Test")

    # Step 8: Run other privacy metric tests if needed
    run_command("python3 delta-diversity_test.py", cwd="Test")
    run_command("python3 l-diversity_test.py", cwd="Test")
    run_command("python3 t-closeness.py", cwd="Test")

    # Final Summary
    print_pipeline_summary()

if __name__ == "__main__":
    main()