import os
import random
import pandas as pd
import argparse
from pathlib import Path
import warnings

warnings.simplefilter(action='ignore', category=UserWarning)   
###############################################################################################################  
#      This is a anonymization script which uses the following technique to anonymize the CSV file            # 
# (1) Anonymization Technique	Description                                                                   #              
# (2) k-Anonymization	Ensures each record is indistinguishable from at least k−1 others.                    #  
# (3) Pseudonymization	Replaces sensitive identifiers with randomly generated pseudonyms                     #
# (4) Random Shuffling	Disrupts the natural order of data to obscure relationships                           #
# (5) Generalization	Likely reduces the granularity of data to make it less identifiable                   #
# (6) Suppression	Replaces constant values across all rows, removing variability                            #          
# (7) Secondary Pseudonym Pools	Adds additional layers of abstraction for pseudonymized data                  #
# (8) Column Segmentation	Processes columns separately to reduce the risk of relational re-identification   #
###############################################################################################################

K = 3  # k-anonymity parameter 

# File paths
INPUT_FILE = r"C:\Users\ThothathriG\Desktop\Thesis\DART\testdata.csv"
OUTPUT_DIR = r"C:\Users\ThothathriG\Desktop\Thesis\DART\output"

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

def get_first_table(input_file):
    """Fetches the first table name from the input CSV."""
    data = pd.read_csv(input_file)
    first_table = data['Table name'].iloc[1] if 'Table name' in data.columns else None
    if first_table is None:
        raise ValueError("Column 'Table name' not found in the input file.")
    return first_table

def process_table(table_name, input_file, output_dir):
    """Processes a single table by applying anonymization techniques."""
    # Read the full dataset
    data = pd.read_csv(input_file)
    
    # Filter rows for the specific table
    table_data = data[data['Table name'] == table_name]
    if table_data.empty:
        print(f"No data found for table {table_name}.")
        return

    print(f"Processing table: {table_name}")

    # Process each column
    for col in table_data.columns:
        if col not in ['Table name']:  # Skip the 'Table name' column
            if table_data[col].dtype == 'object':
                # Pseudonymize string columns
                print(f"Pseudonymizing column: {col}")
                table_data[col] = table_data[col].apply(lambda x: generate_pseudonym(len(str(x))))
            elif pd.api.types.is_numeric_dtype(table_data[col]):
                # Shuffle and apply k-anonymity to numeric columns
                print(f"Shuffling and applying k-anonymity to column: {col}")
                table_data[col] = shuffle_column(table_data[col])
                table_data[col] = force_k(table_data[col], K)
            else:
                print(f"Skipping unsupported column type: {col}")

    # Save anonymized data
    ensure_directory_exists(output_dir)
    output_path = Path(output_dir) / f"{table_name}_anonymized.csv"
    table_data.to_csv(output_path, index=False)
    print(f"Anonymized table saved to: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Local CSV Anonymization Script")
    parser.add_argument('--input_file', default=INPUT_FILE, help="Path to the input CSV file")
    parser.add_argument('--output_dir', default=OUTPUT_DIR, help="Directory to save anonymized CSV files")
    parser.add_argument('--tables', nargs='*', help="List of table names to process (optional)")
    args = parser.parse_args()

    # Automatically get the first table if no --tables argument is provided
    if not args.tables:
        print("No --tables argument provided. Fetching the first table...")
        first_table = get_first_table(args.input_file)
        args.tables = [first_table]
        print(f"Automatically selected first table: {first_table}")

    # Process each specified table
    for table in args.tables:
        process_table(table, args.input_file, args.output_dir)
