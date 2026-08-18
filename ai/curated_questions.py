"""No-key portfolio demos that use the same guarded query path as the LLM."""

CURATED_QUESTIONS = {
    "Which specialties have the highest denial rates?": {
        "sql": """
            WITH all_claims AS (
                SELECT provider_id, claim_status FROM inpatient_claims
                UNION ALL SELECT provider_id, claim_status FROM outpatient_claims
                UNION ALL SELECT provider_id, claim_status FROM carrier_claims
            )
            SELECT p.specialty, COUNT(*) AS total_claims,
                   SUM(CASE WHEN a.claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
                   ROUND(100.0 * SUM(CASE WHEN a.claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate_pct
            FROM all_claims a JOIN providers p USING (provider_id)
            GROUP BY p.specialty ORDER BY denial_rate_pct DESC
        """,
        "answer": "This ranks specialties by denial rate and includes claim volume so reviewers can distinguish a meaningful operational pattern from a small sample.",
        "chart_type": "bar",
        "x_axis": "specialty",
        "y_axis": "denial_rate_pct"
    },
    "Which providers have the strongest payment-integrity signals?": {
        "sql": """
            WITH lines AS (
                SELECT o.provider_id, o.claim_id, COUNT(*) AS line_items
                FROM outpatient_claims o JOIN claim_procedures cp
                  ON o.claim_id = cp.claim_id AND cp.claim_type = 'outpatient'
                GROUP BY o.provider_id, o.claim_id
            )
            SELECT p.provider_id, p.provider_name, p.specialty,
                   SUM(CASE WHEN l.line_items >= 3 THEN 1 ELSE 0 END) AS potential_unbundled_claims
            FROM lines l JOIN providers p USING (provider_id)
            GROUP BY p.provider_id, p.provider_name, p.specialty
            ORDER BY potential_unbundled_claims DESC LIMIT 20
        """,
        "answer": "These providers have the most outpatient claims with three or more procedure lines. The pattern is a review signal—not proof of fraud—and requires coding and clinical validation.",
        "chart_type": "bar",
        "x_axis": "provider_id",
        "y_axis": "potential_unbundled_claims"
    },
    "Show the monthly paid-amount trend.": {
        "sql": """
            WITH all_claims AS (
                SELECT claim_start_date, claim_payment_amount FROM inpatient_claims
                UNION ALL SELECT claim_start_date, claim_payment_amount FROM outpatient_claims
                UNION ALL SELECT claim_start_date, claim_payment_amount FROM carrier_claims
            )
            SELECT strftime('%Y-%m', claim_start_date) AS month,
                   COUNT(*) AS claims, ROUND(SUM(claim_payment_amount), 2) AS total_paid
            FROM all_claims GROUP BY month ORDER BY month
        """,
        "answer": "The monthly series shows paid amount and claim volume together, making it useful for identifying seasonality and investigating unusual changes.",
        "chart_type": "line",
        "x_axis": "month",
        "y_axis": "total_paid"
    },
    "Which chronic conditions are most common?": {
        "sql": """
            SELECT condition_name,
                   SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) AS beneficiaries,
                   ROUND(100.0 * SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS prevalence_pct
            FROM chronic_conditions GROUP BY condition_name ORDER BY prevalence_pct DESC
        """,
        "answer": "This compares synthetic chronic-condition prevalence across the beneficiary population and can guide utilization or population-health drill-downs.",
        "chart_type": "bar",
        "x_axis": "condition_name",
        "y_axis": "prevalence_pct"
    }
}
