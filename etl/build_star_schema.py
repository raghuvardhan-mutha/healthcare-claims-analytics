"""Build a Power BI- and Snowflake-aligned dimensional layer in SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "claims_analytics.db"


DDL = """
DROP TABLE IF EXISTS fact_claim_procedure;
DROP TABLE IF EXISTS bridge_claim_diagnosis;
DROP TABLE IF EXISTS fact_claim;
DROP TABLE IF EXISTS dim_provider;
DROP TABLE IF EXISTS dim_member;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date AS
WITH dates AS (
    SELECT claim_start_date AS calendar_date FROM inpatient_claims
    UNION SELECT claim_start_date FROM outpatient_claims
    UNION SELECT claim_start_date FROM carrier_claims
)
SELECT CAST(strftime('%Y%m%d', calendar_date) AS INTEGER) AS date_key,
       calendar_date,
       CAST(strftime('%Y', calendar_date) AS INTEGER) AS year,
       CAST(strftime('%m', calendar_date) AS INTEGER) AS month_number,
       strftime('%Y-%m', calendar_date) AS year_month,
       CASE CAST(strftime('%m', calendar_date) AS INTEGER)
           WHEN 1 THEN 'January' WHEN 2 THEN 'February' WHEN 3 THEN 'March'
           WHEN 4 THEN 'April' WHEN 5 THEN 'May' WHEN 6 THEN 'June'
           WHEN 7 THEN 'July' WHEN 8 THEN 'August' WHEN 9 THEN 'September'
           WHEN 10 THEN 'October' WHEN 11 THEN 'November' ELSE 'December'
       END AS month_name,
       ((CAST(strftime('%m', calendar_date) AS INTEGER) - 1) / 3) + 1 AS quarter
FROM dates;

CREATE UNIQUE INDEX idx_dim_date_key ON dim_date(date_key);

CREATE TABLE dim_member AS
SELECT ROW_NUMBER() OVER (ORDER BY beneficiary_id) AS member_key,
       beneficiary_id, birth_date, death_date, sex, race, state, county_code,
       esrd_indicator, part_a_coverage_months, part_b_coverage_months,
       hmo_coverage_months, part_d_coverage_months
FROM beneficiaries;

CREATE UNIQUE INDEX idx_dim_member_key ON dim_member(member_key);
CREATE UNIQUE INDEX idx_dim_member_id ON dim_member(beneficiary_id);

CREATE TABLE dim_provider AS
SELECT ROW_NUMBER() OVER (ORDER BY provider_id) AS provider_key,
       provider_id, provider_name, specialty, provider_type, state
FROM providers;

CREATE UNIQUE INDEX idx_dim_provider_key ON dim_provider(provider_key);
CREATE UNIQUE INDEX idx_dim_provider_id ON dim_provider(provider_id);

CREATE TABLE fact_claim AS
WITH claims AS (
    SELECT claim_id, 'inpatient' AS claim_type, beneficiary_id, provider_id,
           claim_start_date AS service_date, diagnosis_related_group AS drg_code
    FROM inpatient_claims
    UNION ALL
    SELECT claim_id, 'outpatient', beneficiary_id, provider_id, claim_start_date, NULL
    FROM outpatient_claims
    UNION ALL
    SELECT claim_id, 'carrier', beneficiary_id, provider_id, claim_start_date, NULL
    FROM carrier_claims
)
SELECT c.claim_id || '|' || c.claim_type AS claim_key,
       c.claim_id, c.claim_type,
       CAST(strftime('%Y%m%d', c.service_date) AS INTEGER) AS service_date_key,
       m.member_key, p.provider_key, c.drg_code,
       a.submitted_date, a.received_date, a.adjudicated_date, a.payment_date,
       a.billed_amount, a.allowed_amount, a.paid_amount, a.member_responsibility_amount,
       a.adjudication_status, a.denial_reason_code, a.source_transaction,
       a.remittance_transaction, a.submission_type, a.appeal_indicator,
       l.is_injected_signal, l.injected_pattern,
       CAST(julianday(a.adjudicated_date) - julianday(a.received_date) AS INTEGER) AS adjudication_days
FROM claims c
JOIN dim_member m ON c.beneficiary_id = m.beneficiary_id
JOIN dim_provider p ON c.provider_id = p.provider_id
JOIN claim_adjudication a ON c.claim_id = a.claim_id AND c.claim_type = a.claim_type
JOIN claim_integrity_labels l ON c.claim_id = l.claim_id AND c.claim_type = l.claim_type;

CREATE UNIQUE INDEX idx_fact_claim_key ON fact_claim(claim_key);
CREATE INDEX idx_fact_claim_date ON fact_claim(service_date_key);
CREATE INDEX idx_fact_claim_member ON fact_claim(member_key);
CREATE INDEX idx_fact_claim_provider ON fact_claim(provider_key);

CREATE TABLE bridge_claim_diagnosis AS
SELECT cd.claim_id || '|' || cd.claim_type AS claim_key,
       cd.diagnosis_code, cd.diagnosis_sequence
FROM claim_diagnoses cd;

CREATE INDEX idx_bridge_claim_diagnosis ON bridge_claim_diagnosis(claim_key);

CREATE TABLE fact_claim_procedure AS
SELECT cp.claim_id || '|' || cp.claim_type AS claim_key,
       cp.procedure_code, cp.procedure_sequence, cp.line_charge_amount
FROM claim_procedures cp;

CREATE INDEX idx_fact_claim_procedure ON fact_claim_procedure(claim_key);
"""


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Warehouse not found. Run etl/load_data.py first.")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
        claims = conn.execute("SELECT COUNT(*) FROM fact_claim").fetchone()[0]
        members = conn.execute("SELECT COUNT(*) FROM dim_member").fetchone()[0]
        providers = conn.execute("SELECT COUNT(*) FROM dim_provider").fetchone()[0]
        conn.commit()
        conn.execute("VACUUM")
    print(f"Dimensional layer ready: {claims:,} claims, {members:,} members, {providers:,} providers")


if __name__ == "__main__":
    main()
