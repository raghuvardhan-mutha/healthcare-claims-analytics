-- ============================================================================
-- Healthcare Claims Analytics — Normalized Schema
-- Source: CMS DE-SynPUF-style synthetic Medicare claims data
-- Engine: PostgreSQL-oriented DDL. The local SQLite loader applies documented
--         NUMERIC/BOOLEAN type translations in etl/load_data.py.
-- ============================================================================

DROP TABLE IF EXISTS claim_procedures;
DROP TABLE IF EXISTS claim_diagnoses;
DROP TABLE IF EXISTS claim_integrity_labels;
DROP TABLE IF EXISTS claim_adjudication;
DROP TABLE IF EXISTS prescription_drug_events;
DROP TABLE IF EXISTS carrier_claims;
DROP TABLE IF EXISTS outpatient_claims;
DROP TABLE IF EXISTS inpatient_claims;
DROP TABLE IF EXISTS chronic_conditions;
DROP TABLE IF EXISTS beneficiaries;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS diagnosis_codes;
DROP TABLE IF EXISTS procedure_codes;
DROP TABLE IF EXISTS drug_codes;

-- 1. Reference: Diagnosis codes (ICD-9/10 style)
CREATE TABLE diagnosis_codes (
    diagnosis_code      VARCHAR(10) PRIMARY KEY,
    description          VARCHAR(255) NOT NULL,
    category              VARCHAR(100)
);

-- 2. Reference: Procedure codes (CPT/HCPCS style)
CREATE TABLE procedure_codes (
    procedure_code       VARCHAR(10) PRIMARY KEY,
    description           VARCHAR(255) NOT NULL,
    category               VARCHAR(100),
    base_allowed_amount    NUMERIC(10,2)
);

-- 3. Reference: Drug codes (NDC style, for Part D events)
CREATE TABLE drug_codes (
    drug_code             VARCHAR(11) PRIMARY KEY,
    drug_name              VARCHAR(150) NOT NULL,
    drug_class              VARCHAR(100),
    is_generic               BOOLEAN
);

-- 4. Beneficiaries (patients)
CREATE TABLE beneficiaries (
    beneficiary_id        VARCHAR(20) PRIMARY KEY,
    birth_date              DATE,
    death_date               DATE,
    sex                        VARCHAR(10),
    race                         VARCHAR(30),
    state                          VARCHAR(2),
    county_code                     VARCHAR(5),
    esrd_indicator                    BOOLEAN,
    part_a_coverage_months               SMALLINT,
    part_b_coverage_months                 SMALLINT,
    hmo_coverage_months                      SMALLINT,
    part_d_coverage_months                      SMALLINT
);

-- 5. Chronic conditions (one row per beneficiary per condition flag)
CREATE TABLE chronic_conditions (
    beneficiary_id      VARCHAR(20) REFERENCES beneficiaries(beneficiary_id),
    condition_name        VARCHAR(50),
    has_condition            BOOLEAN,
    PRIMARY KEY (beneficiary_id, condition_name)
);

-- 6. Providers
CREATE TABLE providers (
    provider_id            VARCHAR(20) PRIMARY KEY,
    provider_name             VARCHAR(150),
    specialty                    VARCHAR(100),
    provider_type                   VARCHAR(50),      -- Hospital / Physician Group / Individual
    state                              VARCHAR(2),
    npi_flag_suspicious                  BOOLEAN DEFAULT FALSE
);

-- 7. Inpatient claims (hospital admissions)
CREATE TABLE inpatient_claims (
    claim_id                VARCHAR(20) PRIMARY KEY,
    beneficiary_id             VARCHAR(20) REFERENCES beneficiaries(beneficiary_id),
    provider_id                   VARCHAR(20) REFERENCES providers(provider_id),
    claim_start_date                 DATE,
    claim_end_date                      DATE,
    admission_date                         DATE,
    discharge_date                            DATE,
    diagnosis_related_group                      VARCHAR(10),
    claim_payment_amount                            NUMERIC(12,2),
    total_charge_amount                                NUMERIC(12,2),
    deductible_amount                                     NUMERIC(10,2),
    claim_status                                             VARCHAR(20)   -- Paid / Denied / Pending / Appealed
);

-- 8. Outpatient claims
CREATE TABLE outpatient_claims (
    claim_id                VARCHAR(20) PRIMARY KEY,
    beneficiary_id             VARCHAR(20) REFERENCES beneficiaries(beneficiary_id),
    provider_id                   VARCHAR(20) REFERENCES providers(provider_id),
    claim_start_date                 DATE,
    claim_end_date                      DATE,
    claim_payment_amount                   NUMERIC(12,2),
    total_charge_amount                       NUMERIC(12,2),
    deductible_amount                            NUMERIC(10,2),
    claim_status                                    VARCHAR(20)
);

-- 9. Carrier claims (physician / professional services, Part B)
CREATE TABLE carrier_claims (
    claim_id                VARCHAR(20) PRIMARY KEY,
    beneficiary_id             VARCHAR(20) REFERENCES beneficiaries(beneficiary_id),
    provider_id                   VARCHAR(20) REFERENCES providers(provider_id),
    claim_start_date                 DATE,
    claim_end_date                      DATE,
    claim_payment_amount                   NUMERIC(12,2),
    line_processing_indicator                 VARCHAR(5),
    claim_status                                 VARCHAR(20)
);

-- 10. Prescription drug events (Part D)
CREATE TABLE prescription_drug_events (
    event_id                VARCHAR(20) PRIMARY KEY,
    beneficiary_id              VARCHAR(20) REFERENCES beneficiaries(beneficiary_id),
    drug_code                      VARCHAR(11) REFERENCES drug_codes(drug_code),
    service_date                      DATE,
    quantity_dispensed                   NUMERIC(8,2),
    days_supply                             SMALLINT,
    total_drug_cost                            NUMERIC(10,2),
    patient_pay_amount                            NUMERIC(10,2)
);

-- 11. Claim <-> Diagnosis bridge (many-to-many)
CREATE TABLE claim_diagnoses (
    claim_id             VARCHAR(20),
    claim_type              VARCHAR(20),   -- inpatient / outpatient / carrier
    diagnosis_code             VARCHAR(10) REFERENCES diagnosis_codes(diagnosis_code),
    diagnosis_sequence             SMALLINT,
    PRIMARY KEY (claim_id, claim_type, diagnosis_sequence)
);

-- 12. Claim <-> Procedure bridge (many-to-many)
CREATE TABLE claim_procedures (
    claim_id             VARCHAR(20),
    claim_type              VARCHAR(20),
    procedure_code              VARCHAR(10) REFERENCES procedure_codes(procedure_code),
    procedure_sequence             SMALLINT,
    line_charge_amount                NUMERIC(10,2),
    PRIMARY KEY (claim_id, claim_type, procedure_sequence)
);

-- 13. Synthetic claim submission and adjudication lifecycle (837 -> 835)
CREATE TABLE claim_adjudication (
    claim_id                        VARCHAR(20),
    claim_type                      VARCHAR(20),
    submitted_date                  DATE NOT NULL,
    received_date                   DATE NOT NULL,
    adjudicated_date                DATE NOT NULL,
    payment_date                    DATE,
    billed_amount                   NUMERIC(12,2) NOT NULL,
    allowed_amount                  NUMERIC(12,2) NOT NULL,
    paid_amount                     NUMERIC(12,2) NOT NULL,
    member_responsibility_amount    NUMERIC(12,2) NOT NULL,
    adjudication_status             VARCHAR(20) NOT NULL,
    denial_reason_code              VARCHAR(10),
    source_transaction              VARCHAR(10) NOT NULL,
    remittance_transaction          VARCHAR(10),
    submission_type                 VARCHAR(20) NOT NULL,
    appeal_indicator                BOOLEAN DEFAULT FALSE,
    injected_pattern                VARCHAR(40) NOT NULL,
    PRIMARY KEY (claim_id, claim_type)
);

-- 14. Ground-truth labels for evaluating synthetic payment-integrity rules
CREATE TABLE claim_integrity_labels (
    claim_id             VARCHAR(20),
    claim_type           VARCHAR(20),
    is_injected_signal   BOOLEAN NOT NULL,
    injected_pattern     VARCHAR(40) NOT NULL,
    PRIMARY KEY (claim_id, claim_type)
);

-- Indexes for common analytical joins
CREATE INDEX idx_inpatient_bene ON inpatient_claims(beneficiary_id);
CREATE INDEX idx_inpatient_provider ON inpatient_claims(provider_id);
CREATE INDEX idx_outpatient_bene ON outpatient_claims(beneficiary_id);
CREATE INDEX idx_outpatient_provider ON outpatient_claims(provider_id);
CREATE INDEX idx_carrier_bene ON carrier_claims(beneficiary_id);
CREATE INDEX idx_carrier_provider ON carrier_claims(provider_id);
CREATE INDEX idx_pde_bene ON prescription_drug_events(beneficiary_id);
CREATE INDEX idx_claimdiag_claim ON claim_diagnoses(claim_id, claim_type);
CREATE INDEX idx_claimproc_claim ON claim_procedures(claim_id, claim_type);
CREATE INDEX idx_adjudication_status ON claim_adjudication(adjudication_status);
CREATE INDEX idx_integrity_pattern ON claim_integrity_labels(injected_pattern);
