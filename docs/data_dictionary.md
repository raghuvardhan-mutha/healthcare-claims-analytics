# Data Dictionary

All records are synthetic. The model is inspired by common Medicare claims concepts and is not a copy of an official CMS file layout.

| Table | Grain | Primary key | Purpose |
|---|---|---|---|
| `beneficiaries` | One row per beneficiary | `beneficiary_id` | Demographics and coverage-month attributes |
| `chronic_conditions` | One row per beneficiary and condition | `beneficiary_id`, `condition_name` | Synthetic chronic-condition flags |
| `providers` | One row per provider | `provider_id` | Provider name, specialty, type, state, and seeded evaluation flag |
| `inpatient_claims` | One row per inpatient claim | `claim_id` | Admission, discharge, DRG, payment, charge, deductible, and status |
| `outpatient_claims` | One row per outpatient claim | `claim_id` | Service dates, payment, charge, deductible, and status |
| `carrier_claims` | One row per professional claim | `claim_id` | Service dates, payment, processing indicator, and status |
| `prescription_drug_events` | One row per pharmacy event | `event_id` | NDC-style drug event, supply, total cost, and patient payment |
| `diagnosis_codes` | One row per diagnosis code | `diagnosis_code` | Simplified diagnosis reference dimension |
| `procedure_codes` | One row per procedure code | `procedure_code` | CPT/HCPCS-style procedure reference and baseline amount |
| `drug_codes` | One row per drug code | `drug_code` | NDC-style drug reference, class, and generic indicator |
| `claim_diagnoses` | One row per claim diagnosis sequence | `claim_id`, `claim_type`, `diagnosis_sequence` | Many-to-many bridge from claims to diagnoses |
| `claim_procedures` | One row per claim procedure sequence | `claim_id`, `claim_type`, `procedure_sequence` | Many-to-many bridge from claims to procedures and line charges |
| `claim_adjudication` | One row per claim | `claim_id`, `claim_type` | Synthetic 837-to-835 submission, adjudication, payment, denial, and appeal lifecycle |
| `claim_integrity_labels` | One row per claim | `claim_id`, `claim_type` | Ground-truth label for deliberately injected synthetic review signals |

## Adjudication fields

| Column | Description |
|---|---|
| `submitted_date` | Synthetic date the claim was submitted |
| `received_date` | Synthetic payer receipt date |
| `adjudicated_date` | Synthetic adjudication completion date |
| `payment_date` | Payment date when applicable |
| `billed_amount` | Provider-billed amount |
| `allowed_amount` | Synthetic allowed amount after adjudication |
| `paid_amount` | Synthetic payer-paid amount |
| `member_responsibility_amount` | Difference assigned to member responsibility |
| `adjudication_status` | Paid, Denied, Pending, or Appealed |
| `denial_reason_code` | Synthetic CARC-style reason code for denied claims |
| `source_transaction` | Synthetic `837I` or `837P` source indicator |
| `remittance_transaction` | Synthetic `835` indicator when adjudicated |
| `submission_type` | Original or replacement submission |
| `appeal_indicator` | Whether the claim follows the synthetic appeal path |

## Dimensional analytics layer

| Table | Grain |
|---|---|
| `dim_date` | One row per claim service date |
| `dim_member` | One row per synthetic beneficiary |
| `dim_provider` | One row per synthetic provider |
| `fact_claim` | One row per claim across inpatient, outpatient, and carrier sources |
| `bridge_claim_diagnosis` | One row per claim-diagnosis sequence |
| `fact_claim_procedure` | One row per claim-procedure sequence |

## Core metric definitions

| Metric | Definition |
|---|---|
| Denial rate | Denied claims divided by all claims in the selected population |
| Service duration | Claim end date minus claim start date; not adjudication turnaround time |
| Potential unbundling | Outpatient claim containing three or more procedure lines in this demonstration rule |
| Potential duplicate group | Two or more carrier claim IDs with the same beneficiary, provider, procedure, and service date |
| DRG payment outlier | Inpatient paid amount greater than 1.5 times the mean for the same DRG |
| 30-day readmission signal | Admission occurring from 0 through 30 days after the beneficiary's previous discharge |
| Cost-versus-peer ratio | Provider mean outpatient payment divided by the mean of provider averages in the same specialty |

## Payment-integrity score

The demonstration score is intentionally explainable:

```text
2 × unbundled claims
+ 3 × duplicate groups
+ 10 × max(cost-versus-peer ratio − 1, 0)
```

The weights prioritize duplicate groups over line-count signals. In production, weights and thresholds would require historical labels, validation, governance, and review for bias and false positives.
