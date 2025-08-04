import pandas as pd
import numpy as np
import random
import string

# ========== Top-/Bottom-Coding ==========
def apply_top_coding(series, threshold=90, replacement='90+'):
    return series.apply(lambda x: replacement if pd.notnull(x) and x > threshold else x)

# ========== Micro-aggregation ==========
def micro_aggregate(series, group_size=3):
    sorted_series = series.sort_values().reset_index(drop=True)
    groups = [sorted_series[i:i+group_size] for i in range(0, len(sorted_series), group_size)]
    aggregated = pd.concat([group.apply(lambda x: group.mean()) for group in groups]).sort_index()
    return aggregated.reindex(series.index)

# ========== Bucketing (Binning) ==========
def bucket_numeric(series, bins):
    bucketed = pd.cut(series, bins=bins, include_lowest=True, precision=0)
    return bucketed.astype(str).str.extract(r'\(([^,]+),\s*([^)]+)\]')[1]  # returns only upper bound

# ========== Masking & Reduction ==========
def mask_sensitive_text(series, max_len=3):
    return series.apply(lambda x: "X" * max_len if isinstance(x, str) and x.strip() != "" else x)

# ========== Noise Addition (Data Perturbation) ==========
def add_noise(series, percentage=5):
    series = pd.to_numeric(series, errors="coerce")  
    noise = np.random.uniform(-percentage, percentage, size=len(series)) / 100
    return (series * (1 + noise)).round().astype(series.dtype)

# ========== Data Swapping ==========
def swap_data(series):
    return series.sample(frac=1).reset_index(drop=True).reindex(series.index)



