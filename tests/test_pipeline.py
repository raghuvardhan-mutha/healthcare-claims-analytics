"""Fast structural and analytics checks for the generated warehouse."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ensure_pipeline() -> Path:
    db = ROOT / "data" / "claims_analytics.db"
    if not db.exists():
        for script in ("generate_data.py", "load_data.py", "build_star_schema.py", "build_data_marts.py"):
            subprocess.run([sys.executable, str(ROOT / "etl" / script)], check=True, cwd=ROOT)
    return db


def test_expected_tables_and_row_counts() -> None:
    with sqlite3.connect(ensure_pipeline()) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {
            "beneficiaries", "providers", "inpatient_claims", "outpatient_claims", "carrier_claims",
            "claim_adjudication", "claim_integrity_labels", "dim_date", "dim_member",
            "dim_provider", "fact_claim",
        } <= tables
        assert conn.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0] == 5_000
        assert conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0] == 400


def test_core_data_quality_rules() -> None:
    with sqlite3.connect(ensure_pipeline()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM inpatient_claims WHERE claim_payment_amount < 0").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM outpatient_claims WHERE claim_end_date < claim_start_date").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM carrier_claims WHERE claim_status NOT IN ('Paid','Denied','Pending','Appealed')").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM claim_procedures WHERE line_charge_amount < 0").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM claim_adjudication WHERE paid_amount > allowed_amount OR allowed_amount > billed_amount"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM claim_adjudication WHERE received_date < submitted_date OR adjudicated_date < received_date"
        ).fetchone()[0] == 0


def test_star_schema_reconciles_to_source_claims() -> None:
    with sqlite3.connect(ensure_pipeline()) as conn:
        source_count = conn.execute(
            "SELECT (SELECT COUNT(*) FROM inpatient_claims) + "
            "(SELECT COUNT(*) FROM outpatient_claims) + (SELECT COUNT(*) FROM carrier_claims)"
        ).fetchone()[0]
        assert conn.execute("SELECT COUNT(*) FROM fact_claim").fetchone()[0] == source_count
        source_paid = conn.execute("SELECT ROUND(SUM(paid_amount), 2) FROM claim_adjudication").fetchone()[0]
        fact_paid = conn.execute("SELECT ROUND(SUM(paid_amount), 2) FROM fact_claim").fetchone()[0]
        assert fact_paid == source_paid
        assert conn.execute("SELECT COUNT(*) FROM fact_claim WHERE adjudication_days < 0").fetchone()[0] == 0


def test_data_marts_are_created() -> None:
    ensure_pipeline()
    expected = {
        "executive_summary.csv", "claims_by_status.csv", "financial_by_specialty.csv",
        "provider_performance.csv", "patient_chronic_conditions.csv", "fraud_risk_providers.csv",
    }
    assert expected <= {path.name for path in (ROOT / "dashboards" / "data_marts").glob("*.csv")}


def test_snowflake_exports_and_deployment_scripts() -> None:
    ensure_pipeline()
    expected_exports = {
        "dim_date.csv", "dim_member.csv", "dim_provider.csv", "fact_claim.csv",
        "bridge_claim_diagnosis.csv", "fact_claim_procedure.csv",
    }
    assert expected_exports <= {path.name for path in (ROOT / "data" / "snowflake").glob("*.csv")}
    ddl = (ROOT / "snowflake" / "01_star_schema.sql").read_text(encoding="utf-8").upper()
    load = (ROOT / "snowflake" / "02_load.sql").read_text(encoding="utf-8").upper()
    assert all(name in ddl for name in ("DIM_DATE", "DIM_MEMBER", "DIM_PROVIDER", "FACT_CLAIM"))
    assert "COPY INTO FACT_CLAIM" in load
