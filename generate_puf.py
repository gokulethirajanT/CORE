import pandas as pd
import numpy as np
import random
from pathlib import Path
import os

# --- Configurable paths ---
REFERENCE_FOLDER = 'reference'
OUTPUT_FOLDER = 'Data'

# --- Load reference metadata ---
table_info = pd.read_csv(os.path.join(REFERENCE_FOLDER, 'DSB_FDZ_Gesundheit_Tabellen.csv'))
variable_info = pd.read_csv(os.path.join(REFERENCE_FOLDER, 'DSB_FDZ_Gesundheit_Variablen.csv'))

# Clean column names
table_info.columns = table_info.columns.str.strip()
variable_info.columns = variable_info.columns.str.strip()

# Filter Data Model 3 tables
data_model_3_tables = table_info[table_info['Data model'].str.strip() == 'DM3']['Table name'].tolist()

# Create output folder if not exists
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

# --- Utility Functions ---
def generate_pseudonym(length=8):
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

def generate_column_data(col_type, num_rows):
    if col_type == 'integer':
        return np.random.randint(1, 1000, num_rows)
    elif col_type == 'float':
        return np.round(np.random.uniform(0, 1000, num_rows), 2)
    elif col_type == 'string':
        return [generate_pseudonym(6) for _ in range(num_rows)]
    elif col_type == 'date':
        return pd.date_range(start='2020-01-01', periods=num_rows).strftime('%Y-%m-%d')
    else:
        return ["NA"] * num_rows

# --- Main Processing ---
print("Starting PUF synthetic data generation for Data Model 3 tables...")

for table in data_model_3_tables:
    print(f"Generating synthetic data for table: {table}")
    
    # Filter variables for this table
    columns_info = variable_info[variable_info['Table name'] == table]
    column_names = columns_info['Data field name'].tolist()
    
    num_rows = 100  # Fixed number of rows for synthetic data (can adjust)
    synthetic_data = {}

    for col in column_names:
        # Example basic mapping: more advanced logic can be added based on variable_info
        if 'ID' in col or 'PSID' in col or 'VSID' in col:
            synthetic_data[col] = [generate_pseudonym(10) for _ in range(num_rows)]
        elif 'JAHR' in col or 'Jahr' in col:
            synthetic_data[col] = np.random.choice(range(2000, 2025), num_rows)
        elif 'ICD' in col:
            synthetic_data[col] = [f"ICD-{random.randint(100,999)}" for _ in range(num_rows)]
        else:
            synthetic_data[col] = generate_column_data('string', num_rows)

    # Create DataFrame and save CSV
    df = pd.DataFrame(synthetic_data)
    output_path = os.path.join(OUTPUT_FOLDER, f"{table}.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved synthetic table to {output_path}")

print("All synthetic PUF files generated successfully.")
