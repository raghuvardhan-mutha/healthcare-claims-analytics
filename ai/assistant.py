"""OpenAI-powered natural-language interface to the synthetic claims data."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from .curated_questions import CURATED_QUESTIONS
from .database import DEFAULT_DB_PATH, execute_read_only
from .sql_guard import SQLGuard


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_LAYER_PATH = ROOT / "ai" / "semantic_layer.json"


class MissingAPIKeyError(RuntimeError):
    """Raised when a free-form question is asked without an API key."""


@dataclass(frozen=True)
class ClaimsAnswer:
    question: str
    answer: str
    sql: str
    columns: list[str]
    rows: list[dict[str, object]]
    chart_type: str = "none"
    x_axis: str | None = None
    y_axis: str | None = None
    source: str = "openai"


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "chart_type": {"type": "string", "enum": ["bar", "line", "none"]},
        "x_axis": {"type": ["string", "null"]},
        "y_axis": {"type": ["string", "null"]},
    },
    "required": ["sql", "chart_type", "x_axis", "y_axis"],
    "additionalProperties": False,
}


class ClaimsAssistant:
    """Plan safe SQL, execute it read-only, and explain the result."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        db_path: Path = DEFAULT_DB_PATH,
        client: OpenAI | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6")
        self.db_path = db_path
        self.semantic_layer = json.loads(SEMANTIC_LAYER_PATH.read_text(encoding="utf-8"))
        self.guard = SQLGuard(self.semantic_layer["tables"])
        self.client = client

    @property
    def curated_questions(self) -> list[str]:
        return list(CURATED_QUESTIONS)

    def ask(self, question: str) -> ClaimsAnswer:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Please enter a healthcare analytics question.")

        if clean_question in CURATED_QUESTIONS:
            return self._run_curated(clean_question)

        if not self.api_key and self.client is None:
            raise MissingAPIKeyError(
                "Free-form questions require OPENAI_API_KEY. The built-in example questions work without a key."
            )

        plan = self._plan(clean_question)
        approved_sql = self.guard.validate(plan["sql"])
        columns, rows = execute_read_only(approved_sql, self.db_path)
        answer = self._explain(clean_question, approved_sql, columns, rows)
        x_axis = plan.get("x_axis") if plan.get("x_axis") in columns else None
        y_axis = plan.get("y_axis") if plan.get("y_axis") in columns else None
        chart_type = plan.get("chart_type", "none") if x_axis and y_axis else "none"
        return ClaimsAnswer(
            question=clean_question,
            answer=answer,
            sql=approved_sql,
            columns=columns,
            rows=rows,
            chart_type=chart_type,
            x_axis=x_axis,
            y_axis=y_axis,
        )

    def _client(self) -> OpenAI:
        if self.client is not None:
            return self.client
        self.client = OpenAI(api_key=self.api_key, timeout=30.0)
        return self.client

    def _plan(self, question: str) -> dict[str, Any]:
        instructions = (
            "You are a healthcare claims analytics SQL planner. Generate exactly one read-only SQLite SELECT query. "
            "Use only the supplied tables and columns. Never use PRAGMA, ATTACH, database-changing SQL, or multiple statements. "
            "Use the metric definitions exactly. Return a chart only when two returned columns are suitable. "
            "Treat all data as synthetic and all payment-integrity patterns as review signals, never confirmed fraud."
        )
        payload = {
            "question": question,
            "semantic_layer": self.semantic_layer,
        }
        response = self._client().responses.create(
            model=self.model,
            instructions=instructions,
            input=json.dumps(payload),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "claims_sql_plan",
                    "strict": True,
                    "schema": PLAN_SCHEMA,
                }
            },
            store=False,
        )
        return json.loads(response.output_text)

    def _explain(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[dict[str, object]],
    ) -> str:
        sample = rows[:25]
        instructions = (
            "You are a healthcare analytics reviewer. Answer only from the supplied query result. "
            "Be concise, mention the most decision-useful finding, and state when the result is empty. "
            "All data is synthetic. Say 'potential payment-integrity signal' rather than confirmed fraud. "
            "Do not provide medical advice or infer facts not present in the result."
        )
        response = self._client().responses.create(
            model=self.model,
            instructions=instructions,
            input=json.dumps(
                {
                    "question": question,
                    "sql": sql,
                    "columns": columns,
                    "rows_returned": len(rows),
                    "result_sample": sample,
                },
                default=str,
            ),
            store=False,
        )
        return response.output_text.strip()

    def _run_curated(self, question: str) -> ClaimsAnswer:
        item = CURATED_QUESTIONS[question]
        approved_sql = self.guard.validate(item["sql"])
        columns, rows = execute_read_only(approved_sql, self.db_path)
        return ClaimsAnswer(
            question=question,
            answer=item["answer"],
            sql=approved_sql,
            columns=columns,
            rows=rows,
            chart_type=item["chart_type"],
            x_axis=item["x_axis"],
            y_axis=item["y_axis"],
            source="curated",
        )
