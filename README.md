# Healthcare Claims Analytics Platform

An end-to-end healthcare claims analytics project: a normalized data model,
Python ETL pipeline, 30+ SQL analytics queries, and dashboard-ready data
marts covering claims operations, financials, provider performance, patient
population health, and payment-integrity (fraud) analytics.

Built as a portfolio project modeled on CMS's DE-SynPUF Medicare claims file
structure, and on real claims-analytics work I do as a Data Analyst on
United Health Group's Claims & Payment Integrity team — including a
window-function-based unbundled/duplicate-billing detection approach adapted
from an actual investigation I ran there.

## Why this project

Most portfolio projects stop at "load a CSV, make a chart." This one is
built the way a claims analytics team actually works: a proper relational
schema instead of one flat table, ETL with source-to-target validation
(not just a happy-path load), SQL organized by business domain the way a
BI team would hand it off, and a fraud-detection module that mirrors a
real payment-integrity workflow rather than a generic anomaly-detection demo.

## Data note

This repo uses **synthetic data generated to match the structure of CMS's
DE-SynPUF** (Data Entrepreneurs' Synthetic Public Use Files) — same table
shapes, realistic ICD/CPT/NDC-style codes, realistic dollar ranges — rather
than the actual CMS files, so the project can be run and reviewed without a
data use agreement or a multi-GB download. A small number of claims (~2%)
have deliberately injected fraud patterns (unbundled billing, duplicate
claims, upcoded DRGs) so the payment-integrity SQL has real signal to catch.
See `etl/generate_data.py` for exactly how each pattern is injected.

## Architecture

```
CSV generation (synthetic, DE-SynPUF-shaped)
        │
        ▼
Python ETL  ──►  SQLite (portable; schema also runs unmodified on PostgreSQL)
        │              │
        │              ▼
        │        30+ SQL analytics queries (5 domains)
        │              │
        ▼              ▼
  Validation log   Pre-aggregated data marts ──► Power BI / dashboard visuals
```

## Data model

12 tables, normalized around Medicare's real claim-type split (inpatient /
outpatient / carrier / Part D), with reference tables for diagnosis,
procedure, and drug codes, and bridge tables for the claim↔diagnosis and
claim↔procedure many-to-many relationships:

`beneficiaries` · `chronic_conditions` · `providers` · `inpatient_claims` ·
`outpatient_claims` · `carrier_claims` · `prescription_drug_events` ·
`diagnosis_codes` · `procedure_codes` · `drug_codes` · `claim_diagnoses` ·
`claim_procedures`

Full DDL: [`sql/01_schema.sql`](sql/01_schema.sql)

## SQL analytics (5 domains, 30 queries)

| File | Domain | Highlights |
|---|---|---|
| [`sql/02_claims_analytics.sql`](sql/02_claims_analytics.sql) | Claims operations | Denial rates by specialty/state, claim aging, monthly volume trend |
| [`sql/03_financial_analytics.sql`](sql/03_financial_analytics.sql) | Financial | Charge-to-paid ratio, cost per chronic condition, MoM revenue trend |
| [`sql/04_provider_analytics.sql`](sql/04_provider_analytics.sql) | Provider performance | Cost-per-claim vs. specialty peer average, utilization outliers |
| [`sql/05_patient_analytics.sql`](sql/05_patient_analytics.sql) | Patient population | Comorbidity burden, utilization by condition count, 30-day readmissions |
| [`sql/06_fraud_detection.sql`](sql/06_fraud_detection.sql) | Payment integrity | Unbundling & duplicate-billing detection via window functions, composite provider risk score |

The fraud-detection queries use `PARTITION BY` / `ROW_NUMBER()` /
`COUNT() OVER()` to find claims sharing beneficiary + provider + date of
service billed as multiple line items or duplicate claim IDs — the same
technique behind a real unbundling pattern I found in production claims
data, which led to a systematic billing edit and $1.2M in recovered revenue.

## Dashboards

Six dashboard pages, each backed by a pre-aggregated data mart in
`dashboards/data_marts/` and previewed as a static chart in `dashboards/`:

1. **Executive Summary** — monthly paid claims & volume trend
2. **Claims** — claim status mix (paid/denied/pending/appealed)
3. **Financial** — total paid by specialty
4. **Provider** — top providers by paid amount
5. **Patient** — chronic condition prevalence
6. **Fraud / Payment Integrity** — provider risk ranking (unbundling signal)

The data marts are plain CSVs designed to drop straight into Power BI
(or Tableau/Looker) — each is already grouped/aggregated at the grain the
dashboard page needs, so building the `.pbix` on top is mostly
visual layout rather than data modeling.

## Project structure

```
healthcare-claims-analytics/
├── README.md
├── sql/
│   ├── 01_schema.sql              # DDL — 12-table normalized schema
│   ├── 02_claims_analytics.sql
│   ├── 03_financial_analytics.sql
│   ├── 04_provider_analytics.sql
│   ├── 05_patient_analytics.sql
│   └── 06_fraud_detection.sql
├── etl/
│   ├── generate_data.py           # synthetic data generator (DE-SynPUF-shaped)
│   └── load_data.py               # loads CSVs -> DB, runs validation checks
├── data/                          # generated CSVs + claims_analytics.db
├── dashboards/
│   ├── 01_executive_summary.png ... 06_fraud_risk.png
│   └── data_marts/                # pre-aggregated CSVs for BI tools
└── docs/
    └── etl_validation_log.md      # source-to-target row counts, DQ checks
```

## How to run it

```bash
# 1. Install dependencies
pip install faker pandas matplotlib

# 2. Generate the synthetic dataset (writes CSVs to data/)
python etl/generate_data.py

# 3. Build schema + load into SQLite, run validation checks
python etl/load_data.py

# 4. Explore the analytics
sqlite3 data/claims_analytics.db
sqlite> .read sql/06_fraud_detection.sql
```

To point this at PostgreSQL instead of SQLite: run `sql/01_schema.sql`
against your Postgres instance, then swap the `sqlite3` connection in
`etl/load_data.py` for `psycopg2` (the schema and all analytics SQL are
already written in standard, Postgres-compatible SQL).

## Dataset scale

~5,000 beneficiaries · 400 providers · ~40,000 claims (inpatient/outpatient/
carrier) · 18,000 prescription drug events · 3 years of claim history
(2021–2023).

## Stack

Python (pandas, Faker) · SQL (window functions, CTEs) · SQLite/PostgreSQL ·
Power BI-ready data marts · Git

## About this project

Built by Raghu Vardhan Mutha, Data Analyst — Claims & Payment Integrity at
United Health Group. This project reflects the same problem space I work in
day to day (claims lifecycle analytics, denial/appeal trends, provider
performance, payment-integrity investigation), rebuilt end-to-end on
synthetic data for a public portfolio.
