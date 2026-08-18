-- ============================================================================
-- FINANCIAL ANALYTICS -- payment trends, cost drivers, charge-vs-paid variance
-- ============================================================================

-- Q1. Total paid amount by year and claim type
SELECT strftime('%Y', claim_start_date) AS claim_year, 'Inpatient' AS claim_type,
       SUM(claim_payment_amount) AS total_paid
FROM inpatient_claims GROUP BY 1
UNION ALL
SELECT strftime('%Y', claim_start_date) AS claim_year, 'Outpatient', SUM(claim_payment_amount)
FROM outpatient_claims GROUP BY 1
ORDER BY claim_year, claim_type;

-- Q2. Charge-to-payment ratio (how much billed vs actually paid) -- payment integrity signal
SELECT 'Inpatient' AS claim_type,
       ROUND(SUM(total_charge_amount), 2) AS total_charged,
       ROUND(SUM(claim_payment_amount), 2) AS total_paid,
       ROUND(SUM(total_charge_amount) / NULLIF(SUM(claim_payment_amount), 0), 2) AS charge_to_paid_ratio
FROM inpatient_claims
UNION ALL
SELECT 'Outpatient',
       ROUND(SUM(total_charge_amount), 2), ROUND(SUM(claim_payment_amount), 2),
       ROUND(SUM(total_charge_amount) / NULLIF(SUM(claim_payment_amount), 0), 2)
FROM outpatient_claims;

-- Q3. Top 15 highest-cost beneficiaries (total spend across all claim types) -- high-cost case management
SELECT beneficiary_id, ROUND(SUM(paid), 2) AS total_paid
FROM (
    SELECT beneficiary_id, claim_payment_amount AS paid FROM inpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM outpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM carrier_claims
)
GROUP BY beneficiary_id
ORDER BY total_paid DESC
LIMIT 15;

-- Q4. Average cost per chronic condition (which conditions drive the most spend)
SELECT cc.condition_name,
       COUNT(DISTINCT cc.beneficiary_id) AS beneficiaries_with_condition,
       ROUND(SUM(t.paid), 2) AS total_paid,
       ROUND(SUM(t.paid) / COUNT(DISTINCT cc.beneficiary_id), 2) AS avg_paid_per_beneficiary
FROM chronic_conditions cc
JOIN (
    SELECT beneficiary_id, claim_payment_amount AS paid FROM inpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM outpatient_claims
    UNION ALL SELECT beneficiary_id, claim_payment_amount FROM carrier_claims
) t ON cc.beneficiary_id = t.beneficiary_id
WHERE cc.has_condition = 1
GROUP BY cc.condition_name
ORDER BY total_paid DESC;

-- Q5. Prescription drug spend: generic vs brand-name cost comparison
SELECT dc.is_generic,
       COUNT(*) AS fills,
       ROUND(SUM(p.total_drug_cost), 2) AS total_cost,
       ROUND(AVG(p.total_drug_cost), 2) AS avg_cost_per_fill
FROM prescription_drug_events p
JOIN drug_codes dc ON p.drug_code = dc.drug_code
GROUP BY dc.is_generic;

-- Q6. Month-over-month revenue/payment trend with % change
WITH monthly AS (
    SELECT strftime('%Y-%m', claim_start_date) AS month, SUM(claim_payment_amount) AS paid
    FROM (
        SELECT claim_start_date, claim_payment_amount FROM inpatient_claims
        UNION ALL SELECT claim_start_date, claim_payment_amount FROM outpatient_claims
        UNION ALL SELECT claim_start_date, claim_payment_amount FROM carrier_claims
    )
    GROUP BY month
)
SELECT month, paid,
       ROUND(100.0 * (paid - LAG(paid) OVER (ORDER BY month)) / NULLIF(LAG(paid) OVER (ORDER BY month), 0), 2) AS pct_change_mom
FROM monthly
ORDER BY month;

-- Q7. Deductible burden by state (patient out-of-pocket exposure)
SELECT b.state, ROUND(SUM(o.deductible_amount), 2) AS total_deductible,
       ROUND(AVG(o.deductible_amount), 2) AS avg_deductible
FROM outpatient_claims o
JOIN beneficiaries b ON o.beneficiary_id = b.beneficiary_id
GROUP BY b.state
ORDER BY total_deductible DESC;
