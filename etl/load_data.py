"""
load_data.py
-------------
ETL step 2: loads the generated CSVs (data/*.csv) into a database according
to sql/01_schema.sql, then runs a set of source-to-target validation checks
and writes a data-quality log.

Uses SQLite for this repo's local/demo environment (zero external
dependencies, runs anywhere). The schema and all downstream SQL in sql/ are
written in standard SQL and are portable to PostgreSQL -- to point this at
Postgres instead, swap the sqlite3 connection below for psycopg2 and run
sql/01_schema.sql against your Postgres instance first.
"""
import sqlite3
import csv
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCHEMA_FILE = os.path.join(BASE_DIR, "sql", "01_schema.sql")
DB_FILE = os.path.join(BASE_DIR, "data", "claims_analytics.db")
LOG_FILE = os.path.join(BASE_DIR, "docs", "etl_validation_log.md")

TABLE_LOAD_ORDER = [
    "diagnosis_codes", "procedure_codes", "drug_codes",
    "beneficiaries", "chronic_conditions", "providers",
    "inpatient_claims", "outpatient_claims", "carrier_claims",
    "prescription_drug_events", "claim_diagnoses", "claim_procedures",
    "claim_adjudication", "claim_integrity_labels",
]

BOOL_COLUMNS = {
    "beneficiaries": ["esrd_indicator"],
    "chronic_conditions": ["has_condition"],
    "providers": ["npi_flag_suspicious"],
    "drug_codes": ["is_generic"],
    "claim_adjudication": ["appeal_indicator"],
    "claim_integrity_labels": ["is_injected_signal"],
}


def sqlite_compatible_schema(sql_text: str) -> str:
    """Strip Postgres-only syntax (REFERENCES with types SQLite lacks are fine,
    but NUMERIC(p,s) and BOOLEAN need light translation for older SQLite)."""
    sql_text = re.sub(r"NUMERIC\(\d+,\s*\d+\)", "REAL", sql_text)
    sql_text = sql_text.replace("BOOLEAN", "INTEGER")
    return sql_text


def build_schema(conn):
    with open(SCHEMA_FILE) as f:
        raw = f.read()
    conn.executescript(sqlite_compatible_schema(raw))
    conn.commit()


def load_csv(conn, table):
    path = os.path.join(DATA_DIR, f"{table}.csv")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        bool_cols = BOOL_COLUMNS.get(table, [])
        rows = []
        for r in reader:
            vals = []
            for c in cols:
                v = r[c]
                if c in bool_cols:
                    v = 1 if str(v).strip().lower() in ("true", "1") else 0
                elif v == "":
                    v = None
                vals.append(v)
            rows.append(vals)
        placeholders = ",".join(["?"] * len(cols))
        conn.executemany(
            f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", rows
        )
    conn.commit()
    return len(rows)


def run_validation(conn):
    """Source-to-target row counts + basic referential/data-quality checks."""
    lines = ["# ETL Validation Log", ""]
    cur = conn.cursor()

    lines.append("## Row counts (source CSV -> target table)")
    validation_passed = True
    for t in TABLE_LOAD_ORDER:
        src_path = os.path.join(DATA_DIR, f"{t}.csv")
        with open(src_path) as f:
            src_count = sum(1 for _ in f) - 1
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        tgt_count = cur.fetchone()[0]
        status = "OK" if src_count == tgt_count else "MISMATCH"
        validation_passed = validation_passed and src_count == tgt_count
        lines.append(f"- `{t}`: source={src_count:,} | loaded={tgt_count:,} | **{status}**")

    lines.append("\n## Referential integrity checks")
    checks = [
        ("Inpatient claims with no matching beneficiary",
         "SELECT COUNT(*) FROM inpatient_claims ip LEFT JOIN beneficiaries b "
         "ON ip.beneficiary_id = b.beneficiary_id WHERE b.beneficiary_id IS NULL"),
        ("Outpatient claims with no matching provider",
         "SELECT COUNT(*) FROM outpatient_claims op LEFT JOIN providers p "
         "ON op.provider_id = p.provider_id WHERE p.provider_id IS NULL"),
        ("Carrier claims with negative payment amount",
         "SELECT COUNT(*) FROM carrier_claims WHERE claim_payment_amount < 0"),
        ("Claim diagnoses referencing unknown diagnosis codes",
         "SELECT COUNT(*) FROM claim_diagnoses cd LEFT JOIN diagnosis_codes d "
         "ON cd.diagnosis_code = d.diagnosis_code WHERE d.diagnosis_code IS NULL"),
        ("Outpatient claims with end date before start date",
         "SELECT COUNT(*) FROM outpatient_claims WHERE claim_end_date < claim_start_date"),
        ("Claims with invalid status values",
         "SELECT COUNT(*) FROM ("
         "SELECT claim_status FROM inpatient_claims UNION ALL "
         "SELECT claim_status FROM outpatient_claims UNION ALL "
         "SELECT claim_status FROM carrier_claims) "
         "WHERE claim_status NOT IN ('Paid','Denied','Pending','Appealed')"),
        ("Procedure lines with negative charges",
         "SELECT COUNT(*) FROM claim_procedures WHERE line_charge_amount < 0"),
        ("Adjudication dates outside submitted-received-adjudicated order",
         "SELECT COUNT(*) FROM claim_adjudication WHERE received_date < submitted_date "
         "OR adjudicated_date < received_date OR (payment_date IS NOT NULL AND payment_date < adjudicated_date)"),
        ("Adjudications where paid exceeds allowed or allowed exceeds billed",
         "SELECT COUNT(*) FROM claim_adjudication WHERE paid_amount > allowed_amount OR allowed_amount > billed_amount"),
        ("Denied adjudications with a nonzero payment",
         "SELECT COUNT(*) FROM claim_adjudication WHERE adjudication_status = 'Denied' AND paid_amount <> 0"),
        ("Claims missing an adjudication record",
         "SELECT COUNT(*) FROM (SELECT claim_id, 'inpatient' claim_type FROM inpatient_claims UNION ALL "
         "SELECT claim_id, 'outpatient' FROM outpatient_claims UNION ALL "
         "SELECT claim_id, 'carrier' FROM carrier_claims) c LEFT JOIN claim_adjudication a "
         "ON c.claim_id = a.claim_id AND c.claim_type = a.claim_type WHERE a.claim_id IS NULL"),
    ]
    for label, q in checks:
        cur.execute(q)
        n = cur.fetchone()[0]
        status = "PASS" if n == 0 else f"FLAGGED ({n} rows)"
        validation_passed = validation_passed and n == 0
        lines.append(f"- {label}: **{status}**")

    lines.append("\n## Summary")
    cur.execute("SELECT COUNT(*) FROM inpatient_claims")
    ip = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM outpatient_claims")
    op = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM carrier_claims")
    cc = cur.fetchone()[0]
    total = ip + op + cc
    lines.append(f"- Total claims loaded: **{total:,}** ({ip:,} inpatient, {op:,} outpatient, {cc:,} carrier)")
    lines.append(f"- Validation result: **{'PASS' if validation_passed else 'REVIEW FLAGS ABOVE'}**")

    with open(LOG_FILE, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"Building schema from {SCHEMA_FILE} ...")
    build_schema(conn)
    print("Loading CSVs...\n")
    for t in TABLE_LOAD_ORDER:
        n = load_csv(conn, t)
        print(f"  Loaded {n:,} rows into {t}")
    print("\nRunning source-to-target validation...\n")
    run_validation(conn)
    conn.close()
    print(f"\nDatabase ready at: {DB_FILE}")
