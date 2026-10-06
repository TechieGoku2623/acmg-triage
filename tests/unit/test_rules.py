from __future__ import annotations

import json
from pathlib import Path

from acmg_triage.codes import RULES_CODES, computability_split
from acmg_triage.combining import combine
from acmg_triage.rules import applied_codes, apply_default_rules
from acmg_triage.schemas import ProbeVariant, SampleVariant

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "sample" / "variants.json"


def _sample(sample_id: str) -> ProbeVariant:
    raw = json.loads(SAMPLES.read_text(encoding="utf-8"))
    for item in raw["variants"]:
        sample = SampleVariant.model_validate(item)
        if sample.sample_id == sample_id:
            return sample.features
    raise AssertionError(sample_id)


def test_computability_covers_28_codes() -> None:
    split = computability_split()
    assert split.n_total == 28
    assert split.n_rules + split.n_catalog + split.n_literature_llm == 28
    assert set(RULES_CODES) == {
        "PVS1",
        "PM2",
        "PM4",
        "PP3",
        "BA1",
        "BS1",
        "BP4",
        "BP7",
    }


def test_s1_frameshift_fires_pvs1_and_pm2() -> None:
    calls = apply_default_rules(_sample("S1-pathogenic-frameshift"))
    assert set(applied_codes(calls)) == {"PVS1", "PM2"}
    assert combine(calls).classification == "Likely pathogenic"


def test_s2_ba1_short_circuits() -> None:
    calls = apply_default_rules(_sample("S2-ba1-short-circuit"))
    result = combine(calls)
    assert result.short_circuited_ba1 is True
    assert result.classification == "Benign"
    assert "PP3" not in result.applied_codes


def test_s3_conflict_is_not_collapsed() -> None:
    calls = apply_default_rules(_sample("S3-conflicting-vus"))
    result = combine(calls)
    assert "PM2" in result.applied_codes
    assert "BP4" in result.applied_codes
    assert result.classification == "Conflicting"


def test_s4_default_pm2_fires_on_extremely_low_af() -> None:
    calls = apply_default_rules(_sample("S4-clingen-pm2-override"))
    assert "PM2" in applied_codes(calls)
    assert "BA1" not in applied_codes(calls)


def test_s5_without_lof_does_not_fire_pvs1() -> None:
    calls = apply_default_rules(_sample("S5-insufficient-evidence"))
    assert "PVS1" not in applied_codes(calls)
