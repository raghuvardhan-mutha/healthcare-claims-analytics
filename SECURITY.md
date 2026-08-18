# Security Policy

## Scope

This repository is a portfolio-grade analytics reference implementation using synthetic data. It is not approved for real patient data, protected health information (PHI), production claims, or confidential company information.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, API keys, or sensitive information. Report a suspected vulnerability privately to the repository owner through the contact method listed on the owner's GitHub profile.

Include:

- A concise description of the issue
- The affected file or workflow
- Reproduction steps using synthetic data only
- Potential impact
- A suggested mitigation, if available

## Secrets

- Store `OPENAI_API_KEY` only in a local `.env` file excluded by Git or in GitHub Actions secrets.
- Never commit keys, tokens, passwords, or connection strings.
- If a secret is exposed, revoke it immediately, remove it from Git history, and create a replacement.

## AI and SQL safety model

The assistant uses layered controls: an approved semantic layer, structured planning, SQL AST validation, SELECT-only execution, a read-only SQLite connection, a five-second query timeout, and a 200-row result cap.

These controls reduce risk but do not make the application suitable for production healthcare workloads. A production deployment would also require authenticated access, authorization, audit logs, monitoring, rate limiting, data-loss prevention, vendor review, and organization-approved HIPAA and data-processing controls.

## Supported version

Security updates apply to the latest commit on `main`.
