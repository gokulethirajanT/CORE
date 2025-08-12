# delta_presence_test.py
import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- plotting (headless) ---
import matplotlib
matplotlib.use("Agg")  # server/CI-safe
import matplotlib.pyplot as plt

load_dotenv()

# ------------ Config ------------
SAMPLE_TABLE = os.getenv("L_TABLE", "vers_puf")        # sample (PUF DB)
POP_TABLE    = os.getenv("POP_TABLE", "vers")          # population (Seeder DB)
DELTA_MIN    = float(os.getenv("DELTA_MIN", 0.0))      # lower bound (e.g., 0.0–0.1)
DELTA_MAX    = float(os.getenv("DELTA_MAX", 0.2))      # upper bound (e.g., 0.1–0.2)
EXPORT_VIOLATIONS = os.getenv("EXPORT_VIOLATIONS", "1") == "1"

def build_pg_url(prefix: str):
    user = os.getenv(f"{prefix}_DB_USER") or os.getenv("DB_USER")
    pwd  = os.getenv(f"{prefix}_DB_PASSWORD") or os.getenv("DB_PASSWORD")
    host = os.getenv(f"{prefix}_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv(f"{prefix}_DB_PORT") or os.getenv("DB_PORT", "5432")
    name = os.getenv(f"{prefix}_DB_NAME") or os.getenv("DB_NAME")
    if not (user and pwd and host and port and name):
        raise RuntimeError(f"Missing DB env vars for {prefix}")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"

PUF_URL      = os.getenv("DATABASE_URL") or build_pg_url("PUF")
BASELINE_URL = os.getenv("BASELINE_DB_URL") or build_pg_url("BASELINE")

eng_sample = create_engine(PUF_URL)
eng_pop    = create_engine(BASELINE_URL)

# ------------ Helpers ------------
def object_exists(engine, tbl: str) -> bool:
    sql = text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name=:tbl
    """)
    with engine.connect() as conn:
        return conn.execute(sql, {"tbl": tbl}).scalar() > 0

def get_columns(engine, tbl: str):
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:tbl
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(sql, {"tbl": tbl}).all()]

def build_qi_sql(cols_upper):
    """
    Return (select_exprs, group_by_exprs, labels) for QIs.
    Supports raw (PLZ, GEBJAHR) or precomputed (PLZ3, GEBJAHR_BAND) + optional GESCHLECHT.
    """
    select_exprs, group_by_exprs, labels = [], [], []

    # PLZ or PLZ3
    if "PLZ" in cols_upper:
        select_exprs.append('LEFT("PLZ",3) AS "PLZ3"')
        group_by_exprs.append('LEFT("PLZ",3)')
        labels.append('PLZ3')
    elif "PLZ3" in cols_upper:
        select_exprs.append('"PLZ3"')
        group_by_exprs.append('"PLZ3"')
        labels.append('PLZ3')

    # GEBJAHR or GEBJAHR_BAND
    if "GEBJAHR" in cols_upper:
        select_exprs.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS "GEBJAHR_BAND"')
        group_by_exprs.append('(FLOOR("GEBJAHR"::int/5)*5)::int')
        labels.append('GEBJAHR_BAND')
    elif "GEBJAHR_BAND" in cols_upper:
        select_exprs.append('"GEBJAHR_BAND"')
        group_by_exprs.append('"GEBJAHR_BAND"')
        labels.append('GEBJAHR_BAND')

    # Optional extra QI
    if "GESCHLECHT" in cols_upper:
        select_exprs.append('"GESCHLECHT"')
        group_by_exprs.append('"GESCHLECHT"')
        labels.append('GESCHLECHT')

    if not labels:
        raise RuntimeError("No usable QIs (need PLZ/PLZ3, GEBJAHR/GEBJAHR_BAND, or GESCHLECHT).")

    return select_exprs, group_by_exprs, labels

def aggregated_counts(engine, table: str):
    cols = [c.upper() for c in get_columns(engine, table)]
    select_exprs, group_by_exprs, labels = build_qi_sql(cols)
    select_qis = ", ".join(select_exprs)
    group_by_sql = ", ".join(group_by_exprs)
    sql = text(f"""
        SELECT {select_qis}, COUNT(*)::bigint AS n
        FROM {table}
        GROUP BY {group_by_sql}
    """)
    df = pd.read_sql_query(sql, engine)
    return df, labels

# ---------- Plots ----------
def plot_delta_distribution(df: pd.DataFrame, dmin: float, dmax: float, out_path: str = "delta_presence_distribution.png"):
    plt.figure(figsize=(8,5))
    plt.hist(df["delta"], bins=30, edgecolor="black")
    plt.axvline(dmin, linestyle="--", linewidth=2, label=f"DELTA_MIN = {dmin}")
    plt.axvline(dmax, linestyle="--", linewidth=2, label=f"DELTA_MAX = {dmax}")
    plt.title("DM3 CORE Class 1 — δ-Presence Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("δ = n_sample / n_pop")
    plt.ylabel("Number of Groups")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_delta_cumulative(df: pd.DataFrame, out_path: str = "delta_presence_cumulative.png"):
    """
    ECDF of delta: x = threshold t, y = % groups with delta ≤ t.
    """
    xs = np.linspace(0, max(1.0, df["delta"].max()), 200)
    ys = [(df["delta"] <= x).mean() * 100.0 for x in xs]
    plt.figure(figsize=(8,5))
    plt.plot(xs, ys)
    plt.title("DM3 Class 1: Cumulative Coverage by δ Threshold")
    plt.xlabel("δ threshold (t)")
    plt.ylabel("Groups with δ ≤ t (%)")
    plt.grid(True, linewidth=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

def plot_top_violations(bad_df: pd.DataFrame, group_cols: list[str], dmin: float, dmax: float,
                        out_path: str = "delta_presence_top_violations.png", top_n: int = 20):
    if bad_df.empty:
        return None
    def mk_label(row):
        return " | ".join(f"{c}={row[c]}" for c in group_cols)
    tmp = bad_df.copy()
    # How far outside bounds a group is (0 if inside)
    def gap(d):
        if d < dmin: return dmin - d
        if d > dmax: return d - dmax
        return 0.0
    tmp["gap"] = tmp["delta"].apply(gap)
    tmp["group"] = tmp.apply(mk_label, axis=1)
    tmp = tmp.sort_values(["gap", "delta"], ascending=[False, False]).head(top_n)

    plt.figure(figsize=(10, max(4, 0.4*len(tmp))))
    plt.barh(tmp["group"], tmp["gap"], edgecolor="black")
    plt.gca().invert_yaxis()
    plt.xlabel("Gap outside bounds")
    plt.title(f"Top {len(tmp)} δ-Presence Violations (farther = worse)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path

# ------------ Main ------------
def check_delta_presence():
    if not object_exists(eng_sample, SAMPLE_TABLE):
        return {"status":"FAIL", "reason": f"Missing sample table/view {SAMPLE_TABLE} in PUF DB"}
    if not object_exists(eng_pop, POP_TABLE):
        return {"status":"FAIL", "reason": f"Missing population table/view {POP_TABLE} in BASELINE DB"}

    # Aggregate sample & population by same QIs
    sample_counts, group_cols_s = aggregated_counts(eng_sample, SAMPLE_TABLE)
    pop_counts,    group_cols_p = aggregated_counts(eng_pop, POP_TABLE)

    if group_cols_s != group_cols_p:
        return {"status":"FAIL",
                "reason": f"QI mismatch between sample {group_cols_s} and population {group_cols_p}. "
                          f"Ensure both sides expose the same QIs (e.g., PLZ/PLZ3, GEBJAHR/GEBJAHR_BAND, GESCHLECHT)."}

    key_cols = group_cols_s
    merged = pd.merge(
        pop_counts.rename(columns={"n":"n_pop"}),
        sample_counts.rename(columns={"n":"n_sample"}),
        on=key_cols, how="left"
    )
    merged["n_sample"] = merged["n_sample"].fillna(0).astype("int64")
    merged["delta"] = merged.apply(lambda r: (r["n_sample"]/r["n_pop"]) if r["n_pop"] > 0 else 1.0, axis=1)
    merged["violation"] = (merged["delta"] < DELTA_MIN) | (merged["delta"] > DELTA_MAX)

    # Persist all groups
    groups_csv = "delta_presence_groups.csv"
    merged.to_csv(groups_csv, index=False)

    bad = merged[merged["violation"]].copy()
    bad = bad.sort_values(by=["delta"] + key_cols, ascending=[False] + [True]*len(key_cols))

    # Visuals
    dist_png = plot_delta_distribution(merged, DELTA_MIN, DELTA_MAX)
    cum_png  = plot_delta_cumulative(merged)
    top_png  = plot_top_violations(bad, key_cols, DELTA_MIN, DELTA_MAX) if not bad.empty else None

    pct_in_bounds = float(((~merged["violation"]).mean()) * 100.0)

    out = {
        "status": "PASS" if bad.empty else "FAIL",
        "groups": int(merged.shape[0]),
        "violating_groups": int(bad.shape[0]),
        "delta_min": DELTA_MIN,
        "delta_max": DELTA_MAX,
        "max_delta": float(merged["delta"].max()) if not merged.empty else None,
        "min_delta": float(merged["delta"].min()) if not merged.empty else None,
        "pct_in_bounds": pct_in_bounds,
        "groups_csv": groups_csv,
        "distribution_plot": dist_png,
        "cumulative_plot": cum_png,
    }

    if not bad.empty and EXPORT_VIOLATIONS:
        bad.to_csv("delta_presence_violations.csv", index=False)
        out["violations_csv"] = "delta_presence_violations.csv"
    if top_png:
        out["top_violations_plot"] = top_png

    if not bad.empty:
        out["violations_preview"] = bad.head(20)

    return out

if __name__ == "__main__":
    print("Running δ-presence check (sample vs population)...")
    res = check_delta_presence()
    preview = res.pop("violations_preview", None)
    print(res)
    if preview is not None:
        print("\nViolating groups (first 20):")
        print(preview.to_string(index=False))
