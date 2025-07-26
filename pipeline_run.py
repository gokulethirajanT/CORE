import subprocess
import os

def run_command(command, cwd=None):
    print(f"\n🚀 Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Error: Command failed - {command}")
        exit(1)
    print(f"✅ Done: {command}")

def main():
    # Step 1: Flush old seeder data
    run_command("python3 flush_seeders_data.py", cwd="seeder")

    # Step 2: Run all seeders in order
    run_command("python3 run_seeders_in_order.py", cwd="seeder")

    # Step 3: Flush old PUF data
    run_command("python3 flush_puf_data.py")

    # Step 4: Generate PUFs
    run_command("python3 generate_puf.py --tables vers versq versqdmp")

    print("\n✅ Pipeline finished successfully.")

if __name__ == "__main__":
    main()
