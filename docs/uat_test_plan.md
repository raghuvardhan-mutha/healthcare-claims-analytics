# User acceptance test plan

| ID | Scenario | Expected result | Current status |
|---|---|---|---|
| UAT-01 | Run `python run_pipeline.py` from a clean checkout | Pipeline refreshes the warehouse, star schema, marts, and previews | Passed |
| UAT-02 | Run `python -m pytest -q` | All automated tests pass | Passed |
| UAT-03 | Execute Snowflake setup/load/quality scripts | Six model tables load; validation queries return zero violations | Requires Snowflake account |
| UAT-04 | Open the `.pbip` and refresh the public GitHub marts | Six model tables load without Snowflake credentials | Requires Power BI Desktop |
| UAT-05 | Compare Power BI Total Claims and Total Paid with validation log | Values reconcile for the same build seed | Pending UAT-04 |
| UAT-06 | Review month, status, specialty, and provider visuals | Published mart values display consistently | Pending UAT-04 |
| UAT-07 | Review the payment-integrity provider table | Signals display without language asserting fraud | Pending UAT-04 |
| UAT-08 | Ask a built-in Streamlit question without an API key | Approved answer, result data, and SQL display successfully | Passed |
| UAT-09 | Submit unsafe or non-SELECT SQL through assistant validation | Request is rejected before database execution | Passed |
| UAT-10 | Build and run the Docker image | Health endpoint responds and Streamlit loads | Manual deployment check |

Record tester, date, environment, actual result, and evidence link for each scenario before a production-style demonstration. UAT-04 through UAT-07 require Power BI Desktop on Windows; only UAT-03 requires a configured Snowflake account.
