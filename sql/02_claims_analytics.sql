-- ============================================================================
-- CLAIMS ANALYTICS -- processing volume, denial rates, turnaround, status mix
-- ============================================================================

-- Q1. Overall claim volume and dollar value by claim type
SELECT 'Inpatient' AS claim_type, COUNT(*) AS claim_count,
       SUM(claim_payment_amount) AS total_paid, ROUND(AVG(claim_payment_amount),2) AS avg_paid
FROM inpatient_claims
UNION ALL
SELECT 'Outpatient', COUNT(*), SUM(claim_payment_amount), ROUND(AVG(claim_payment_amount),2)
FROM outpatient_claims
UNION ALL
SELECT 'Carrier', COUNT(*), SUM(claim_payment_amount), ROUND(AVG(claim_payment_amount),2)
FROM carrier_claims;

-- Q2. Claim status distribution (denial / pending / appeal rate) across all claim types
WITH all_claims AS (
    SELECT claim_status FROM inpatient_claims
    UNION ALL SELECT claim_status FROM outpatient_claims
    UNION ALL SELECT claim_status FROM carrier_claims
)
SELECT claim_status,
       COUNT(*) AS claims,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM all_claims), 2) AS pct_of_total
FROM all_claims
GROUP BY claim_status
ORDER BY claims DESC;

-- Q3. Denial rate by provider specialty (surfaces specialties with abnormal denial rates)
SELECT p.specialty,
       COUNT(*) AS total_claims,
       SUM(CASE WHEN o.claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
       ROUND(100.0 * SUM(CASE WHEN o.claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate_pct
FROM outpatient_claims o
JOIN providers p ON o.provider_id = p.provider_id
GROUP BY p.specialty
ORDER BY denial_rate_pct DESC;

-- Q4. Average service duration (claim start to claim end) by claim type
SELECT 'Inpatient' AS claim_type,
       ROUND(AVG(julianday(claim_end_date) - julianday(claim_start_date)), 1) AS avg_days
FROM inpatient_claims
UNION ALL
SELECT 'Outpatient', ROUND(AVG(julianday(claim_end_date) - julianday(claim_start_date)), 1)
FROM outpatient_claims;

-- Q5. Monthly claims volume trend (seasonality check)
SELECT strftime('%Y-%m', claim_start_date) AS claim_month,
       COUNT(*) AS claims,
       SUM(claim_payment_amount) AS total_paid
FROM (
    SELECT claim_start_date, claim_payment_amount FROM inpatient_claims
    UNION ALL SELECT claim_start_date, claim_payment_amount FROM outpatient_claims
    UNION ALL SELECT claim_start_date, claim_payment_amount FROM carrier_claims
)
GROUP BY claim_month
ORDER BY claim_month;

-- Q6. Top 10 diagnosis codes by claim volume across all claim types
SELECT d.diagnosis_code, d.description, d.category, COUNT(*) AS claim_count
FROM claim_diagnoses cd
JOIN diagnosis_codes d ON cd.diagnosis_code = d.diagnosis_code
GROUP BY d.diagnosis_code, d.description, d.category
ORDER BY claim_count DESC
LIMIT 10;

-- Q7. Claims pending more than 30 days at the historical snapshot date
SELECT claim_id, beneficiary_id, claim_start_date,
       CAST(julianday('2024-01-01') - julianday(claim_start_date) AS INTEGER) AS days_pending
FROM outpatient_claims
WHERE claim_status = 'Pending'
ORDER BY days_pending DESC
LIMIT 25;

-- Q8. Appeal rate by state (regulatory/compliance risk view)
SELECT b.state,
       COUNT(*) AS total_claims,
       SUM(CASE WHEN o.claim_status = 'Appealed' THEN 1 ELSE 0 END) AS appealed,
       ROUND(100.0 * SUM(CASE WHEN o.claim_status = 'Appealed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS appeal_rate_pct
FROM outpatient_claims o
JOIN beneficiaries b ON o.beneficiary_id = b.beneficiary_id
GROUP BY b.state
ORDER BY appeal_rate_pct DESC;
