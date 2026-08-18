"""Export the verified dimensional layer as Snowflake- and Power BI-ready CSVs."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "claims_analytics.db"
OUT_DIR = ROOT / "data" / "snowflake"
TABLES = (
    "dim_date", "dim_member", "dim_provider", "fact_claim",
    "bridge_claim_diagnosis", "fact_claim_procedure",
)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for table in TABLES:
            cursor = conn.execute(f"SELECT * FROM {table}")
            path = OUT_DIR / f"{table}.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(cursor)
            print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
