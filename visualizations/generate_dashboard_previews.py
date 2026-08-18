"""Render six lightweight portfolio previews from the generated data marts."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
MART_DIR = ROOT / "dashboards" / "data_marts"
OUT_DIR = ROOT / "dashboards"
NAVY = "#17324D"
TEAL = "#15A6A6"
ORANGE = "#F28E2B"
RED = "#D9534F"


def read_csv(name: str) -> list[dict[str, str]]:
    with (MART_DIR / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def style(title: str, subtitle: str) -> None:
    plt.title(title, loc="left", fontsize=16, fontweight="bold", color=NAVY)
    plt.figtext(0.125, 0.91, subtitle, fontsize=9, color="#5B6770")
    plt.grid(axis="y", alpha=0.18)
    plt.tight_layout(rect=(0, 0, 1, 0.90))


def save(name: str) -> None:
    plt.savefig(OUT_DIR / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()


def main() -> None:
    monthly = read_csv("executive_summary.csv")
    plt.figure(figsize=(10, 5))
    plt.plot([r["month"] for r in monthly], [float(r["total_paid"]) for r in monthly], color=TEAL, linewidth=2.5)
    plt.xticks(range(0, len(monthly), 3), [monthly[i]["month"] for i in range(0, len(monthly), 3)], rotation=45)
    style("Executive Summary", "Monthly paid amount across all claim types")
    save("01_executive_summary.png")

    status = read_csv("claims_by_status.csv")
    plt.figure(figsize=(8, 5))
    plt.bar([r["claim_status"] for r in status], [int(r["claims"]) for r in status], color=[TEAL, RED, ORANGE, NAVY])
    style("Claims Status", "Operational mix of paid, denied, pending and appealed claims")
    save("02_claims_status.png")

    specialty = read_csv("financial_by_specialty.csv")[:10]
    plt.figure(figsize=(10, 6))
    plt.barh([r["specialty"] for r in reversed(specialty)], [float(r["total_paid"]) for r in reversed(specialty)], color=TEAL)
    style("Financial Performance", "Top specialties by total paid amount")
    save("03_financial_by_specialty.png")

    providers = read_csv("provider_performance.csv")[:15]
    plt.figure(figsize=(10, 6))
    plt.barh([r["provider_id"] for r in reversed(providers)], [float(r["total_paid"]) for r in reversed(providers)], color=NAVY)
    style("Provider Performance", "Top providers by total paid amount")
    save("04_provider_performance.png")

    chronic = read_csv("patient_chronic_conditions.csv")
    plt.figure(figsize=(10, 6))
    plt.barh([r["condition_name"].replace("_", " ") for r in reversed(chronic)], [float(r["prevalence_pct"]) for r in reversed(chronic)], color=TEAL)
    style("Population Health", "Synthetic chronic-condition prevalence")
    save("05_patient_chronic_conditions.png")

    risk = read_csv("fraud_risk_providers.csv")[:15]
    plt.figure(figsize=(10, 6))
    plt.barh([r["provider_id"] for r in reversed(risk)], [float(r["composite_risk_score"]) for r in reversed(risk)], color=RED)
    style("Payment Integrity", "Providers ranked by explainable composite risk score")
    save("06_fraud_risk.png")

    print("Rendered six dashboard previews.")


if __name__ == "__main__":
    main()
