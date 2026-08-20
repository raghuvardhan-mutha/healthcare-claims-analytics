# Report build specification

Use a 16:9 canvas, the included theme, and cross-filtering from charts to detail tables. Page titles should include “Synthetic portfolio data”.

| Page | Required visuals | Primary fields and measures |
|---|---|---|
| Executive Summary | KPI cards and monthly paid/claim trend | Total Claims, Total Paid, Paid per Claim, Monthly Summary[Month] |
| Claims & Denials | Status distribution and claim-count card | Claims Status[Claim Status], Status Claims |
| Financial Performance | Specialty paid amount and volume comparison | Specialty Financials[Specialty], Specialty Total Paid, Specialty Claims, Specialty Paid per Claim |
| Provider Performance | Provider ranking and specialty detail table | Provider Performance[Provider Name], Provider Performance[Specialty], Provider Claims, Provider Total Paid, Provider Average Paid |
| Payment Integrity | Review-signal cards and prioritized provider table | Payment Integrity[Provider Name], Review Providers, Total Potential Unbundled Claims, Total Potential Duplicate Groups, Average Risk Score |

## Interaction and accessibility contract

- Use color plus labels; never rely on red/green alone.
- Show thousands separators, currency units, percentage precision, definitions, and last-refresh time.
- Keep payment-integrity language to “review signal”, “prioritize”, and “investigate”; do not label a provider or claim as fraudulent.
- Add alt text to every nondecorative visual and maintain logical tab order.
- Keep provider identifiers available in detail tables, but use provider names and specialties in summary visuals.
