import pandas as pd
import numpy as np
import hashlib

# ========== Class 3: Homomorphic Encryption (Simulated) ==========
def homomorphic_encrypt(series, secret_key='FDZ2025'):
    def encrypt(value):
        if pd.isnull(value):
            return value
        raw = f"{secret_key}-{str(value)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]  # Simulate ciphertext
    return series.apply(encrypt)

# ========== Class 3: Differential Privacy (Laplace Mechanism) ==========
def apply_differential_privacy(series, epsilon=0.5, sensitivity=1):
    # Convert nullable pandas Int64 to float64 explicitly
    if pd.api.types.is_integer_dtype(series.dtype):
        series = series.astype("float64")
    else:
        series = pd.to_numeric(series, errors='coerce')

    # Add Laplace noise
    noise = np.random.laplace(loc=0.0, scale=sensitivity/epsilon, size=series.shape[0])
    return (series + noise).round().astype(series.dtype)

