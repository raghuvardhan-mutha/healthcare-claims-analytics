"""Validate and constrain model-generated SQLite queries before execution."""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp


class UnsafeQueryError(ValueError):
    """Raised when generated SQL violates the read-only analytics policy."""


@dataclass(frozen=True)
class SQLGuard:
    allowed_tables: dict[str, list[str]]
    row_limit: int = 200

    def validate(self, sql: str) -> str:
        candidate = sql.strip().rstrip(";").strip()
        if not candidate:
            raise UnsafeQueryError("The model returned an empty query.")

        try:
            statements = sqlglot.parse(candidate, read="sqlite")
        except sqlglot.errors.ParseError as exc:
            raise UnsafeQueryError("The generated SQL could not be parsed.") from exc

        if len(statements) != 1:
            raise UnsafeQueryError("Only one SQL statement is allowed.")

        statement = statements[0]
        if not isinstance(statement, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
            raise UnsafeQueryError("Only SELECT queries and read-only CTEs are allowed.")

        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.Command,
            exp.Transaction,
        )
        if any(statement.find(node_type) is not None for node_type in forbidden):
            raise UnsafeQueryError("The query contains a prohibited operation.")

        cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
        referenced_tables = {
            table.name.lower()
            for table in statement.find_all(exp.Table)
            if table.name.lower() not in cte_names
        }
        unknown_tables = referenced_tables - set(self.allowed_tables)
        if unknown_tables:
            raise UnsafeQueryError(f"Unapproved table(s): {', '.join(sorted(unknown_tables))}.")

        approved_columns = {
            column.lower()
            for columns in self.allowed_tables.values()
            for column in columns
        }
        aliases = {alias.alias.lower() for alias in statement.find_all(exp.Alias) if alias.alias}
        unknown_columns = {
            column.name.lower()
            for column in statement.find_all(exp.Column)
            if column.name != "*"
            and column.name.lower() not in approved_columns
            and column.name.lower() not in aliases
        }
        if unknown_columns:
            raise UnsafeQueryError(f"Unapproved column(s): {', '.join(sorted(unknown_columns))}.")

        normalized = statement.sql(dialect="sqlite")
        return f"SELECT * FROM ({normalized}) AS approved_result LIMIT {self.row_limit}"
