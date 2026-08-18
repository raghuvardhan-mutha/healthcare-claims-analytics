"""Create documented, dashboard-ready CSV marts from the SQLite warehouse."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "claims_analytics.db"
OUT_DIR = ROOT / "dashboards" / "data_marts"


MARTS = {
    "executive_summary.csv": """
        WITH all_claims AS (
            SELECT claim_start_date, claim_payment_amount FROM inpatient_claims
            UNION ALL SELECT claim_start_date, claim_payment_amount FROM outpatient_claims
            UNION ALL SELECT claim_start_date, claim_payment_amount FROM carrier_claims
        )
        SELECT strftime('%Y-%m', claim_start_date) AS month,
               COUNT(*) AS claims,
               ROUND(SUM(claim_payment_amount), 2) AS total_paid
        FROM all_claims GROUP BY month ORDER BY month
    """,
    "claims_by_status.csv": """
        WITH all_claims AS (
            SELECT claim_status FROM inpatient_claims
            UNION ALL SELECT claim_status FROM outpatient_claims
            UNION ALL SELECT claim_status FROM carrier_claims
        )
        SELECT claim_status, COUNT(*) AS claims
        FROM all_claims GROUP BY claim_status ORDER BY claims DESC
    """,
    "financial_by_specialty.csv": """
        WITH all_claims AS (
            SELECT provider_id, claim_payment_amount FROM inpatient_claims
            UNION ALL SELECT provider_id, claim_payment_amount FROM outpatient_claims
            UNION ALL SELECT provider_id, claim_payment_amount FROM carrier_claims
        )
        SELECT p.specialty, COUNT(*) AS claims,
               ROUND(SUM(a.claim_payment_amount), 2) AS total_paid
        FROM all_claims a JOIN providers p USING (provider_id)
        GROUP BY p.specialty ORDER BY total_paid DESC
    """,
    "provider_performance.csv": """
        WITH all_claims AS (
            SELECT provider_id, claim_payment_amount FROM inpatient_claims
            UNION ALL SELECT provider_id, claim_payment_amount FROM outpatient_claims
            UNION ALL SELECT provider_id, claim_payment_amount FROM carrier_claims
        )
        SELECT p.provider_id, p.provider_name, p.specialty,
               COUNT(*) AS claims, ROUND(SUM(a.claim_payment_amount), 2) AS total_paid,
               ROUND(AVG(a.claim_payment_amount), 2) AS avg_paid
        FROM all_claims a JOIN providers p USING (provider_id)
        GROUP BY p.provider_id, p.provider_name, p.specialty
        ORDER BY total_paid DESC LIMIT 50
    """,
    "patient_chronic_conditions.csv": """
        SELECT condition_name,
               SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) AS beneficiaries_affected,
               ROUND(100.0 * SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS prevalence_pct
        FROM chronic_conditions GROUP BY condition_name ORDER BY prevalence_pct DESC
    """,
    "fraud_risk_providers.csv": """
        WITH outpatient_lines AS (
            SELECT o.provider_id, o.claim_id, COUNT(cp.procedure_code) AS line_items
            FROM outpatient_claims o
            JOIN claim_procedures cp ON o.claim_id = cp.claim_id AND cp.claim_type = 'outpatient'
            GROUP BY o.provider_id, o.claim_id
        ),
        unbundling AS (
            SELECT provider_id,
                   AVG(line_items) AS avg_line_items,
                   SUM(CASE WHEN line_items >= 3 THEN 1 ELSE 0 END) AS unbundled_claims
            FROM outpatient_lines GROUP BY provider_id
        ),
        duplicate_groups AS (
            SELECT cc.provider_id, cc.beneficiary_id, cc.claim_start_date, cp.procedure_code,
                   COUNT(DISTINCT cc.claim_id) AS billed_count
            FROM carrier_claims cc
            JOIN claim_procedures cp ON cc.claim_id = cp.claim_id AND cp.claim_type = 'carrier'
            GROUP BY cc.provider_id, cc.beneficiary_id, cc.claim_start_date, cp.procedure_code
            HAVING COUNT(DISTINCT cc.claim_id) >= 2
        ),
        duplicates AS (
            SELECT provider_id, COUNT(*) AS duplicate_groups
            FROM duplicate_groups GROUP BY provider_id
        ),
        provider_cost AS (
            SELECT provider_id, AVG(claim_payment_amount) AS avg_paid
            FROM outpatient_claims GROUP BY provider_id
        ),
        specialty_cost AS (
            SELECT p.specialty, AVG(pc.avg_paid) AS specialty_avg_paid
            FROM provider_cost pc JOIN providers p USING (provider_id)
            GROUP BY p.specialty
        )
        SELECT p.provider_id, p.provider_name, p.specialty,
               ROUND(u.avg_line_items, 2) AS avg_line_items_per_claim,
               u.unbundled_claims, COALESCE(d.duplicate_groups, 0) AS duplicate_groups,
               ROUND(pc.avg_paid / NULLIF(sc.specialty_avg_paid, 0), 2) AS cost_vs_peer_ratio,
               ROUND(
                   2.0 * u.unbundled_claims
                   + 3.0 * COALESCE(d.duplicate_groups, 0)
                   + 10.0 * MAX(pc.avg_paid / NULLIF(sc.specialty_avg_paid, 0) - 1.0, 0),
                   2
               ) AS composite_risk_score
        FROM providers p
        JOIN unbundling u USING (provider_id)
        JOIN provider_cost pc USING (provider_id)
        JOIN specialty_cost sc USING (specialty)
        LEFT JOIN duplicates d USING (provider_id)
        ORDER BY composite_risk_score DESC LIMIT 50
    """,
}


def write_query(conn: sqlite3.Connection, filename: str, query: str) -> None:
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    with (OUT_DIR / filename).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([column[0] for column in cursor.description])
        writer.writerows(rows)
    print(f"  {filename}: {len(rows):,} rows")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Warehouse not found. Run etl/load_data.py first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for filename, query in MARTS.items():
            write_query(conn, filename, query)


if __name__ == "__main__":
    main()
