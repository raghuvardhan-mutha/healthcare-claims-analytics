# Snowflake Deployment

This folder deploys the verified dimensional layer to Snowflake using an internal stage and `COPY INTO`.

## Build the export files

```bash
python run_pipeline.py
```

The generated CSV files are written to `data/snowflake/` and remain excluded from Git.

## Deploy

Run the scripts in order using Snowsight or SnowSQL:

1. `00_setup.sql`
2. `01_star_schema.sql`
3. Upload the files using the `PUT` command documented in `02_load.sql`.
4. `02_load.sql`
5. `03_quality_checks.sql`

The warehouse defaults to `XSMALL` and auto-suspends after 60 seconds to limit portfolio costs. Snowflake standard-table key constraints document relationships but are not enforced; the quality-check script explicitly tests key integrity before BI publication.
