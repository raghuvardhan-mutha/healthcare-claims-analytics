# User acceptance test plan

| ID | Scenario | Expected result |
|---|---|---|
| UAT-01 | Run `python run_pipeline.py` from a clean checkout | Pipeline completes and refreshes warehouse, star schema, marts, and previews |
| UAT-02 | Run `python -m pytest -q` | All automated tests pass |
| UAT-03 | Execute Snowflake setup/load/quality scripts | Six model tables load; validation queries return zero violations |
| UAT-04 | Open the `.pbip`, set Snowflake parameters, and refresh | Four model tables load and relationships remain active |
| UAT-05 | Compare Power BI Total Claims and Total Paid with validation log | Values reconcile for the same filters and build seed |
| UAT-06 | Filter year, claim type, specialty, and provider | All intended visuals update consistently |
| UAT-07 | Select a payment-integrity pattern | Provider/claim details narrow without language asserting fraud |
| UAT-08 | Ask a built-in Streamlit question without an API key | Approved answer, result data, and SQL display successfully |
| UAT-09 | Submit unsafe or non-SELECT SQL through assistant validation | Request is rejected before database execution |
| UAT-10 | Build and run the Docker image | Health endpoint responds and Streamlit loads |

Record tester, date, environment, actual result, and evidence link for each scenario before a production-style demonstration. UAT-04 through UAT-07 require Power BI Desktop on Windows; UAT-03 requires a configured Snowflake account.
