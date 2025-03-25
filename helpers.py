import pandas as pd

# Set constant variables manually for DM3
def get_constant_variables_local():
    return ['BJAHR', 'DATENMODELL']

# Load pseudo variables from data_types.csv
def get_pseudo_variables_local(data_model=3):
    df = pd.read_csv("reference/data_types.csv")
    pseudos = df.query('Type == "pseudo" and Datamodel == @data_model')['Variable'].tolist()
    return pseudos

# Load data types from data_types.csv
def get_data_types_local(data_model=3):
    df = pd.read_csv("reference/data_types.csv")
    filtered = df.query('Datamodel == @data_model')
    return dict(zip(filtered['Variable'], filtered['Type']))

# Map pseudo variable names to table names
def get_pseudo_mapping_local(data_model=3):
    df = pd.read_csv("reference/data_types.csv")
    mapping_df = df.query('Type == "pseudo" and Datamodel == @data_model')
    return dict(zip(mapping_df['Variable'], mapping_df['Table']))

# Clean values based on their expected type
def clean_data_local(series, dtype):
    if dtype == "category":
        return series.astype("category")
    elif dtype == "date":
        return pd.to_datetime(series, errors='coerce').dt.date
    elif dtype == "year":
        return pd.to_datetime(series, errors='coerce').dt.year
    elif dtype == "integer":
        return pd.to_numeric(series, errors='coerce').astype('Int64')
    elif dtype == "float":
        return pd.to_numeric(series, errors='coerce').astype(float)
    else:
        return series.fillna("NA")