# Contributing

Thank you for considering an improvement to the Healthcare Claims & Payment Integrity Analytics Platform.

## Before opening a change

- Keep all examples synthetic. Never add PHI, real patient records, credentials, proprietary code, or confidential company data.
- Describe payment-integrity outputs as potential signals or review indicators, never confirmed fraud.
- Preserve the project's role as operational and financial decision support rather than clinical decision-making.
- Open an issue before proposing a large architectural change.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py
python -m pytest -q
```

## Pull-request checklist

- [ ] The complete pipeline runs successfully.
- [ ] All tests pass.
- [ ] New metrics have a clear definition and denominator.
- [ ] SQL remains compatible with the documented SQLite dialect.
- [ ] AI changes preserve SELECT-only execution, the semantic allowlist, timeouts, and row limits.
- [ ] Documentation and dashboard outputs are updated when behavior changes.
- [ ] No secrets, generated database files, or sensitive data are committed.

## Style

- Prefer small, focused functions and descriptive names.
- Add docstrings where the purpose is not obvious.
- Keep business terminology clear enough for an analyst, reviewer, or recruiter to follow.
- Include tests for new transformation rules, metrics, or guardrails.

By contributing, you agree that your contribution will be licensed under the repository's MIT License.
