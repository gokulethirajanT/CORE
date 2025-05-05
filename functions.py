import string
import secrets
import sys

import pandas as pd
import numpy as np
import random

from helpers import get_constant_variables, get_pseudo_variables

POSSIBLE_CHARACTERS = string.digits  # DM3 IDs are typically numeric
UNCHANGED_VARIABLES = get_pseudo_variables() + get_constant_variables()


def generate_secure_bytes(size: int, n_bytes=32):
    """Generate secure byte strings using secrets.token_hex.
    This uses the most secure source of randomness that your operating system provides.

    Parameters:
        size: Length of array to be returned.
        n_bytes: Number of bytes to generate a random byte string.
    Returns:
        numpy.ndarray: Array of secure random bytes.
    """
    return np.array([secrets.token_hex(n_bytes) for _ in range(size)])


def shuffle_column(variable: pd.Series):
    """Shuffle values based on secure random bytes.

    Parameters:
        variable (array-like): Input vector of any length.

    Returns:
        pandas.Series: The same vector, randomly ordered.
    """
    random_integers = generate_secure_bytes(len(variable))
    sorted_indices = np.argsort(random_integers)
    shuffled_variable = np.array(variable)[sorted_indices]
    return pd.Series(shuffled_variable)


def assert_k_condition(k: int):
    assert k >= 2, "k must be larger or equal to 2"


def check_k_single_variable(vector: pd.Series, k: int):
    assert_k_condition(k)
    counts = vector.value_counts()
    k_check = all(i >= k for i in counts)
    return k_check


def force_k(values: pd.Series, value_type: str, k: int):
    """Apply k-anonymity by merging or generalizing low-frequency values.

    Parameters:
        values (array-like): Input vector
        value_type (str): Type defined in `data_types.csv`
        k (int): Minimum count for anonymity

    Returns:
        pandas.Series: K-anonymized column
    """
    df = pd.DataFrame({'values': list(values)})

    if value_type in ['date', 'year', 'integer']:
        while True:
            number_counts = df['values'].value_counts(dropna=False)
            to_replace = number_counts[number_counts < k].index
            if to_replace.empty:
                break
            current = df[df['values'].isin(to_replace)].iloc[0, 0]
            nearest = find_nearest_number(df['values'].dropna(), current)
            if pd.isnull(current):
                df['values'] = df['values'].fillna(nearest)
            else:
                df.loc[df['values'] == current, 'values'] = nearest
        return pd.Series(df['values'])

    elif value_type in ['category', 'alphanumeric']:
        k_not_fulfilled = df['values'].value_counts(dropna=False).loc[lambda x: x < k]
        if not k_not_fulfilled.empty:
            k_fulfilled = df['values'].value_counts(dropna=False).loc[lambda x: x >= k]
            if len(k_not_fulfilled) == 1 or k > sum(k_not_fulfilled):
                smallest_valid = k_fulfilled.index.tolist()[-1]
                df['Other'] = df['values'].apply(
                    lambda x: x if x in k_fulfilled and x is not smallest_valid else 'Other')
            else:
                df['Other'] = df['values'].apply(
                    lambda x: x if x not in k_not_fulfilled else 'Other')
            return pd.Series(df['Other'].to_list())
        else:
            return pd.Series(df['values'].to_list())

    else:
        sys.exit(f"Data type {value_type} is not supported for DM3.")


def find_nearest_number(values: pd.Series, single_value):
    """Find the closest number to `single_value` in `values`."""
    values = [val for val in values if val != single_value]
    if not values:
        return None
    if single_value is None or pd.isnull(single_value):
        return min(values)
    return min(values, key=lambda x: abs(x - single_value))


def generate_pseudonym(variable: str, length=19):
    """
    Generate a pseudonym for DM3 variables.

    Parameters:
        variable (str): Variable name (e.g., 'BSNRPSEUDO')
        length (int): Length of generated pseudonym

    Returns:
        str: Random numeric pseudonym
    """
    return ''.join(random.choices(POSSIBLE_CHARACTERS, k=length))
