"""
generate_data.py
-----------------
Generates a synthetic Medicare-claims-style dataset modeled on the structure
of CMS's DE-SynPUF (Data Entrepreneurs' Synthetic Public Use Files).

This is NOT real CMS data -- it is fully synthetic data generated to match
the *shape* of DE-SynPUF (same table structure, realistic code distributions,
realistic $ ranges) so the pipeline, schema, and analytics below can be
demoed without needing to download/license the real files.

A small number of fraud-pattern claims are deliberately injected
(unbundled procedures, duplicate billing, upcoded DRGs) so the fraud
detection SQL/dashboard has real signal to find.

Output: CSV files in ../data/, one per table, matching sql/01_schema.sql
"""
import argparse
import random
import csv
import os
from datetime import date, timedelta
from faker import Faker

random.seed(42)
adjudication_rng = random.Random(2_026_0818)
fake = Faker()
Faker.seed(42)

SCALE_PROFILES = {
    "demo": (5_000, 400, 3_000, 12_000, 25_000, 18_000),
    "medium": (25_000, 2_000, 20_000, 80_000, 200_000, 120_000),
    "large": (100_000, 8_000, 75_000, 300_000, 625_000, 500_000),
}
N_BENEFICIARIES, N_PROVIDERS, N_INPATIENT, N_OUTPATIENT, N_CARRIER, N_PDE = SCALE_PROFILES["demo"]
FRAUD_RATE = 0.02  # deterministic target rate within each applicable claim type

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

STATES = ["MA", "NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC"]
RACES = ["White", "Black", "Hispanic", "Asian", "Other"]
CHRONIC_CONDITIONS = [
    "Diabetes", "Heart_Failure", "Ischemic_Heart_Disease", "COPD",
    "Chronic_Kidney_Disease", "Depression", "Cancer", "Stroke",
    "Rheumatoid_Arthritis", "Alzheimers"
]
SPECIALTIES = [
    "Internal Medicine", "Cardiology", "Orthopedic Surgery", "General Surgery",
    "Family Practice", "Emergency Medicine", "Radiology", "Anesthesiology",
    "Oncology", "Nephrology", "Neurology", "Psychiatry"
]
PROVIDER_TYPES = ["Hospital", "Physician Group", "Individual Practitioner", "Outpatient Facility"]

DIAGNOSES = [
    ("2500", "Diabetes mellitus without complication", "Endocrine"),
    ("4280", "Congestive heart failure", "Cardiovascular"),
    ("41401", "Coronary atherosclerosis", "Cardiovascular"),
    ("4919", "COPD unspecified", "Respiratory"),
    ("5859", "Chronic kidney disease unspecified", "Renal"),
    ("311", "Depressive disorder", "Behavioral Health"),
    ("1749", "Malignant neoplasm of breast", "Oncology"),
    ("43491", "Cerebral artery occlusion with infarction", "Cardiovascular"),
    ("71489", "Rheumatoid arthritis", "Musculoskeletal"),
    ("3310", "Alzheimer's disease", "Neurological"),
    ("78650", "Chest pain unspecified", "Cardiovascular"),
    ("486", "Pneumonia organism unspecified", "Respiratory"),
    ("5990", "Urinary tract infection", "Renal"),
    ("7242", "Lumbago (low back pain)", "Musculoskeletal"),
    ("496", "Chronic airway obstruction", "Respiratory"),
]

PROCEDURES = [
    ("99213", "Office visit, established patient, low complexity", "E&M", 75.00),
    ("99214", "Office visit, established patient, moderate complexity", "E&M", 110.00),
    ("99283", "Emergency department visit, moderate severity", "E&M", 180.00),
    ("93000", "Electrocardiogram, complete", "Diagnostic", 25.00),
    ("71046", "Chest X-ray, 2 views", "Radiology", 45.00),
    ("80053", "Comprehensive metabolic panel", "Lab", 30.00),
    ("36415", "Collection of venous blood", "Lab", 8.00),
    ("29881", "Knee arthroscopy with meniscectomy", "Surgery", 1450.00),
    ("47562", "Laparoscopic cholecystectomy", "Surgery", 2100.00),
    ("33533", "Coronary artery bypass, single graft", "Surgery", 18500.00),
    ("70450", "CT head/brain without contrast", "Radiology", 260.00),
    ("97110", "Therapeutic exercise, physical therapy", "Therapy", 40.00),
    ("90837", "Psychotherapy, 60 minutes", "Behavioral Health", 150.00),
    ("27447", "Total knee replacement", "Surgery", 14200.00),
    ("45378", "Colonoscopy diagnostic", "Surgery", 850.00),
]

DRUGS = [
    ("00071015523", "Lipitor (atorvastatin)", "Statins", False),
    ("00093715601", "Atorvastatin (generic)", "Statins", True),
    ("00002751501", "Humalog (insulin lispro)", "Insulin", False),
    ("00378180201", "Metformin", "Antidiabetic", True),
    ("00069153041", "Norvasc (amlodipine)", "Antihypertensive", False),
    ("00591035501", "Amlodipine (generic)", "Antihypertensive", True),
    ("00186007031", "Lasix (furosemide)", "Diuretic", False),
    ("00378180501", "Furosemide (generic)", "Diuretic", True),
    ("00074433902", "Synthroid (levothyroxine)", "Thyroid", False),
    ("00006027331", "Sertraline (generic)", "Antidepressant", True),
]

DRG_CODES = ["039", "057", "064", "089", "127", "175", "194", "247", "292", "313", "460", "470"]
DENIAL_CODES = ["CO-16", "CO-29", "CO-50", "CO-96", "PR-1", "PR-2"]


def configure_scale(profile: str) -> None:
    """Apply a documented generation profile without changing downstream code."""
    global N_BENEFICIARIES, N_PROVIDERS, N_INPATIENT, N_OUTPATIENT, N_CARRIER, N_PDE
    N_BENEFICIARIES, N_PROVIDERS, N_INPATIENT, N_OUTPATIENT, N_CARRIER, N_PDE = SCALE_PROFILES[profile]


def adjudication_row(claim_id, claim_type, service_date, billed, paid, status, pattern="none"):
    """Create a synthetic 837-to-835 adjudication lifecycle for one claim."""
    submitted = service_date + timedelta(days=adjudication_rng.randint(1, 7))
    received = submitted + timedelta(days=adjudication_rng.randint(0, 2))
    adjudicated = received + timedelta(days=adjudication_rng.randint(1, 18))
    payment_date = "" if status in ("Denied", "Pending") else (adjudicated + timedelta(days=adjudication_rng.randint(1, 7))).isoformat()
    billed = round(max(billed, paid), 2)
    allowed = 0.0 if status == "Denied" else round(min(billed, max(paid, billed * adjudication_rng.uniform(0.58, 0.88))), 2)
    member_responsibility = 0.0 if status == "Denied" else round(max(allowed - paid, 0), 2)
    denial_code = adjudication_rng.choice(DENIAL_CODES) if status == "Denied" else ""
    return (
        claim_id, claim_type, submitted.isoformat(), received.isoformat(), adjudicated.isoformat(),
        payment_date, billed, allowed, paid, member_responsibility, status, denial_code,
        "837I" if claim_type == "inpatient" else "837P", "" if status == "Pending" else "835",
        "replacement" if status == "Appealed" else "original", status == "Appealed", pattern,
    )


def rand_date(start_year=2021, end_year=2023):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ---------------------------------------------------------------------------
# 1. Reference tables
# ---------------------------------------------------------------------------
def write_reference_tables():
    with open(f"{OUT_DIR}/diagnosis_codes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["diagnosis_code", "description", "category"])
        w.writerows(DIAGNOSES)

    with open(f"{OUT_DIR}/procedure_codes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["procedure_code", "description", "category", "base_allowed_amount"])
        w.writerows(PROCEDURES)

    with open(f"{OUT_DIR}/drug_codes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["drug_code", "drug_name", "drug_class", "is_generic"])
        w.writerows(DRUGS)


# ---------------------------------------------------------------------------
# 2. Beneficiaries + chronic conditions
# ---------------------------------------------------------------------------
def generate_beneficiaries():
    bene_ids = [f"BEN{100000+i}" for i in range(N_BENEFICIARIES)]
    with open(f"{OUT_DIR}/beneficiaries.csv", "w", newline="") as f, \
         open(f"{OUT_DIR}/chronic_conditions.csv", "w", newline="") as f2:
        w = csv.writer(f)
        w.writerow(["beneficiary_id", "birth_date", "death_date", "sex", "race", "state",
                     "county_code", "esrd_indicator", "part_a_coverage_months",
                     "part_b_coverage_months", "hmo_coverage_months", "part_d_coverage_months"])
        w2 = csv.writer(f2)
        w2.writerow(["beneficiary_id", "condition_name", "has_condition"])

        for bid in bene_ids:
            birth = date(random.randint(1930, 1958), random.randint(1, 12), random.randint(1, 28))
            death = ""
            if random.random() < 0.03:
                death = (birth + timedelta(days=random.randint(25000, 34000))).isoformat()
            w.writerow([
                bid, birth.isoformat(), death,
                random.choice(["M", "F"]),
                random.choices(RACES, weights=[70, 15, 8, 5, 2])[0],
                random.choice(STATES),
                f"{random.randint(1,999):03d}",
                random.random() < 0.02,
                12, 12,
                random.choice([0, 0, 0, 12]),
                random.choice([0, 12, 12])
            ])
            for cond in CHRONIC_CONDITIONS:
                has = random.random() < 0.28
                w2.writerow([bid, cond, has])
    return bene_ids


# ---------------------------------------------------------------------------
# 3. Providers
# ---------------------------------------------------------------------------
def generate_providers():
    provider_ids = [f"PRV{20000+i}" for i in range(N_PROVIDERS)]
    with open(f"{OUT_DIR}/providers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["provider_id", "provider_name", "specialty", "provider_type", "state", "npi_flag_suspicious"])
        for i, pid in enumerate(provider_ids):
            # ~3% of providers are seeded as "suspicious" (outlier billing) for fraud module
            suspicious = i < int(N_PROVIDERS * 0.03)
            w.writerow([
                pid,
                fake.company() + (" Medical Group" if random.random() < 0.5 else " Clinic"),
                random.choice(SPECIALTIES),
                random.choice(PROVIDER_TYPES),
                random.choice(STATES),
                suspicious
            ])
    return provider_ids, [f"PRV{20000+i}" for i in range(int(N_PROVIDERS * 0.03))]


# ---------------------------------------------------------------------------
# 4. Claims (inpatient, outpatient, carrier) + diagnosis/procedure bridges
# ---------------------------------------------------------------------------
def generate_claims(bene_ids, provider_ids, suspicious_providers):
    diag_codes = [d[0] for d in DIAGNOSES]
    proc_codes = [(p[0], p[3]) for p in PROCEDURES]

    diag_rows, proc_rows, adjudication_rows = [], [], []

    # --- Inpatient ---
    with open(f"{OUT_DIR}/inpatient_claims.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "beneficiary_id", "provider_id", "claim_start_date", "claim_end_date",
                     "admission_date", "discharge_date", "diagnosis_related_group",
                     "claim_payment_amount", "total_charge_amount", "deductible_amount", "claim_status"])
        for i in range(N_INPATIENT):
            cid = f"IP{500000+i}"
            bid = random.choice(bene_ids)
            is_fraud = random.random() < FRAUD_RATE
            pid = random.choice(suspicious_providers if is_fraud else provider_ids)
            admit = rand_date()
            los = random.randint(1, 12)
            discharge = admit + timedelta(days=los)
            base_pay = round(random.uniform(4000, 28000), 2)
            if is_fraud:
                base_pay = round(base_pay * random.uniform(1.6, 2.3), 2)  # upcoded DRG payment spike
            charge = round(base_pay * random.uniform(1.15, 1.6), 2)
            status = random.choices(["Paid", "Denied", "Pending", "Appealed"], weights=[82, 8, 6, 4])[0]
            if status in ("Denied", "Pending"):
                base_pay = 0.0
            w.writerow([cid, bid, pid, admit.isoformat(), discharge.isoformat(),
                        admit.isoformat(), discharge.isoformat(),
                        random.choice(DRG_CODES), base_pay, charge,
                        round(random.uniform(150, 1600), 2), status])
            adjudication_rows.append(adjudication_row(
                cid, "inpatient", discharge, charge, base_pay, status,
                "drg_payment_outlier" if is_fraud else "none",
            ))
            dc = random.choice(diag_codes)
            diag_rows.append((cid, "inpatient", dc, 1))

    # --- Outpatient ---
    with open(f"{OUT_DIR}/outpatient_claims.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "beneficiary_id", "provider_id", "claim_start_date", "claim_end_date",
                     "claim_payment_amount", "total_charge_amount", "deductible_amount", "claim_status"])
        for i in range(N_OUTPATIENT):
            cid = f"OP{700000+i}"
            bid = random.choice(bene_ids)
            is_fraud = random.random() < FRAUD_RATE
            pid = random.choice(suspicious_providers if is_fraud else provider_ids)
            d = rand_date()
            proc_code, base_amt = random.choice(proc_codes)
            pay = round(base_amt * random.uniform(0.85, 1.1), 2)
            charge = round(pay * random.uniform(1.2, 1.8), 2)
            status = random.choices(["Paid", "Denied", "Pending", "Appealed"], weights=[80, 10, 6, 4])[0]
            if status in ("Denied", "Pending"):
                pay = 0.0
            w.writerow([cid, bid, pid, d.isoformat(), d.isoformat(), pay, charge,
                        round(random.uniform(0, 250), 2), status])
            adjudication_rows.append(adjudication_row(
                cid, "outpatient", d, charge, pay, status,
                "potential_unbundling" if is_fraud else "none",
            ))
            diag_rows.append((cid, "outpatient", random.choice(diag_codes), 1))

            # normal claim: 1 procedure line. Fraud pattern: unbundling -> same
            # service billed as 3-4 separate component procedure codes instead of 1.
            if is_fraud:
                for seq, alt_proc in enumerate(random.sample([p[0] for p in proc_codes], k=3), start=1):
                    proc_rows.append((cid, "outpatient", alt_proc, seq, round(base_amt * random.uniform(0.4, 0.7), 2)))
            else:
                proc_rows.append((cid, "outpatient", proc_code, 1, charge))

    # --- Carrier (physician/professional) ---
    with open(f"{OUT_DIR}/carrier_claims.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "beneficiary_id", "provider_id", "claim_start_date", "claim_end_date",
                     "claim_payment_amount", "line_processing_indicator", "claim_status"])
        seen_dupe_keys = set()
        for i in range(N_CARRIER):
            cid = f"CC{900000+i}"
            bid = random.choice(bene_ids)
            is_duplicate = random.random() < FRAUD_RATE
            pid = random.choice(suspicious_providers if is_duplicate else provider_ids)
            d = rand_date()
            proc_code, base_amt = random.choice(proc_codes)
            pay = round(base_amt * random.uniform(0.8, 1.05), 2)
            status = random.choices(["Paid", "Denied", "Pending", "Appealed"], weights=[85, 7, 5, 3])[0]
            if is_duplicate:
                status = "Paid"
            if status in ("Denied", "Pending"):
                pay = 0.0
            w.writerow([cid, bid, pid, d.isoformat(), d.isoformat(), pay, "A", status])
            adjudication_rows.append(adjudication_row(
                cid, "carrier", d, base_amt, pay, status,
                "duplicate_billing_source" if is_duplicate else "none",
            ))
            diag_rows.append((cid, "carrier", random.choice(diag_codes), 1))
            proc_rows.append((cid, "carrier", proc_code, 1, base_amt))

            # Fraud pattern: duplicate billing -- same bene/provider/procedure/date
            # billed twice as separate claim IDs.
            dupe_key = (bid, pid, proc_code, d.isoformat())
            if is_duplicate and dupe_key not in seen_dupe_keys:
                seen_dupe_keys.add(dupe_key)
                dup_cid = f"CC{900000+i}D"
                w.writerow([dup_cid, bid, pid, d.isoformat(), d.isoformat(), pay, "A", "Paid"])
                adjudication_rows.append(adjudication_row(
                    dup_cid, "carrier", d, base_amt, pay, "Paid", "duplicate_billing_copy",
                ))
                diag_rows.append((dup_cid, "carrier", random.choice(diag_codes), 1))
                proc_rows.append((dup_cid, "carrier", proc_code, 1, base_amt))

    with open(f"{OUT_DIR}/claim_diagnoses.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "claim_type", "diagnosis_code", "diagnosis_sequence"])
        w.writerows(diag_rows)

    with open(f"{OUT_DIR}/claim_procedures.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "claim_type", "procedure_code", "procedure_sequence", "line_charge_amount"])
        w.writerows(proc_rows)

    with open(f"{OUT_DIR}/claim_adjudication.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "claim_id", "claim_type", "submitted_date", "received_date", "adjudicated_date",
            "payment_date", "billed_amount", "allowed_amount", "paid_amount",
            "member_responsibility_amount", "adjudication_status", "denial_reason_code",
            "source_transaction", "remittance_transaction", "submission_type",
            "appeal_indicator", "injected_pattern",
        ])
        w.writerows(adjudication_rows)

    with open(f"{OUT_DIR}/claim_integrity_labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "claim_type", "is_injected_signal", "injected_pattern"])
        for row in adjudication_rows:
            pattern = row[-1]
            w.writerow([row[0], row[1], pattern != "none", pattern])


# ---------------------------------------------------------------------------
# 5. Prescription drug events (Part D)
# ---------------------------------------------------------------------------
def generate_pde(bene_ids):
    drug_codes = [(d[0]) for d in DRUGS]
    with open(f"{OUT_DIR}/prescription_drug_events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "beneficiary_id", "drug_code", "service_date",
                     "quantity_dispensed", "days_supply", "total_drug_cost", "patient_pay_amount"])
        for i in range(N_PDE):
            eid = f"PDE{300000+i}"
            bid = random.choice(bene_ids)
            drug = random.choice(drug_codes)
            d = rand_date()
            qty = random.choice([30, 60, 90])
            cost = round(random.uniform(8, 320), 2)
            copay = round(cost * random.uniform(0.05, 0.3), 2)
            w.writerow([eid, bid, drug, d.isoformat(), qty, qty, cost, copay])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic claims data.")
    parser.add_argument(
        "--scale", choices=sorted(SCALE_PROFILES), default=os.getenv("CLAIMS_SCALE", "demo"),
        help="demo=40K, medium=300K, large=1M base claims",
    )
    args = parser.parse_args()
    configure_scale(args.scale)
    print("Generating reference tables...")
    write_reference_tables()
    print("Generating beneficiaries + chronic conditions...")
    bene_ids = generate_beneficiaries()
    print("Generating providers...")
    provider_ids, suspicious_providers = generate_providers()
    print("Generating claims (inpatient/outpatient/carrier) + diagnosis/procedure bridges...")
    generate_claims(bene_ids, provider_ids, suspicious_providers)
    print("Generating prescription drug events...")
    generate_pde(bene_ids)
    print(f"\nDone ({args.scale} profile). {N_BENEFICIARIES} beneficiaries, {N_PROVIDERS} providers "
          f"({len(suspicious_providers)} seeded as fraud-pattern outliers), "
          f"{N_INPATIENT + N_OUTPATIENT + N_CARRIER} total claims, {N_PDE} drug events.")
    print(f"CSV files written to: {OUT_DIR}")
