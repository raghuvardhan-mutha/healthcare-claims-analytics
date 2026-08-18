# Project Walkthrough

This guide provides a concise path for reviewers, hiring teams, and contributors to understand the project.

## One-minute overview

The platform generates deterministic synthetic Medicare-style claims, loads them into a normalized SQLite warehouse, validates the data, produces reusable SQL analysis and BI-ready marts, and exposes a guarded natural-language analytics assistant. The focus is healthcare operational and financial decision support—not clinical decision-making.

## Recommended review path

1. Read the [executive summary](../README.md#executive-summary).
2. Review the [dashboard gallery](../README.md#dashboard-gallery).
3. Inspect the [schema](../sql/01_schema.sql) and [data dictionary](data_dictionary.md).
4. Open one SQL domain, such as [payment integrity](../sql/06_fraud_detection.sql).
5. Review the [AI guard](../ai/sql_guard.py) and [semantic layer](../ai/semantic_layer.json).
6. Run the pipeline and tests.
7. Launch the Streamlit application and try a built-in question.

## Business scenario

A healthcare analytics team needs repeatable visibility into:

- Claim volumes and status distribution
- Denials and appeals
- Paid-amount and reimbursement trends
- Provider performance versus specialty peers
- Utilization and readmission signals
- Potential duplicate, unbundling, and payment-outlier patterns

The project creates one reusable analytical foundation for those questions.

## Technical demonstration

```bash
pip install -r requirements.txt
python run_pipeline.py
python -m pytest -q
streamlit run streamlit_app.py
```

Expected pipeline stages:

1. Generate deterministic synthetic files.
2. Build and validate the SQLite warehouse.
3. Create six dashboard-ready marts.
4. Render six dashboard previews.

## AI demonstration

Start with a built-in question, which does not require an API key:

> Which specialties have the highest denial rates?

The application displays:

- A concise analytical answer
- A chart when the result is suitable
- The complete result table
- The exact approved SQL
- The answer mode and row limit

For a free-form question, configure `OPENAI_API_KEY` privately. The assistant will plan a structured query, validate it against the semantic layer, execute it read-only, and explain only the returned evidence.

## Interview-ready talking points

- **Problem:** Claims analysis is often slowed by fragmented data, repeated manual queries, and inconsistent metric definitions.
- **Approach:** Build a reproducible claims warehouse, reusable SQL domains, validated marts, and a constrained self-service AI layer.
- **Quality:** Use deterministic generation, source-to-target checks, business-rule validation, automated tests, and CI.
- **Payment integrity:** Prioritize transparent review signals while avoiding unsupported fraud conclusions.
- **AI governance:** Constrain the model with approved tables and metrics, validate SQL, execute read-only, and show the query to the user.
- **Limitation:** Synthetic results demonstrate the method; real operational decisions require policy, contract, coding, clinical, and medical-record evidence.

## Suggested next extension

The highest-value portfolio extension is a native Power BI or Tableau workbook built on `dashboards/data_marts/`, followed by a hosted Streamlit demo. Those additions would make the existing analytical and AI work directly explorable by recruiters.
