import pandas as pd
import numpy as np
import random
import string
from helpers import get_constant_variables, get_pseudo_variables

POSSIBLE_CHARACTERS = string.ascii_uppercase + string.ascii_lowercase + string.digits
UNCHANGED_VARIABLES = get_pseudo_variables() + get_constant_variables()

def generate_pseudonym(length=19):
    return ''.join(random.choices(POSSIBLE_CHARACTERS, k=length))

def shuffle_column(series: pd.Series) -> pd.Series:
    shuffled = series.sample(frac=1).reset_index(drop=True)
    return shuffled

def check_k_single_variable(series: pd.Series, k: int) -> bool:
    return all(series.value_counts().ge(k))

def find_nearest_number(values: pd.Series, val):
    return min(values.dropna().unique(), key=lambda x: abs(x - val))

def force_k(values: pd.Series, value_type: str, k: int) -> pd.Series:
    df = pd.DataFrame({'values': list(values)})

    if value_type in ["date", "year", "integer", "float", "month"]:
        max_iter = 100
        count = 0
        while True:
            count += 1
            if count > max_iter:
                print("⚠️ force_k() stopped after max iterations. Some values may still be < k.")
                break

            counts = df["values"].value_counts(dropna=False)
            low_counts = counts[counts < k].index
            if len(low_counts) == 0:
                break

            to_replace_idx = df["values"].isin(low_counts)
            remaining_values = df["values"][~to_replace_idx].dropna().unique()

            if len(remaining_values) == 0:
                fallback = df["values"].dropna().mode()
                replacement = fallback.iloc[0] if not fallback.empty else 0
            else:
                replacement = find_nearest_number(pd.Series(remaining_values), df["values"][to_replace_idx].iloc[0])

            df.loc[to_replace_idx, "values"] = replacement

        return pd.Series(df["values"].to_list())

    elif value_type == "string":
        while not check_k_single_variable(values, k):
            values = [v[:-1] if isinstance(v, str) else v for v in values]
        return pd.Series(values)

    elif value_type == "category":
        vc = df["values"].value_counts(dropna=False)
        valid = vc[vc >= k].index
        df["values"] = df["values"].apply(lambda x: x if x in valid else "Other")
        return pd.Series(df["values"].to_list())

    else:
        raise ValueError(f"Unsupported type: {value_type}")



