# KPI catalog

| KPI | Definition | Grain / filters | Owner | Guardrail |
|---|---|---|---|---|
| Total Claims | Count of claim fact rows | Service date, type, provider, member | Claims operations | Duplicate IDs are retained only when deliberately generated and distinguished by claim key/type |
| Total Billed | Sum of billed amount | Claim grain | Finance | Synthetic amount; not submitted charges from a real payer |
| Total Allowed | Sum of allowed amount | Claim grain | Finance | Must be less than or equal to billed |
| Total Paid | Sum of paid amount | Claim grain | Finance | Must be less than or equal to allowed |
| Denied Claims | Claims with adjudication status = Denied | Claim grain | Claims operations | Status-based, not a final appeal outcome |
| Denial Rate | Denied Claims / Total Claims | Current report filter context | Claims operations | Use minimum-volume context for provider comparison |
| Appeal Rate | Appeal-indicator claims / Total Claims | Current report filter context | Claims operations | Indicator is synthetic and does not imply success |
| Avg Adjudication Days | Average days from received to adjudicated | Claim grain | Claims operations | Excludes no rows in the synthetic model |
| Payment Ratio | Total Paid / Total Billed | Current report filter context | Finance | Not a contract compliance measure |
| Review Signal Rate | Injected review-signal claims / Total Claims | Current report filter context | Payment integrity | Prioritization signal only; never label as fraud |

Power BI measure definitions are versioned in `powerbi/HealthcareClaimsAnalytics.SemanticModel/model.bim`. SQL implementations and reconciliation checks are in `sql/` and `snowflake/03_quality_checks.sql`.
