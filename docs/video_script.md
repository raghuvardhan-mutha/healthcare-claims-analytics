# Video Walkthrough Script (target: 7–8 minutes)

Record your screen (repo open in VS Code + terminal + one dashboard PNG open).
Read this as a guide, not a script to recite word-for-word — say it in your
own words, but hit every numbered beat. Bold = what to have on screen.

---

## 1. Intro (30 sec)
**Screen: README.md**

"Hi, I'm Raghu — I'm a Data Analyst on the Claims & Payment Integrity team
at United Health Group. For this walkthrough I'm showing a Healthcare Claims
Analytics project I built end-to-end: a normalized data model, an ETL
pipeline, 30-plus SQL analytics queries across five business domains, and
dashboard-ready outputs — including a fraud-detection module modeled on a
real investigation I ran at UHG."

## 2. The problem / why this project (45 sec)
**Screen: README, "Why this project" section**

"A lot of portfolio projects are one flat CSV and a chart. I wanted to show
how claims analytics actually works on a team: a real relational schema
split by claim type — inpatient, outpatient, carrier — the way Medicare
claims are actually structured, ETL with validation instead of just a
happy-path load, and SQL organized the way a BI team would hand queries off
to different stakeholders: claims ops, finance, provider network, patient
population health, and payment integrity."

## 3. Data note — be upfront (30 sec)
**Screen: README, "Data note" section**

"Quick transparency note: this uses synthetic data generated to match the
structure of CMS's DE-SynPUF file — same table shapes, realistic codes and
dollar ranges — not the real CMS data, since that needs a data use
agreement. I also deliberately seeded about 2% of claims with fraud
patterns — unbundled billing, duplicate claims, upcoded DRGs — so the
payment-integrity SQL has real signal to catch, which I'll show you."

## 4. Schema walkthrough (60–90 sec)
**Screen: sql/01_schema.sql**

"Twelve tables. Beneficiaries and providers as the core dimensions, three
claim fact tables split by claim type because that's how Medicare data is
actually organized, a prescription drug events table for Part D, reference
tables for diagnosis, procedure, and drug codes, and two bridge tables for
the many-to-many relationship between claims and diagnoses/procedures —
because a single claim can have multiple diagnosis codes attached."

*(Scroll to show the foreign keys / indexes briefly.)*

## 5. ETL + data quality (60 sec)
**Screen: etl/load_data.py, then run it live OR show docs/etl_validation_log.md**

"The ETL script loads the generated CSVs into the schema and then runs
source-to-target validation — row count reconciliation between the source
files and what actually landed in each table, plus referential integrity
checks: orphaned claims, negative payment amounts, diagnosis codes that
don't exist in the reference table. This is the validation log it produces
—" *(show docs/etl_validation_log.md)* "— 100% row-count match, all
integrity checks passing."

## 6. SQL analytics — pick 2–3 to actually explain (2 min)
**Screen: sql/04_provider_analytics.sql, Q2 (peer-outlier detection)**

"This one finds providers billing more than 30% above their specialty's
average cost per claim — a self-join pattern against a specialty benchmark
rather than a hardcoded threshold, so it adapts as the peer group changes."

**Screen: sql/06_fraud_detection.sql, Q1 and Q2**

"This is the part I'm most proud of — it's adapted from real work. At UHG I
used window functions to catch outpatient surgical claims where a provider
group was billing bundled procedure components as separate CPT codes. Here,
Query 1 does the same thing: it groups claims by beneficiary, provider, and
date of service, counts procedure line items per claim, and flags anything
with 3+ lines where you'd expect one bundled code. Query 2 catches duplicate
billing using `ROW_NUMBER()` partitioned by beneficiary/provider/procedure/
date — same claim details billed twice under different claim IDs."

*(Optional, if time: show Q4, the composite provider risk score.)*

"Query 4 combines those signals — unbundling rate and cost variance versus
peers — into a single ranked risk score per provider. That's the kind of
output that would actually go to a payment-integrity team to prioritize
which providers get audited first."

## 7. Dashboards (60 sec)
**Screen: dashboards/06_fraud_risk.png**

"This chart is built off the fraud-risk data mart — average procedure lines
per claim, by provider. The coral bars are the providers I seeded with the
unbundling pattern, navy is everyone else — you can see the detection
query cleanly separates them. I also built five other dashboard pages:
executive summary, claims status mix, financial by specialty, provider
performance, and chronic condition prevalence — each backed by its own
pre-aggregated data mart so it's a clean handoff into Power BI."

## 8. Close (20–30 sec)
**Screen: README, project structure**

"That's the project end to end — schema, ETL with validation, 30 SQL
queries across five domains, and dashboard-ready outputs, with a fraud
detection approach grounded in something I actually built and shipped at
UHG. Repo link and everything I walked through is in the README. Thanks for
watching."

---

## Recording tips
- Do 1–2 practice runs un-recorded first so the SQL explanations don't feel
  read-aloud.
- If a tool (Loom, QuickTime, OBS) lets you highlight cursor clicks, turn
  that on — it's much easier to follow along.
- Keep code font size large enough to read on a laptop screen (14pt+ in
  your editor).
- If you go over 10 minutes, cut section 6 down to just the fraud queries
  (2 and 6 are the ones that differentiate you) rather than trimming the
  intro/close.
