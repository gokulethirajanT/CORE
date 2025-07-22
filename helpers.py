import psycopg2
import pandas as pd


def connect_to_database(dsn: str, username: str, password: str, dbname: str):
    """
    Establish a PostgreSQL connection to a given database.

    Parameters:
        dsn (str): Must be 'postgres'
        username (str): DB user
        password (str): DB password
        dbname (str): Target database name (e.g., DM3_SEEDER, DM3_PUF_1)

    Returns:
        tuple: (connection, cursor)
    """
    if dsn != "postgres":
        raise ValueError("This helper supports only PostgreSQL (dsn='postgres').")

    try:
        cnxn = psycopg2.connect(
            dbname=dbname,
            user=username,
            password=password,
            host="localhost",
            port="5432"
        )
        cursor = cnxn.cursor()
        return cnxn, cursor
    except Exception as e:
        print(f"❌ PostgreSQL connection failed to {dbname} as {username}: {e}")
        return None, None




def get_constant_variables(data_model=3):
    """
    Return columns with constant values in DM3.

    Returns:
        list of str
    """
    return ['BJAHR', 'DATENMODELL']


def get_secondary_pools_dm3():
    """
    Return dependent pseudo-ID fields using other pools.

    Returns:
        dict
    """
    return {
        "BSNRUEBPSEUDO": "BSNRPSEUDO",
        "LANRUEBPSEUDO": "LANRPSEUDO",
        "NBSNRPSEUDO": "BSNRPSEUDO",
        "TSVGBSNRPSEUDO": "BSNRPSEUDO",
        "BSNRVOPSEUDO": "BSNRPSEUDO",
        "EINWEISPSEUDO": "BSNRPSEUDO",
        "VERANLASSKHPSEUDO": "KHPSEUDO"
    }


def get_pseudo_variables(data_model=3):
    """
    Get list of pseudo-ID variables for DM3.

    Returns:
        list of str
    """
    df = pd.read_csv("data_types.csv")
    return df.query('Type == "pseudo" and Datamodel == 3').Variable.to_list()


def get_data_types(data_model=3):
    """
    Return variable -> data type mapping for DM3.

    Returns:
        dict
    """
    df = pd.read_csv("data_types.csv")
    dm3_df = df.query('Datamodel == 3')
    return dict(zip(dm3_df.Variable, dm3_df.Type))


def get_pseudo_mapping(data_model=3):
    """
    Map pseudo-ID variable to its original table name (DM3 only).

    Returns:
        dict
    """
    df = pd.read_csv("data_types.csv")
    subset = df.query('Type == "pseudo" and Datamodel == 3')
    return dict(zip(subset.Variable, subset.Table))


def clean_data(column_data, dt):
    """
    Clean a column based on its declared type.

    Parameters:
        column_data (pd.Series)
        dt (str): 'date', 'integer', 'category', 'year', etc.

    Returns:
        pd.Series
    """
    if dt == "category":
        column_data = column_data.astype('category')
    elif dt == "date":
        column_data = pd.to_datetime(column_data, errors='coerce', format='%Y%m%d').dt.date
        column_data = column_data.apply(lambda x: x if not pd.isnull(x) else None)
    elif dt == "year":
        column_data = pd.to_datetime(column_data, format='%Y', errors='coerce').dt.year
    elif dt == "integer":
        column_data = pd.to_numeric(column_data, errors='coerce').astype('Int64')
    return column_data
