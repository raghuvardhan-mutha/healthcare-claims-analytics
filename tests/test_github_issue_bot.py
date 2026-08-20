from scripts.github_issue_bot import extract_question, is_ai_question


def test_extract_question_from_issue_template() -> None:
    issue = {
        "title": "[AI Question]",
        "body": (
            "### Analytics question\n\n"
            "Which specialties have the highest denial rates?\n\n"
            "### Data acknowledgement\n\n- [x] Synthetic data"
        ),
        "labels": [],
    }
    assert is_ai_question(issue)
    assert extract_question(issue) == "Which specialties have the highest denial rates?"


def test_extract_question_falls_back_for_unstructured_issue() -> None:
    issue = {"title": "[AI Question] Monthly trend", "body": "Show paid amount by month."}
    assert extract_question(issue) == "[AI Question] Monthly trend\n\nShow paid amount by month."
