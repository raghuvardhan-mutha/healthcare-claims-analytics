"""Read-only database access for the AI assistant."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "claims_analytics.db"


def ensure_database(db_path: Path = DEFAULT_DB_PATH) -> Path:
    """Build the deterministic demo warehouse when it is not present."""
    if db_path.exists():
        return db_path
    for script in ("generate_data.py", "load_data.py"):
        subprocess.run(
            [sys.executable, str(ROOT / "etl" / script)],
            cwd=ROOT,
            check=True,
        )
    return db_path


def execute_read_only(
    sql: str,
    db_path: Path = DEFAULT_DB_PATH,
    timeout_seconds: float = 5.0,
) -> tuple[list[str], list[dict[str, object]]]:
    """Execute validated SQL through a query-only SQLite connection."""
    path = ensure_database(db_path).resolve()
    started = time.monotonic()
    uri = f"file:{path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=timeout_seconds) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.set_progress_handler(
            lambda: int(time.monotonic() - started > timeout_seconds),
            10_000,
        )
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = [dict(row) for row in cursor.fetchall()]
    return columns, rows
