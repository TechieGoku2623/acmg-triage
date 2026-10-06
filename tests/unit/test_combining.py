"""The combining table is data. These tests are the published-row diff."""

from __future__ import annotations

from acmg_triage.combining import BENIGN_RULES, PATHOGENIC_RULES, calls_from_codes, combine


def test_table_has_published_pathogenic_rows() -> None:
    labels = [rule.label for rule in PATHOGENIC_RULES]
    assert labels.count("Pathogenic") == 8
    assert labels.count("Likely pathogenic") == 6


def test_table_has_published_benign_rows() -> None:
    labels = [rule.label for rule in BENIGN_RULES]
    assert labels.count("Benign") == 2
    assert labels.count("Likely benign") == 2


def test_ba1_short_circuit_skips_other_codes() -> None:
    result = combine(calls_from_codes(["BA1", "PP3"]))
    assert result.classification == "Benign"
    assert result.short_circuited_ba1 is True
    assert result.applied_codes == ["BA1"]
    assert "PP3" in result.skipped_codes


def test_pvs1_plus_moderate_pm2_is_likely_pathogenic() -> None:
    result = combine(calls_from_codes(["PVS1", "PM2"]))
    assert result.classification == "Likely pathogenic"


def test_pvs1_plus_supporting_pm2_is_vus() -> None:
    """ClinGen SVI PM2-as-supporting does not meet 1 VS + 1 moderate."""

    result = combine(calls_from_codes(["PVS1", "PM2"], {"PM2": "supporting"}))
    assert result.classification == "Uncertain significance"


def test_pvs1_pm2_pp3_is_pathogenic() -> None:
    result = combine(calls_from_codes(["PVS1", "PM2", "PP3"]))
    assert result.classification == "Pathogenic"


def test_pm2_and_bp4_is_conflicting() -> None:
    result = combine(calls_from_codes(["PM2", "BP4"]))
    assert result.classification == "Conflicting"
    assert result.conflicting is True


def test_two_supporting_benign_is_likely_benign() -> None:
    result = combine(calls_from_codes(["BP4", "BP7"]))
    assert result.classification == "Likely benign"


def test_empty_is_vus() -> None:
    result = combine([])
    assert result.classification == "Uncertain significance"
