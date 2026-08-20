# Power BI Desktop project

This folder contains a source-control-friendly Power BI Project (`.pbip`) for the portfolio demo. Its default Import-mode model reads the six small, synthetic data marts published in this public repository, so a reviewer can open and refresh it without a Snowflake account or password.

The project includes six reporting tables, 17 DAX measures, five named report pages, a theme, and a visual build specification. The separate [`../snowflake/`](../snowflake/) folder retains the dimensional Snowflake deployment path for environments where credentials are available.

## Open the demo

1. Download and extract the complete repository outside a OneDrive-synced folder.
2. Open `HealthcareClaimsAnalytics.pbip` in current Power BI Desktop on Windows.
3. If Power BI asks for access to `raw.githubusercontent.com`, choose **Anonymous** and set the privacy level to **Public**. No username or password is required.
4. Select **Refresh** to load the six public synthetic marts.
5. Import `healthcare_claims_theme.json` from **View → Themes → Browse for themes** if the theme is not already active.
6. Use `report_build_spec.md` when reviewing or refining the page layouts.

The demo intentionally uses aggregated marts rather than patient- or claim-level records. This keeps the download small and makes the public Power BI review path independent of Snowflake credentials.

## Snowflake deployment

For a credentialed deployment, run the files in [`../snowflake/`](../snowflake/) and validate them with `03_quality_checks.sql`. The Snowflake model is an optional deployment target; it is not required to open this PBIP demo.

The repository validates the PBIP/PBIR JSON structure, model object names, table definitions, and measures in CI. Final rendering still requires Power BI Desktop because it is not available on the Linux CI runner.
