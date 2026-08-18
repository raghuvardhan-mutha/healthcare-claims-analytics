-- ============================================================================
-- PROVIDER ANALYTICS -- performance, utilization, cost variance across providers
-- ============================================================================

-- Q1. Provider claim volume and total payment (top 20 by volume)
SELECT p.provider_id, p.provider_name, p.specialty,
       COUNT(*) AS claim_count, ROUND(SUM(t.paid), 2) AS total_paid
FROM providers p
JOIN (
    SELECT provider_id, claim_payment_amount AS paid FROM outpatient_claims
    UNION ALL SELECT provider_id, claim_payment_amount FROM carrier_claims
    UNION ALL SELECT provider_id, claim_payment_amount FROM inpatient_claims
) t ON p.provider_id = t.provider_id
GROUP BY p.provider_id, p.provider_name, p.specialty
ORDER BY claim_count DESC
LIMIT 20;

-- Q2. Provider cost-per-claim ranked against specialty peer average (outlier detection)
WITH provider_avg AS (
    SELECT p.provider_id, p.specialty, AVG(o.claim_payment_amount) AS provider_avg_paid
    FROM providers p JOIN outpatient_claims o ON p.provider_id = o.provider_id
    GROUP BY p.provider_id, p.specialty
),
specialty_avg AS (
    SELECT specialty, AVG(provider_avg_paid) AS specialty_avg_paid
    FROM provider_avg GROUP BY specialty
)
SELECT pa.provider_id, pa.specialty,
       ROUND(pa.provider_avg_paid, 2) AS provider_avg,
       ROUND(sa.specialty_avg_paid, 2) AS specialty_avg,
       ROUND(100.0 * (pa.provider_avg_paid - sa.specialty_avg_paid) / sa.specialty_avg_paid, 1) AS pct_above_specialty_avg
FROM provider_avg pa
JOIN specialty_avg sa ON pa.specialty = sa.specialty
WHERE pa.provider_avg_paid > sa.specialty_avg_paid * 1.3   -- 30%+ above peer average
ORDER BY pct_above_specialty_avg DESC;

-- Q3. Provider claim denial rates (bottom performers)
SELECT p.provider_id, p.provider_name, p.specialty,
       COUNT(*) AS total_claims,
       SUM(CASE WHEN o.claim_status = 'Denied' THEN 1 ELSE 0 END) AS denials,
       ROUND(100.0 * SUM(CASE WHEN o.claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate_pct
FROM providers p
JOIN outpatient_claims o ON p.provider_id = o.provider_id
GROUP BY p.provider_id, p.provider_name, p.specialty
HAVING COUNT(*) >= 20
ORDER BY denial_rate_pct DESC
LIMIT 15;

-- Q4. Provider type mix and average claim payment (Hospital vs Physician Group vs Individual)
SELECT p.provider_type, COUNT(*) AS claims, ROUND(AVG(t.paid), 2) AS avg_paid
FROM providers p
JOIN (
    SELECT provider_id, claim_payment_amount AS paid FROM outpatient_claims
    UNION ALL SELECT provider_id, claim_payment_amount FROM carrier_claims
) t ON p.provider_id = t.provider_id
GROUP BY p.provider_type
ORDER BY avg_paid DESC;

-- Q5. Providers billing the same procedure code far more often than specialty peers
-- (utilization concentration -- possible upcoding/unnecessary services signal)
WITH proc_counts AS (
    SELECT cp.procedure_code, o.provider_id, COUNT(*) AS uses
    FROM claim_procedures cp
    JOIN outpatient_claims o ON cp.claim_id = o.claim_id AND cp.claim_type = 'outpatient'
    GROUP BY cp.procedure_code, o.provider_id
),
proc_avg AS (
    SELECT procedure_code, AVG(uses) AS avg_uses, MAX(uses) AS max_uses
    FROM proc_counts GROUP BY procedure_code
)
SELECT pc.provider_id, pc.procedure_code, pc.uses, ROUND(pa.avg_uses, 1) AS peer_avg_uses,
       ROUND(pc.uses / pa.avg_uses, 1) AS times_above_avg
FROM proc_counts pc
JOIN proc_avg pa ON pc.procedure_code = pa.procedure_code
WHERE pc.uses > pa.avg_uses * 3
ORDER BY times_above_avg DESC
LIMIT 15;
