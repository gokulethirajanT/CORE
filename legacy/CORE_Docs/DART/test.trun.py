import os
import random
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import warnings

warnings.simplefilter(action='ignore', category=UserWarning)

K = 3  # k-anonymity parameter

# Directory for input and output files
INPUT_DIR = r"C:\Users\ThothathriG\Desktop\Thesis\DART"
OUTPUT_DIR = r"C:\Users\ThothathriG\Desktop\Thesis\DART\output"

# Function to read the first table from the CSV file
def get_first_table(csv_path):
    """Reads the first table name from the CSV file."""
    df = pd.read_csv(csv_path)
    first_table = df.iloc[0]['Table name']
    return first_table

def ensure_directory_exists(directory):
    """Ensures that the specified directory exists."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def generate_pseudonym(length):
    """Generates a random pseudonym of the specified length."""
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

def shuffle_column(column):
    """Randomly shuffles the values in a column."""
    shuffled = column.sample(frac=1, random_state=42).reset_index(drop=True)
    return shuffled

def force_k(column, k):
    """Applies k-anonymity by grouping values into bins of size k."""
    grouped = column // k * k
    return grouped

def process_table(table_name, input_dir, output_dir):
    """Processes a single table by applying anonymization techniques."""
    input_path = Path(input_dir) / f"{table_name}.csv"
    output_path = Path(output_dir) / f"{table_name}_anonymized.csv"

    if not input_path.exists():
        print(f"Input file for table {table_name} not found.")
        return

    print(f"Processing table: {table_name}")

    # Load the table
    data = pd.read_csv(input_file, dtype={'Table name': str})


    # Process each column
    for col in data.columns:
        if data[col].dtype == 'object':
            # Pseudonymize string columns
            print(f"Pseudonymizing column: {col}")
            data[col] = data[col].apply(lambda x: generate_pseudonym(len(str(x))))
        elif pd.api.types.is_numeric_dtype(data[col]):
            # Shuffle and apply k-anonymity to numeric columns
            print(f"Shuffling and applying k-anonymity to column: {col}")
            data[col] = shuffle_column(data[col])
            data[col] = force_k(data[col], K)
        else:
            print(f"Skipping unsupported column type: {col}")

    # Save anonymized data
    data.to_csv(output_path, index=False)
    print(f"Anonymized table saved to: {output_path}")

if __name__ == '__main__':
    # Get the first table name from the CSV file
    csv_file_path = os.path.join(INPUT_DIR, "testdata.csv")
    first_table = get_first_table(csv_file_path)

    parser = argparse.ArgumentParser(description="Local CSV Anonymization Script")
    parser.add_argument('--input_dir', default=INPUT_DIR, help="Directory containing input CSV files")
    parser.add_argument('--output_dir', default=OUTPUT_DIR, help="Directory to save anonymized CSV files")
    parser.add_argument('--tables', nargs='+', default=[first_table], help="List of table names to process (default: first table from CSV)")
    args = parser.parse_args()

    # Ensure input and output directories exist
    ensure_directory_exists(args.input_dir)
    ensure_directory_exists(args.output_dir)

    # Process each specified table
    for table in args.tables:
        process_table(table, args.input_dir, args.output_dir)
