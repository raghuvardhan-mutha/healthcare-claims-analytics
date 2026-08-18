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
        for script in ("generate_data.py", "load_data.py", "build_data_marts.py"):
            subprocess.run([sys.executable, str(ROOT / "etl" / script)], check=True, cwd=ROOT)
    return db


def test_expected_tables_and_row_counts() -> None:
    with sqlite3.connect(ensure_pipeline()) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"beneficiaries", "providers", "inpatient_claims", "outpatient_claims", "carrier_claims"} <= tables
        assert conn.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0] == 5_000
        assert conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0] == 400


def test_core_data_quality_rules() -> None:
    with sqlite3.connect(ensure_pipeline()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM inpatient_claims WHERE claim_payment_amount < 0").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM outpatient_claims WHERE claim_end_date < claim_start_date").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM carrier_claims WHERE claim_status NOT IN ('Paid','Denied','Pending','Appealed')").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM claim_procedures WHERE line_charge_amount < 0").fetchone()[0] == 0


def test_data_marts_are_created() -> None:
    ensure_pipeline()
    expected = {
        "executive_summary.csv", "claims_by_status.csv", "financial_by_specialty.csv",
        "provider_performance.csv", "patient_chronic_conditions.csv", "fraud_risk_providers.csv",
    }
    assert expected <= {path.name for path in (ROOT / "dashboards" / "data_marts").glob("*.csv")}
