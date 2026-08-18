"""Configuration checks for reproducible portfolio scale profiles."""

from etl.generate_data import SCALE_PROFILES


def test_documented_claim_scale_profiles() -> None:
    demo = SCALE_PROFILES["demo"]
    medium = SCALE_PROFILES["medium"]
    large = SCALE_PROFILES["large"]
    assert sum(demo[2:5]) == 40_000
    assert sum(medium[2:5]) == 300_000
    assert sum(large[2:5]) == 1_000_000
    assert demo < medium < large
