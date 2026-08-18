-- ============================================================================
-- FRAUD / PAYMENT INTEGRITY ANALYTICS
-- Modeled directly on a real pattern I investigated at UHG: using window
-- functions (PARTITION BY / ranking) to find claims sharing member ID,
-- provider ID, and date of service that were billed as suspiciously many
-- separate line items -- i.e. unbundled procedure billing.
-- ============================================================================

-- Q1. UNBUNDLING DETECTION
-- Same beneficiary + provider + date of service billed as 3+ separate
-- procedure codes in one claim, where a single bundled code would be expected.
WITH claim_line_counts AS (
    SELECT o.claim_id, o.beneficiary_id, o.provider_id, o.claim_start_date,
           COUNT(cp.procedure_code) AS line_items,
           SUM(cp.line_charge_amount) AS total_line_charges
    FROM outpatient_claims o
    JOIN claim_procedures cp ON o.claim_id = cp.claim_id AND cp.claim_type = 'outpatient'
    GROUP BY o.claim_id, o.beneficiary_id, o.provider_id, o.claim_start_date
)
SELECT provider_id, beneficiary_id, claim_id, claim_start_date, line_items, total_line_charges
FROM claim_line_counts
WHERE line_items >= 3
ORDER BY total_line_charges DESC
LIMIT 25;

-- Q2. DUPLICATE BILLING DETECTION
-- Same beneficiary/provider/procedure/date billed as 2+ separate claim IDs
-- (window function ranks duplicates within each match group).
WITH ranked AS (
    SELECT cc.claim_id, cc.beneficiary_id, cc.provider_id, cc.claim_start_date, cp.procedure_code,
           cc.claim_payment_amount,
           ROW_NUMBER() OVER (
               PARTITION BY cc.beneficiary_id, cc.provider_id, cp.procedure_code, cc.claim_start_date
               ORDER BY cc.claim_id
           ) AS dup_rank,
           COUNT(*) OVER (
               PARTITION BY cc.beneficiary_id, cc.provider_id, cp.procedure_code, cc.claim_start_date
           ) AS group_size
    FROM carrier_claims cc
    JOIN claim_procedures cp ON cc.claim_id = cp.claim_id AND cp.claim_type = 'carrier'
)
SELECT beneficiary_id, provider_id, procedure_code, claim_start_date,
       group_size AS times_billed, group_size * claim_payment_amount AS total_billed_for_group
FROM ranked
WHERE dup_rank = 1 AND group_size >= 2
ORDER BY total_billed_for_group DESC
LIMIT 25;

-- Q3. UPCODING SIGNAL -- inpatient claims with payment far above the average
-- for their DRG code (potential DRG upcoding)
WITH drg_avg AS (
    SELECT diagnosis_related_group, AVG(claim_payment_amount) AS avg_payment,
           AVG(claim_payment_amount) * 1.5 AS threshold
    FROM inpatient_claims
    GROUP BY diagnosis_related_group
)
SELECT ip.claim_id, ip.provider_id, ip.diagnosis_related_group,
       ip.claim_payment_amount, ROUND(da.avg_payment, 2) AS drg_avg_payment,
       ROUND(ip.claim_payment_amount / da.avg_payment, 2) AS times_above_avg
FROM inpatient_claims ip
JOIN drg_avg da ON ip.diagnosis_related_group = da.diagnosis_related_group
WHERE ip.claim_payment_amount > da.threshold
ORDER BY times_above_avg DESC
LIMIT 25;

-- Q4. PROVIDER-LEVEL FRAUD RISK SCORE
-- Combines three signals into a single ranked risk score per provider:
--   - unbundling rate (avg line items per claim)
--   - duplicate billing occurrences
--   - cost variance vs specialty peers
WITH unbundling AS (
    SELECT o.provider_id, AVG(sub.line_items) AS avg_line_items
    FROM outpatient_claims o
    JOIN (
        SELECT claim_id, COUNT(*) AS line_items
        FROM claim_procedures WHERE claim_type = 'outpatient'
        GROUP BY claim_id
    ) sub ON o.claim_id = sub.claim_id
    GROUP BY o.provider_id
),
cost_variance AS (
    SELECT o.provider_id, AVG(o.claim_payment_amount) AS avg_paid
    FROM outpatient_claims o GROUP BY o.provider_id
),
specialty_map AS (
    SELECT provider_id, specialty FROM providers
),
specialty_avg AS (
    SELECT sm.specialty, AVG(cv.avg_paid) AS specialty_avg_paid
    FROM cost_variance cv JOIN specialty_map sm ON cv.provider_id = sm.provider_id
    GROUP BY sm.specialty
)
SELECT p.provider_id, p.provider_name, p.specialty, p.npi_flag_suspicious,
       ROUND(u.avg_line_items, 2) AS avg_line_items_per_claim,
       ROUND(cv.avg_paid, 2) AS avg_claim_payment,
       ROUND(cv.avg_paid / sa.specialty_avg_paid, 2) AS cost_vs_peer_ratio,
       ROUND(
           (u.avg_line_items / 1.0) + (cv.avg_paid / sa.specialty_avg_paid), 2
       ) AS composite_risk_score
FROM providers p
JOIN unbundling u ON p.provider_id = u.provider_id
JOIN cost_variance cv ON p.provider_id = cv.provider_id
JOIN specialty_avg sa ON p.specialty = sa.specialty
ORDER BY composite_risk_score DESC
LIMIT 20;
