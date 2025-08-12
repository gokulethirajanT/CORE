# t_closeness.py
import os
import math
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- plotting (headless) ---
import matplotlib
matplotlib.use("Agg")  # server/CI-safe
import matplotlib.pyplot as plt

load_dotenv()

# -------- Config --------
TABLE = os.getenv("L_TABLE", "vers_puf")
SENSITIVE_COL = os.getenv("SENSITIVE_COL", "ICD10")
T_THRESHOLD = float(os.getenv("T_THRESHOLD", 0.2))  # max allowed distance
EXPORT_VIOLATIONS = os.getenv("EXPORT_VIOLATIONS", "1") == "1"

def build_pg_url(prefix: str):
    user = os.getenv(f"{prefix}_DB_USER") or os.getenv("DB_USER")
    pwd  = os.getenv(f"{prefix}_DB_PASSWORD") or os.getenv("DB_PASSWORD")
    host = os.getenv(f"{prefix}_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv(f"{prefix}_DB_PORT") or os.getenv("DB_PORT", "5432")
    name = os.getenv(f"{prefix}_DB_NAME") or os.getenv("DB_NAME")
    if not (user and pwd and host and port and name):
        raise RuntimeError("Missing DB env vars")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"

DATABASE_URL = os.getenv("DATABASE_URL") or build_pg_url("PUF")
engine = create_engine(DATABASE_URL)

# -------- Helpers --------
def object_exists(tbl: str) -> bool:
    sql = text("""
        SELECT COUNT(*) 
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :tbl
    """)
    with engine.connect() as conn:
        return conn.execute(sql, {"tbl": tbl}).scalar() > 0

def get_columns(tbl: str):
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :tbl
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(sql, {"tbl": tbl}).all()]

def build_qi_list(cols_upper):
    """Accept raw or precomputed QIs."""
    qis = []
    if "PLZ" in cols_upper:
        qis.append('LEFT("PLZ",3) AS PLZ3')
    elif "PLZ3" in cols_upper:
        qis.append('"PLZ3"')

    if "GEBJAHR" in cols_upper:
        qis.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS GEBJAHR_BAND')
    elif "GEBJAHR_BAND" in cols_upper:
        qis.append('"GEBJAHR_BAND"')

    if "GESCHLECHT" in cols_upper:
        qis.append('"GESCHLECHT"')
    return qis

def normalize_group_cols(qis):
    return [(q.split(" AS ")[-1] if " AS " in q else q).replace('"', '') for q in qis]

def fetch_dataframe(select_qis, sens_col, table):
    sql = text(f"""
        SELECT {select_qis}, "{sens_col}" AS sens
        FROM {table}
        WHERE "{sens_col}" IS NOT NULL
    """)
    return pd.read_sql_query(sql, engine)

def is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_integer_dtype(series) or pd.api.types.is_float_dtype(series)

def tvd_categorical(p: pd.Series, q: pd.Series) -> float:
    # p, q are value->prob mappings as Series indexed by category
    idx = p.index.union(q.index)
    p = p.reindex(idx, fill_value=0.0)
    q = q.reindex(idx, fill_value=0.0)
    return 0.5 * np.abs(p - q).sum()

def tvd_numeric(sample: pd.Series, ref: pd.Series, bins: int = 20) -> float:
    # Histogram-based TVD over numeric domain
    s = pd.to_numeric(sample, errors="coerce").dropna()
    r = pd.to_numeric(ref, errors="coerce").dropna()
    if s.empty or r.empty:
        return 1.0
    lo = min(s.min(), r.min())
    hi = max(s.max(), r.max())
    if lo == hi:
        return 0.0
    hist_s, edges = np.histogram(s, bins=bins, range=(lo, hi), density=False)
    hist_r, _     = np.histogram(r, bins=bins, range=(lo, hi), density=False)
    ps = hist_s / hist_s.sum() if hist_s.sum() > 0 else np.zeros_like(hist_s, dtype=float)
    pr = hist_r / hist_r.sum() if hist_r.sum() > 0 else np.zeros_like(hist_r, dtype=float)
    return 0.5 * np.abs(ps - pr).sum()

# ---------- Plots ----------
def plot_tvd_distribution(df: pd.DataFrame, threshold: float, out_path: str = "t_closeness_distribution.png"):
    """Histogram of group TVD with a vertical line at threshold."""
    plt.figure(figsize=(8, 5))
    plt.hist(df["tvd"], bins=30, edgecolor="black")
    plt.axvline(threshold, linestyle="--", linewidth=2, label=f"T_THRESHOLD = {threshold}")
    plt.title("DM3 CORE Class 2 — T‑closeness (TVD) Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("Total Variation Distance (per group)")
    plt.ylabel("Number of Groups")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_tvd_cumulative(df: pd.DataFrame, out_path: str = "t_closeness_cumulative.png"):
    """
    Cumulative coverage curve:
    x = TVD threshold, y = % of groups with TVD ≤ x.
    Helpful to show how many groups meet a given closeness bound.
    """
    xs = np.linspace(0, max(1.0, df["tvd"].max()), 200)
    ys = [(df["tvd"] <= x).mean() * 100.0 for x in xs]

    plt.figure(figsize=(8, 5))
    plt.plot(xs, ys, marker=None)
    plt.title("DM3 Class 2: Cumulative Coverage by TVD bound")
    plt.xlabel("TVD bound (x)")
    plt.ylabel("Groups with TVD ≤ x (%)")
    plt.grid(True, linewidth=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_top_violations(bad_df: pd.DataFrame, group_cols: list[str], out_path: str = "t_closeness_top_violations.png", top_n: int = 20):
    """Bar chart of the top-N violating groups by TVD."""
    if bad_df.empty:
        return None
    # Build a compact group label
    def mk_label(row):
        parts = []
        for c in group_cols:
            parts.append(f"{c}={row[c]}")
        return " | ".join(parts)

    tmp = bad_df.copy()
    tmp["group"] = tmp.apply(mk_label, axis=1)
    tmp = tmp.sort_values("tvd", ascending=False).head(top_n)

    plt.figure(figsize=(10, max(4, 0.4 * len(tmp))))
    plt.barh(tmp["group"], tmp["tvd"], edgecolor="black")
    plt.gca().invert_yaxis()
    plt.xlabel("TVD")
    plt.title(f"Top {len(tmp)} T‑closeness Violations (higher is worse)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

# -------- Main --------
def check_t_closeness():
    if not object_exists(TABLE):
        return {"status": "FAIL", "reason": f"Missing table/view {TABLE}"}

    cols_raw = get_columns(TABLE)
    cols_upper = [c.upper() for c in cols_raw]

    if SENSITIVE_COL.upper() not in cols_upper:
        return {"status": "FAIL", "reason": f"Sensitive column '{SENSITIVE_COL}' not found in {TABLE}"}

    qis = build_qi_list(cols_upper)
    if not qis:
        return {"status": "FAIL", "reason": "No quasi-identifiers available (PLZ/PLZ3, GEBJAHR/GEBJAHR_BAND, or GESCHLECHT)."}

    select_qis = ", ".join(qis)
    group_cols = normalize_group_cols(qis)

    df = fetch_dataframe(select_qis, SENSITIVE_COL, TABLE)
    if df.empty:
        return {"status": "FAIL", "reason": f"No rows with non-null {SENSITIVE_COL} in {TABLE}"}

    sens = df["sens"]
    numeric_sens = is_numeric(sens)

    # Global reference distribution
    if numeric_sens:
        ref_series = sens.copy()
    else:
        ref_dist = sens.value_counts(dropna=False)
        ref_prob = ref_dist / ref_dist.sum()

    # Compute per-group distances
    grp = df.groupby(group_cols, dropna=False)
    rows = []
    for keys, sub in grp:
        key_tuple = keys if isinstance(keys, tuple) else (keys,)
        n = sub.shape[0]
        s = sub["sens"]
        if numeric_sens:
            dist = tvd_numeric(s, ref_series)
        else:
            p = s.value_counts(dropna=False) / n
            dist = tvd_categorical(p, ref_prob)
        rows.append(tuple(list(key_tuple) + [n, dist]))

    # Build result frame
    res_cols = group_cols + ["n", "tvd"]
    metrics = pd.DataFrame(rows, columns=res_cols).sort_values(by=group_cols).reset_index(drop=True)

    # Persist all groups
    groups_csv = "t_closeness_groups.csv"
    metrics.to_csv(groups_csv, index=False)

    bad = metrics[metrics["tvd"] > T_THRESHOLD].sort_values(by=["tvd", "n"], ascending=[False, True])
    viol_csv = None
    if not bad.empty and EXPORT_VIOLATIONS:
        viol_csv = "t_closeness_violations.csv"
        bad.to_csv(viol_csv, index=False)

    # Visualizations (match style from k_anonymity_check.py)
    dist_png = plot_tvd_distribution(metrics, T_THRESHOLD)
    cum_png  = plot_tvd_cumulative(metrics)
    top_png  = plot_top_violations(bad, group_cols) if not bad.empty else None

    out = {
        "status": "PASS" if bad.empty else "FAIL",
        "groups": int(metrics.shape[0]),
        "violating_groups": int(bad.shape[0]),
        "t_threshold": T_THRESHOLD,
        "max_tvd": float(metrics["tvd"].max()) if not metrics.empty else None,
        "min_tvd": float(metrics["tvd"].min()) if not metrics.empty else None,
        "groups_csv": groups_csv,
        "distribution_plot": dist_png,
        "cumulative_plot": cum_png,
    }

    if viol_csv:
        out["violations_csv"] = viol_csv
    if top_png:
        out["top_violations_plot"] = top_png

    if not bad.empty:
        out["violations_preview"] = bad.head(20)

    return out

if __name__ == "__main__":
    print("Running t-closeness (TVD) check...")
    res = check_t_closeness()
    preview = res.pop("violations_preview", None)
    print(res)
    if preview is not None:
        print("\nViolating groups (first 20):")
        print(preview.to_string(index=False))
