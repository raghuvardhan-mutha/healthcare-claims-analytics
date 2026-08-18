"""Run the complete local analytics pipeline from one command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STEPS = [
    ("Generate deterministic synthetic claims", ROOT / "etl" / "generate_data.py"),
    ("Load and validate the SQLite warehouse", ROOT / "etl" / "load_data.py"),
    ("Build the dimensional star schema", ROOT / "etl" / "build_star_schema.py"),
    ("Export Snowflake-ready dimensional files", ROOT / "etl" / "export_star_schema.py"),
    ("Build dashboard-ready data marts", ROOT / "etl" / "build_data_marts.py"),
    ("Render dashboard previews", ROOT / "visualizations" / "generate_dashboard_previews.py"),
]


def main() -> None:
    for label, script in STEPS:
        print(f"\n==> {label}")
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
