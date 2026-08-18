# ETL Validation Log

## Row counts (source CSV -> target table)
- `diagnosis_codes`: source=15 | loaded=15 | **OK**
- `procedure_codes`: source=15 | loaded=15 | **OK**
- `drug_codes`: source=10 | loaded=10 | **OK**
- `beneficiaries`: source=5,000 | loaded=5,000 | **OK**
- `chronic_conditions`: source=50,000 | loaded=50,000 | **OK**
- `providers`: source=400 | loaded=400 | **OK**
- `inpatient_claims`: source=3,000 | loaded=3,000 | **OK**
- `outpatient_claims`: source=12,000 | loaded=12,000 | **OK**
- `carrier_claims`: source=25,122 | loaded=25,122 | **OK**
- `prescription_drug_events`: source=18,000 | loaded=18,000 | **OK**
- `claim_diagnoses`: source=40,122 | loaded=40,122 | **OK**
- `claim_procedures`: source=37,394 | loaded=37,394 | **OK**

## Referential integrity checks
- Inpatient claims with no matching beneficiary: **PASS**
- Outpatient claims with no matching provider: **PASS**
- Carrier claims with negative payment amount: **PASS**
- Claim diagnoses referencing unknown diagnosis codes: **PASS**

## Summary
- Total claims loaded: **40,122** (3,000 inpatient, 12,000 outpatient, 25,122 carrier)
- Data quality compliance: **100%**