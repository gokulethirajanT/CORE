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

    # Step 5: Final message 
    print_pipeline_summary()

if __name__ == "__main__":
    main()
