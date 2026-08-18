# Deployment guide

## Local Streamlit

Run `python run_pipeline.py`, then `streamlit run streamlit_app.py`. Built-in questions work without an API key; free-form questions require `OPENAI_API_KEY`.

## Docker

```bash
docker build -t healthcare-claims-analytics .
docker run --rm -p 8501:8501 --env-file .env healthcare-claims-analytics
```

Open `http://localhost:8501`. The container builds the deterministic demo warehouse before starting the app. Do not package real claims data or secrets in the image.

## Streamlit Community Cloud

Connect this GitHub repository, set `streamlit_app.py` as the entry point, and add `OPENAI_API_KEY` only if free-form questions are required. The checked-in `.streamlit/config.toml` supplies a consistent theme and headless server configuration.

## Snowflake and Power BI

Deploy Snowflake with `snowflake/README.md`, then open `powerbi/HealthcareClaimsAnalytics.pbip` and configure the four Snowflake parameters. Publish to a controlled Power BI workspace only after Desktop refresh, reconciliation, access review, and UAT are complete.

Production use additionally requires identity-based access, secrets management, audit logging, monitoring, rate limits, backup/recovery, and organizational privacy/security review.
