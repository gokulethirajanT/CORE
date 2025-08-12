import os
import math
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- plotting (headless) ---
import matplotlib
matplotlib.use("Agg")  # server/CI safe
import matplotlib.pyplot as plt

load_dotenv()

# ---------------- Config ----------------
TABLE = os.getenv("L_TABLE", os.getenv("PUF_VERS_TABLE", "vers_puf"))
SENSITIVE_COL = os.getenv("SENSITIVE_COL", "ICD10")          # <-- set this in your .env
L_TARGET = int(os.getenv("L_TARGET", 2))                      # distinct-count l-diversity target
ENTROPY_L_MIN = float(os.getenv("ENTROPY_L_MIN", 0.693))      # ~ ln(2) by default
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

# --------------- Helpers ----------------
def object_exists(tbl: str) -> bool:
    """Return True if a table or view named tbl exists in public schema."""
    sql = text("""
        SELECT COUNT(*) 
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :tbl
    """)
    with engine.connect() as conn:
        return conn.execute(sql, {"tbl": tbl}).scalar() > 0

def get_columns(tbl: str):
    """Return column names (case-preserving) for tables or views."""
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :tbl
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(sql, {"tbl": tbl}).all()]

def entropy(series: pd.Series) -> float:
    """Shannon entropy of value distribution in a group."""
    counts = series.value_counts(dropna=False)
    if counts.empty:
        return 0.0
    probs = counts / counts.sum()
    return float(-(probs * probs.apply(lambda p: math.log(p) if p > 0 else 0)).sum())

def normalize_group_cols(qis):
    return [(q.split(" AS ")[-1] if " AS " in q else q).replace('"', '') for q in qis]

# ---------- Plots ----------
def plot_l_distribution(df: pd.DataFrame, l_target: int, out_path: str = "l_diversity_l_dist.png"):
    plt.figure(figsize=(8,5))
    plt.hist(df["l_div"], bins=range(1, int(df["l_div"].max()) + 2), edgecolor="black", align="left")
    plt.axvline(l_target, linestyle="--", linewidth=2, label=f"L_TARGET = {l_target}")
    plt.title("DM3 CORE Class 2 — l-Diversity (distinct count) Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("Distinct sensitive values per group (l)")
    plt.ylabel("Number of Groups")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_entropy_distribution(df: pd.DataFrame, entropy_min: float, out_path: str = "l_diversity_entropy_dist.png"):
    plt.figure(figsize=(8,5))
    plt.hist(df["entropy_l"], bins=30, edgecolor="black")
    plt.axvline(entropy_min, linestyle="--", linewidth=2, label=f"ENTROPY_L_MIN = {entropy_min}")
    plt.title("DM3 CORE Class 2 — Entropy l-Diversity Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("Shannon entropy of sensitive value distribution")
    plt.ylabel("Number of Groups")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_cumulative_l(df: pd.DataFrame, out_path: str = "l_diversity_cumulative_l.png"):
    sizes = sorted(df["l_div"].unique())
    total_groups = len(df)
    xs, ys = [], []
    for k in sizes:
        pct = (df["l_div"] >= k).sum() / total_groups * 100.0
        xs.append(k)
        ys.append(pct)
    plt.figure(figsize=(8,5))
    plt.plot(xs, ys, marker="o")
    plt.title("DM3 Class 2: Cumulative Coverage by l (distinct count)")
    plt.xlabel("l (minimum distinct sensitive values)")
    plt.ylabel("Groups with l ≥ x (%)")
    plt.grid(True, linewidth=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_cumulative_entropy(df: pd.DataFrame, out_path: str = "l_diversity_cumulative_entropy.png"):
    xs = np.linspace(0, max(1.0, df["entropy_l"].max()), 200)
    ys = [(df["entropy_l"] >= x).mean() * 100.0 for x in xs]
    plt.figure(figsize=(8,5))
    plt.plot(xs, ys)
    plt.title("DM3 Class 2: Cumulative Coverage by Entropy-l")
    plt.xlabel("Entropy bound (x)")
    plt.ylabel("Groups with entropy ≥ x (%)")
    plt.grid(True, linewidth=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_top_violations(bad_df: pd.DataFrame, group_cols: list[str], out_path: str = "l_diversity_top_violations.png", top_n: int = 20):
    if bad_df.empty:
        return None
    def mk_label(row):
        return " | ".join(f"{c}={row[c]}" for c in group_cols)
    tmp = bad_df.copy()
    tmp["group"] = tmp.apply(mk_label, axis=1)
    # Worst = smallest l_div, then smallest entropy; show top_n
    tmp = tmp.sort_values(["l_div", "entropy_l", "n"], ascending=[True, True, True]).head(top_n)
    plt.figure(figsize=(10, max(4, 0.4 * len(tmp))))
    plt.barh(tmp["group"], tmp["l_div"], edgecolor="black")
    plt.gca().invert_yaxis()
    plt.xlabel("l (distinct sensitive values)")
    plt.title(f"Top {len(tmp)} l-Diversity Violations (lower is worse)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

# --------------- Main check -------------
def check_l_diversity(return_violations=True):
    if not object_exists(TABLE):
        return {"status": "FAIL", "reason": f"Missing table/view {TABLE}"}

    cols_raw = get_columns(TABLE)
    cols = [c.upper() for c in cols_raw]

    if SENSITIVE_COL.upper() not in cols:
        return {"status": "FAIL", "reason": f"Sensitive column '{SENSITIVE_COL}' not found in {TABLE}"}

    # Build QIs: accept raw fields or precomputed aliases
    qis = []
    if "PLZ" in cols:
        qis.append('LEFT("PLZ",3) AS PLZ3')
    elif "PLZ3" in cols:
        qis.append('"PLZ3"')
    if "GEBJAHR" in cols:
        qis.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS GEBJAHR_BAND')
    elif "GEBJAHR_BAND" in cols:
        qis.append('"GEBJAHR_BAND"')
    if "GESCHLECHT" in cols:
        qis.append('"GESCHLECHT"')

    if not qis:
        return {"status": "FAIL", "reason": "No quasi-identifiers available (expecting PLZ/PLZ3, GEBJAHR/GEBJAHR_BAND, or GESCHLECHT)."}

    select_qis = ", ".join(qis)
    group_cols = normalize_group_cols(qis)

    # Pull row-level data (QIs + sensitive), then aggregate in pandas
    sql = text(f"""
        SELECT {select_qis}, "{SENSITIVE_COL}" AS sens
        FROM {TABLE}
        WHERE "{SENSITIVE_COL}" IS NOT NULL
    """)
    df = pd.read_sql_query(sql, engine)
    if df.empty:
        return {"status": "FAIL", "reason": f"No rows with non-null {SENSITIVE_COL} in {TABLE}"}

    # Aggregate
    grp = df.groupby(group_cols, dropna=False)
    metrics = grp.agg(n=("sens", "size"),
                      l_div=("sens", pd.Series.nunique)).reset_index()

    # Entropy l-diversity per group
    ent = grp["sens"].apply(entropy).reset_index(name="entropy_l")
    metrics = metrics.merge(ent, on=group_cols, how="left")

    # Persist all groups
    groups_csv = "l_diversity_groups.csv"
    metrics.to_csv(groups_csv, index=False)

    # Violations
    bad = metrics[(metrics["l_div"] < L_TARGET) | (metrics["entropy_l"] < ENTROPY_L_MIN)].copy()

    viol_csv = None
    if not bad.empty and EXPORT_VIOLATIONS:
        viol_csv = "l_diversity_violations.csv"
        bad.sort_values(by=["l_div", "entropy_l", "n"], ascending=[True, True, True]).to_csv(viol_csv, index=False)

    # Visualizations
    l_dist_png       = plot_l_distribution(metrics, L_TARGET)
    ent_dist_png     = plot_entropy_distribution(metrics, ENTROPY_L_MIN)
    l_cum_png        = plot_cumulative_l(metrics)
    ent_cum_png      = plot_cumulative_entropy(metrics)
    top_viol_png     = plot_top_violations(bad, group_cols) if not bad.empty else None

    result = {
        "status": "PASS" if bad.empty else "FAIL",
        "groups": int(metrics.shape[0]),
        "min_l_div": int(metrics["l_div"].min()) if not metrics.empty else None,
        "min_entropy_l": float(metrics["entropy_l"].min()) if not metrics.empty else None,
        "violating_groups": int(bad.shape[0]),
        "l_target": L_TARGET,
        "entropy_l_min": ENTROPY_L_MIN,
        "groups_csv": groups_csv,
        "l_dist_plot": l_dist_png,
        "entropy_dist_plot": ent_dist_png,
        "l_cumulative_plot": l_cum_png,
        "entropy_cumulative_plot": ent_cum_png,
    }
    if viol_csv:
        result["violations_csv"] = viol_csv
    if top_viol_png:
        result["top_violations_plot"] = top_viol_png

    if return_violations and not bad.empty:
        result["violations"] = bad.sort_values(by=["l_div", "entropy_l", "n"], ascending=[True, True, True]).reset_index(drop=True)

    return result

# --------------- CLI --------------------
if __name__ == "__main__":
    print("Running l-diversity (distinct & entropy) check...")
    res = check_l_diversity(return_violations=True)
    summary = {k: v for k, v in res.items() if k not in ("violations",)}
    print(summary)
    if "violations" in res:
        print("\nViolating groups (first 20):")
        print(res["violations"].head(20).to_string(index=False))
