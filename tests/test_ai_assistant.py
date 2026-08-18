from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ai import ClaimsAssistant, MissingAPIKeyError


def build_test_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE providers (
                provider_id TEXT PRIMARY KEY, provider_name TEXT, specialty TEXT,
                provider_type TEXT, state TEXT, npi_flag_suspicious INTEGER
            );
            CREATE TABLE inpatient_claims (
                claim_id TEXT PRIMARY KEY, beneficiary_id TEXT, provider_id TEXT,
                claim_start_date TEXT, claim_end_date TEXT, admission_date TEXT,
                discharge_date TEXT, diagnosis_related_group TEXT,
                claim_payment_amount REAL, total_charge_amount REAL,
                deductible_amount REAL, claim_status TEXT
            );
            INSERT INTO providers VALUES ('P1', 'Example Provider', 'Cardiology', 'Group', 'MA', 0);
            INSERT INTO inpatient_claims VALUES (
                'I1', 'B1', 'P1', '2023-01-01', '2023-01-02', '2023-01-01',
                '2023-01-02', '101', 125.0, 200.0, 10.0, 'Paid'
            );
            """
        )


def test_free_form_question_requires_key(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    build_test_db(db)
    assistant = ClaimsAssistant(api_key=None, db_path=db)
    with pytest.raises(MissingAPIKeyError):
        assistant.ask("How much was paid?")


def test_curated_questions_are_available() -> None:
    assistant = ClaimsAssistant(api_key=None)
    assert len(assistant.curated_questions) >= 4
    assert all(question.endswith(("?", ".")) for question in assistant.curated_questions)


class FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class FakeResponses:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return FakeResponse(
                json.dumps(
                    {
                        "sql": "SELECT specialty, COUNT(*) AS providers FROM providers GROUP BY specialty",
                        "chart_type": "bar",
                        "x_axis": "specialty",
                        "y_axis": "providers",
                    }
                )
            )
        return FakeResponse("Cardiology has one synthetic provider in this test result.")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_free_form_question_uses_structured_plan_and_read_only_query(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    build_test_db(db)
    client = FakeClient()
    assistant = ClaimsAssistant(client=client, db_path=db)

    result = assistant.ask("Count providers by specialty")

    assert result.rows == [{"specialty": "Cardiology", "providers": 1}]
    assert result.chart_type == "bar"
    assert result.source == "openai"
    assert client.responses.calls[0]["text"]["format"]["type"] == "json_schema"
    assert client.responses.calls[0]["store"] is False
    assert client.responses.calls[1]["store"] is False
