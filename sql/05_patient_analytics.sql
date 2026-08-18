-- ============================================================================
-- PATIENT / POPULATION ANALYTICS -- demographics, chronic disease burden, utilization
-- ============================================================================

-- Q1. Age distribution of beneficiary population (as of 2023)
SELECT CASE
        WHEN (2023 - CAST(strftime('%Y', birth_date) AS INTEGER)) < 65 THEN 'Under 65'
        WHEN (2023 - CAST(strftime('%Y', birth_date) AS INTEGER)) BETWEEN 65 AND 74 THEN '65-74'
        WHEN (2023 - CAST(strftime('%Y', birth_date) AS INTEGER)) BETWEEN 75 AND 84 THEN '75-84'
        ELSE '85+'
       END AS age_band,
       COUNT(*) AS beneficiaries
FROM beneficiaries
GROUP BY age_band
ORDER BY age_band;

-- Q2. Chronic condition prevalence across the population
SELECT condition_name,
       SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) AS beneficiaries_affected,
       ROUND(100.0 * SUM(CASE WHEN has_condition = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS prevalence_pct
FROM chronic_conditions
GROUP BY condition_name
ORDER BY prevalence_pct DESC;

-- Q3. Comorbidity burden -- number of chronic conditions per beneficiary, distribution
SELECT condition_count, COUNT(*) AS beneficiaries
FROM (
    SELECT beneficiary_id, SUM(has_condition) AS condition_count
    FROM chronic_conditions
    GROUP BY beneficiary_id
)
GROUP BY condition_count
ORDER BY condition_count;

-- Q4. Utilization: average number of claims per beneficiary, segmented by comorbidity count
WITH comorbidity AS (
    SELECT beneficiary_id, SUM(has_condition) AS condition_count
    FROM chronic_conditions GROUP BY beneficiary_id
),
claim_counts AS (
    SELECT beneficiary_id, COUNT(*) AS n_claims FROM (
        SELECT beneficiary_id FROM inpatient_claims
        UNION ALL SELECT beneficiary_id FROM outpatient_claims
        UNION ALL SELECT beneficiary_id FROM carrier_claims
    ) GROUP BY beneficiary_id
)
SELECT c.condition_count,
       COUNT(DISTINCT c.beneficiary_id) AS beneficiaries,
       ROUND(AVG(COALESCE(cl.n_claims, 0)), 1) AS avg_claims_per_beneficiary
FROM comorbidity c
LEFT JOIN claim_counts cl ON c.beneficiary_id = cl.beneficiary_id
GROUP BY c.condition_count
ORDER BY c.condition_count;

-- Q5. Geographic distribution and average three-year paid amount per beneficiary
SELECT b.state, COUNT(DISTINCT b.beneficiary_id) AS beneficiaries,
       ROUND(SUM(t.paid), 2) AS total_paid,
       ROUND(SUM(t.paid) / COUNT(DISTINCT b.beneficiary_id), 2) AS avg_three_year_paid_per_beneficiary
FROM beneficiaries b
JOIN (
    SELECT beneficiary_id, claim_payment_amount AS paid FROM inpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM outpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM carrier_claims
) t ON b.beneficiary_id = t.beneficiary_id
GROUP BY b.state
ORDER BY avg_three_year_paid_per_beneficiary DESC;

-- Q6. Readmission signal: beneficiaries with 2+ inpatient admissions within 30 days of each other
WITH ordered AS (
    SELECT beneficiary_id, admission_date,
           LAG(discharge_date) OVER (PARTITION BY beneficiary_id ORDER BY admission_date) AS prev_discharge
    FROM inpatient_claims
)
SELECT beneficiary_id, COUNT(*) AS readmissions_within_30d
FROM ordered
WHERE prev_discharge IS NOT NULL
  AND julianday(admission_date) - julianday(prev_discharge) BETWEEN 0 AND 30
GROUP BY beneficiary_id
ORDER BY readmissions_within_30d DESC;
