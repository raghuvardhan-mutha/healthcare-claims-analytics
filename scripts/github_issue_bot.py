"""Answer labeled GitHub Issues using the guarded claims assistant."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

from ai import ClaimsAssistant, MissingAPIKeyError


def load_event() -> dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is not set.")
    return json.loads(Path(event_path).read_text(encoding="utf-8"))


def is_ai_question(issue: dict) -> bool:
    labels = {item.get("name", "").lower() for item in issue.get("labels", [])}
    return "ai-question" in labels or issue.get("title", "").lower().startswith("[ai question]")


def post_comment(repository: str, issue_number: int, body: str) -> None:
    token = os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 201:
            raise RuntimeError(f"GitHub returned HTTP {response.status}.")


def format_comment(result) -> str:
    preview = result.rows[:10]
    if preview:
        columns = result.columns
        header = "| " + " | ".join(columns) + " |"
        divider = "| " + " | ".join(["---"] * len(columns)) + " |"
        rows = [
            "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
            for row in preview
        ]
        table = "\n".join([header, divider, *rows])
    else:
        table = "_No matching rows._"

    return (
        "## AI claims analysis\n\n"
        f"{result.answer}\n\n"
        f"{table}\n\n"
        "<details><summary>Approved read-only SQL</summary>\n\n"
        f"```sql\n{result.sql}\n```\n\n"
        "</details>\n\n"
        "> All data is synthetic. Payment-integrity signals identify candidates for review and do not prove fraud."
    )


def main() -> int:
    event = load_event()
    issue = event.get("issue", {})
    if not is_ai_question(issue):
        print("Issue is not labeled or titled as an AI question; nothing to do.")
        return 0

    repository = os.environ["GITHUB_REPOSITORY"]
    question = f"{issue.get('title', '')}\n\n{issue.get('body') or ''}".strip()
    try:
        result = ClaimsAssistant().ask(question)
        comment = format_comment(result)
    except MissingAPIKeyError:
        comment = (
            "The AI assistant is ready, but this repository has no `OPENAI_API_KEY` Actions secret yet. "
            "A repository maintainer can add it under **Settings → Secrets and variables → Actions**."
        )
    except Exception as exc:
        print(f"Assistant error: {type(exc).__name__}: {exc}", file=sys.stderr)
        comment = "The AI analysis could not be completed safely. Please check the Actions log and try again."

    post_comment(repository, int(issue["number"]), comment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
