import os
import math
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

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
    # PLZ or PLZ3
    if "PLZ" in cols:
        qis.append('LEFT("PLZ",3) AS PLZ3')
    elif "PLZ3" in cols:
        qis.append('"PLZ3"')

    # GEBJAHR or GEBJAHR_BAND
    if "GEBJAHR" in cols:
        qis.append('(FLOOR("GEBJAHR"::int/5)*5)::int AS GEBJAHR_BAND')
    elif "GEBJAHR_BAND" in cols:
        qis.append('"GEBJAHR_BAND"')

    # GESCHLECHT (optional extra QI if present)
    if "GESCHLECHT" in cols:
        qis.append('"GESCHLECHT"')

    if not qis:
        return {"status": "FAIL", "reason": "No quasi-identifiers available (expecting PLZ/PLZ3, GEBJAHR/GEBJAHR_BAND, or GESCHLECHT)."}

    select_qis = ", ".join(qis)
    # Normalize group column names: strip quotes and pick alias if present
    group_cols = [(q.split(" AS ")[-1] if " AS " in q else q).replace('"', '') for q in qis]

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

    # Violations
    bad = metrics[(metrics["l_div"] < L_TARGET) | (metrics["entropy_l"] < ENTROPY_L_MIN)].copy()

    result = {
        "status": "PASS" if bad.empty else "FAIL",
        "groups": int(metrics.shape[0]),
        "min_l_div": int(metrics["l_div"].min()) if not metrics.empty else None,
        "min_entropy_l": float(metrics["entropy_l"].min()) if not metrics.empty else None,
        "violating_groups": int(bad.shape[0]),
        "l_target": L_TARGET,
        "entropy_l_min": ENTROPY_L_MIN,
    }

    if return_violations and not bad.empty:
        bad = bad.sort_values(by=["l_div", "entropy_l", "n"],
                              ascending=[True, True, True]).reset_index(drop=True)
        result["violations"] = bad
        if EXPORT_VIOLATIONS:
            out = "l_diversity_violations.csv"
            bad.to_csv(out, index=False)
            result["violations_csv"] = out

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
