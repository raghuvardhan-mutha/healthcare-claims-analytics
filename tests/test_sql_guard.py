from __future__ import annotations

import pytest

from ai.sql_guard import SQLGuard, UnsafeQueryError


TABLES = {
    "claims": ["claim_id", "provider_id", "claim_payment_amount"],
    "providers": ["provider_id", "provider_name"],
}


@pytest.fixture
def guard() -> SQLGuard:
    return SQLGuard(TABLES, row_limit=25)


def test_allows_select_and_enforces_limit(guard: SQLGuard) -> None:
    sql = guard.validate("SELECT provider_id, SUM(claim_payment_amount) AS paid FROM claims GROUP BY provider_id")
    assert "LIMIT 25" in sql
    assert "approved_result" in sql


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE claims",
        "DELETE FROM claims",
        "UPDATE claims SET claim_payment_amount = 0",
        "SELECT * FROM claims; SELECT * FROM providers",
        "SELECT * FROM secret_table",
        "SELECT patient_ssn FROM claims",
    ],
)
def test_blocks_unsafe_or_unknown_sql(guard: SQLGuard, sql: str) -> None:
    with pytest.raises(UnsafeQueryError):
        guard.validate(sql)


def test_allows_read_only_cte(guard: SQLGuard) -> None:
    sql = guard.validate(
        "WITH totals AS (SELECT provider_id, SUM(claim_payment_amount) AS paid FROM claims GROUP BY provider_id) "
        "SELECT provider_id, paid FROM totals ORDER BY paid DESC"
    )
    assert "WITH totals AS" in sql
