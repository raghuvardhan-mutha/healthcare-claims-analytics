import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWER_BI = ROOT / "powerbi"


def test_power_bi_json_assets_are_valid() -> None:
    json_files = sorted(POWER_BI.rglob("*.json")) + sorted(POWER_BI.rglob("*.pbip")) + sorted(POWER_BI.rglob("*.pbir")) + sorted(POWER_BI.rglob("*.pbism"))
    assert json_files
    for path in json_files:
        with path.open(encoding="utf-8") as handle:
            json.load(handle)


def test_power_bi_project_has_expected_pages_and_model() -> None:
    project_path = POWER_BI / "HealthcareClaimsAnalytics.pbip"
    pages_path = POWER_BI / "HealthcareClaimsAnalytics.Report" / "definition" / "pages" / "pages.json"
    model_path = POWER_BI / "HealthcareClaimsAnalytics.SemanticModel" / "model.bim"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))["model"]

    assert project["$schema"] == (
        "https://developer.microsoft.com/json-schemas/fabric/pbip/"
        "pbipProperties/1.0.0/schema.json"
    )
    assert len(pages["pageOrder"]) == 5
    assert pages["activePageName"] in pages["pageOrder"]
    assert {table["name"] for table in model["tables"]} == {"Date", "Member", "Provider", "Claim"}
    claim = next(table for table in model["tables"] if table["name"] == "Claim")
    assert len(claim["measures"]) >= 16
    assert len(model["relationships"]) == 3


def test_release_documentation_and_deployment_assets_exist() -> None:
    required = [
        ROOT / "Dockerfile",
        ROOT / ".dockerignore",
        ROOT / ".streamlit" / "config.toml",
        ROOT / "docs" / "business_requirements.md",
        ROOT / "docs" / "kpi_catalog.md",
        ROOT / "docs" / "uat_test_plan.md",
        ROOT / "docs" / "deployment.md",
    ]
    assert all(path.is_file() and path.stat().st_size > 0 for path in required)
