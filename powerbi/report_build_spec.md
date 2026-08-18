# Report build specification

Use a 16:9 canvas, the included theme, a persistent `Date[Year]` / `Date[Year Month]` slicer, and cross-filtering from charts to detail tables. Page titles should include “Synthetic portfolio data”.

| Page | Required visuals | Primary fields and measures |
|---|---|---|
| Executive Summary | KPI cards, monthly paid trend, status mix, specialty ranking | Total Claims, Total Paid, Denial Rate, Average Adjudication Days, Date[Year Month], Claim[Adjudication Status], Provider[Specialty] |
| Claims & Denials | Denial-rate trend, denial-reason bars, claim-type matrix, appeal card | Denied Claims, Denial Rate, Appeal Rate, Claim[Denial Reason Code], Claim[Claim Type] |
| Financial Performance | Billed/allowed/paid trend, payment ratio, member responsibility, specialty table | Total Billed, Total Allowed, Total Paid, Payment Ratio, Member Responsibility, Paid per Claim |
| Provider Performance | Provider scatter, specialty benchmark, provider detail table | Total Claims, Total Paid, Denial Rate, Average Adjudication Days, Provider[Provider Name], Provider[Specialty] |
| Payment Integrity | Review-signal card/trend, injected-pattern bars, prioritized provider table | Review Signal Claims, Review Signal Rate, Claim[Injected Pattern], Provider[Provider Name] |

## Interaction and accessibility contract

- Use color plus labels; never rely on red/green alone.
- Show thousands separators, currency units, percentage precision, definitions, and last-refresh time.
- Keep payment-integrity language to “review signal”, “prioritize”, and “investigate”; do not label a provider or claim as fraudulent.
- Add alt text to every nondecorative visual and maintain logical tab order.
- Use drillthrough from specialty to provider and provider to claim detail; hide synthetic technical keys from report consumers.
