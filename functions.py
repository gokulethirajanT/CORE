import string
import secrets
import sys
import pandas as pd
import numpy as np
import random

from helpers import get_constant_variables, get_pseudo_variables, get_column_max_length

POSSIBLE_CHARACTERS = string.ascii_uppercase + string.ascii_lowercase + string.digits
UNCHANGED_VARIABLES = get_pseudo_variables() + get_constant_variables()


def generate_secure_bytes(size: int, n_bytes=32):
    """Generate secure random byte strings using secrets."""
    return np.array([secrets.token_hex(n_bytes) for _ in range(size)])


def shuffle_column(variable: pd.Series):
    """Shuffle values securely based on random bytes."""
    random_integers = generate_secure_bytes(len(variable))
    sorted_indices = np.argsort(random_integers)
    shuffled_variable = np.array(variable)[sorted_indices]
    return pd.Series(shuffled_variable)


def assert_k_condition(k: int):
    assert k >= 2, "k must be larger or equal to 2"


def check_k_single_variable(vector: pd.Series, k: int):
    assert_k_condition(k)
    counts = vector.value_counts()
    return all(counts >= k)


def force_k(values: pd.Series, value_type: str, k: int):
    """Enforce k-anonymity by grouping rare values."""
    df = pd.DataFrame({'values': list(values)})

    if value_type in ['date', 'year', 'integer', 'float', 'month']:
        while True:
            number_counts = df['values'].value_counts(dropna=False)
            numbers_to_change = number_counts[number_counts < k].index
            if numbers_to_change.empty:
                break
            current_value = numbers_to_change[0]
            nearest = find_nearest_number(df['values'].dropna(), current_value)
            if pd.isnull(current_value):
                if nearest is not None:
                    df['values'].fillna(nearest, inplace=True)
                else:
                    df['values'] = df['values'].fillna(0)  # Or pick a safe fallback like -1 or "Unknown"
            else:
                df.loc[df['values'] == current_value, 'values'] = nearest
        return pd.Series(df['values'].to_list())

    elif value_type == 'string':
        while not check_k_single_variable(values, k):
            values = [v[:-1] if isinstance(v, str) and len(v) > 1 else v for v in values]
        return pd.Series(values)

    elif value_type in ['category', 'alphanumeric']:
        k_counts = df['values'].value_counts(dropna=False)
        under_k = k_counts[k_counts < k]
        if not under_k.empty:
            valid = k_counts[k_counts >= k].index
            if len(under_k) == 1 or under_k.sum() < k:
                smallest_valid = valid[-1] if len(valid) > 0 else "Other"
                df['values'] = df['values'].apply(lambda x: x if x in valid and x != smallest_valid else "O")
            else:
                df['values'] = df['values'].apply(lambda x: x if x not in under_k.index else "O")
        return pd.Series(df['values'].to_list())

    else:
        sys.exit(f"Unsupported data type for k-anonymity: {value_type}")


def find_nearest_number(values: pd.Series, single_value):
    """Find closest numeric value in list excluding the value itself."""
    values = [v for v in values if v != single_value]
    if not values:
        return None
    if single_value is None:
        return min(values)
    return min(values, key=lambda x: abs(x - single_value))


def generate_pseudonym(variable: str, table: str = "", length: int = None) -> str:
    """
    Generate pseudonym based on FDZ logic:
    - Fixed 19-char alphanumeric for specific variables
    - Numeric pseudonyms of same length as original column for others
    """
    variable = variable.upper()

    # FDZ-style secure pseudonyms (19-char mixed) for core IDs
    if variable in ['ARBNR', 'VSID', 'PSID', 'VERANLASSSTELLEPSEUDO']:
        return ''.join(random.choices(POSSIBLE_CHARACTERS, k=19))

    # Otherwise match length of original column
    if length is None and table:
        length = get_column_max_length(table, variable, seeder_cursor)

    length = length or 8
    return ''.join(random.choices(string.digits, k=length))
