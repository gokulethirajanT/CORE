import string
import secrets
import sys

import pandas as pd
import numpy as np
import random
import psycopg2
import os

from helpers import get_constant_variables, get_pseudo_variables

POSSIBLE_CHARACTERS = string.digits  # DM3 IDs are typically numeric
UNCHANGED_VARIABLES = get_pseudo_variables() + get_constant_variables()

def generate_secure_bytes(size: int, n_bytes=32):
    return np.array([secrets.token_hex(n_bytes) for _ in range(size)])

def shuffle_column(variable: pd.Series):
    random_integers = generate_secure_bytes(len(variable))
    sorted_indices = np.argsort(random_integers)
    shuffled_variable = np.array(variable)[sorted_indices]
    return pd.Series(shuffled_variable)

def assert_k_condition(k: int):
    assert k >= 2, "k must be larger or equal to 2"

def check_k_single_variable(vector: pd.Series, k: int):
    assert_k_condition(k)
    counts = vector.value_counts()
    return all(i >= k for i in counts)

def force_k(values: pd.Series, value_type: str, k: int):
    df = pd.DataFrame({'values': list(values)})

    if value_type in ['date', 'year', 'integer']:
        while True:
            number_counts = df['values'].value_counts(dropna=False)
            to_replace = number_counts[number_counts < k].index
            if to_replace.empty:
                break
            current = df[df['values'].isin(to_replace)].iloc[0, 0]
            nearest = find_nearest_number(df['values'].dropna(), current)

            # Only try to fill or replace if we have a valid nearest
            if nearest is None:
                break  # Cannot proceed, would cause fillna error
            if pd.isnull(current):
                df['values'] = df['values'].fillna(nearest)
            else:
                df.loc[df['values'] == current, 'values'] = nearest

        return pd.Series(df['values'])

    elif value_type in ['category', 'alphanumeric']:
        k_not_fulfilled = df['values'].value_counts(dropna=False).loc[lambda x: x < k]
        if not k_not_fulfilled.empty:
            k_fulfilled = df['values'].value_counts(dropna=False).loc[lambda x: x >= k]
            fallback = 'Other'  # only valid for categorical fields
            if len(k_not_fulfilled) == 1 or k > sum(k_not_fulfilled):
                smallest_valid = k_fulfilled.index.tolist()[-1]
                df['values'] = df['values'].apply(
                    lambda x: x if x in k_fulfilled and x is not smallest_valid else fallback)
            else:
                df['values'] = df['values'].apply(
                    lambda x: x if x not in k_not_fulfilled else fallback)
        return pd.Series(df['values'])

    else:
        sys.exit(f"Data type {value_type} is not supported for DM3.")



def find_nearest_number(values: pd.Series, single_value):
    values = [val for val in values if val != single_value]
    if not values:
        return None
    if single_value is None or pd.isnull(single_value):
        return min(values)
    return min(values, key=lambda x: abs(x - single_value))

_psid_map = {}
def generate_pseudonym(variable: str, table: str = None, conn=None, original_value=None) -> str:
    default_length = 12
    max_length = default_length

    if conn and table:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT character_maximum_length 
                    FROM information_schema.columns 
                    WHERE LOWER(table_name) = LOWER(%s) AND LOWER(column_name) = LOWER(%s)
                """, (table, variable))
                result = cursor.fetchone()
                if result and result[0]:
                    max_length = int(result[0])
        except Exception as e:
            print(f"⚠️ Could not detect max length for {table}.{variable}: {e}")

    # Ensure consistency for PSID
    if variable.upper() == "PSID" and original_value is not None:
        if original_value not in _psid_map:
            _psid_map[original_value] = ''.join(random.choices(POSSIBLE_CHARACTERS, k=max_length))
        return _psid_map[original_value]
    # Fallback for all other pseudonyms
    return ''.join(random.choices(POSSIBLE_CHARACTERS, k=max_length))
    



