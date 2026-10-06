from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from acmg_triage.api import app as api_app
from acmg_triage.batch import classify_vcf, parse_vcf
from acmg_triage.catalog import coverage_for
from acmg_triage.classify import classify_hgvs, classify_variant, resolve_variant
from acmg_triage.cli import app
from acmg_triage.literature import literature_call
from acmg_triage.schemas import SampleVariant

runner = CliRunner()
SAMPLES = Path(__file__).resolve().parents[2] / "data" / "sample" / "variants.json"


def _sample(sample_id: str) -> SampleVariant:
    raw = json.loads(SAMPLES.read_text(encoding="utf-8"))
    for item in raw["variants"]:
        sample = SampleVariant.model_validate(item)
        if sample.sample_id == sample_id:
            return sample
    raise AssertionError(sample_id)


def test_s1_likely_pathogenic_trail() -> None:
    result = classify_hgvs("NM_000059.4:c.5946del")
    assert result.insufficient_evidence is False
    assert result.classification == "Likely pathogenic"
    assert set(result.applied_codes) >= {"PVS1", "PM2"}
    assert result.cost_usd == 0.0
    assert result.disclaimer.startswith("Research tool only")
    assert result.confidence > 0


def test_s2_ba1_lists_skipped_codes() -> None:
    result = classify_hgvs("NM_000059.4:c.1114A>C")
    assert result.classification == "Benign"
    assert result.short_circuited_ba1 is True
    assert result.applied_codes == ["BA1"]
    assert "PP3" in result.skipped_codes
    assert "PS3" in result.skipped_codes
    assert "BS3" in result.skipped_codes
    assert "PP4" in result.skipped_codes


def test_s3_conflicting() -> None:
    result = classify_hgvs("NM_000059.4:c.2311G>A")
    assert result.conflicting is True
    assert result.classification == "Conflicting"
    assert "PM2" in result.applied_codes
    assert "BP4" in result.applied_codes


def test_s5_insufficient_not_a_guess() -> None:
    result = classify_hgvs("NM_001005237.2:c.200A>G")
    assert coverage_for("OR8U1").covered is False
    assert result.insufficient_evidence is True
    assert result.classification is None
    assert result.confidence == 0.0
    assert result.applied_codes == []


def test_s4_reports_default_and_overlay_pm2() -> None:
    result = classify_variant(_sample("S4-clingen-pm2-override").features, "S4")
    assert result.default_classification is not None
    diffs = {d.code: d for d in result.overlay_diffs}
    assert diffs["PM2"].default_applied is True
    assert diffs["PM2"].overlay_applied is False


def test_cli_classify_explain_and_json() -> None:
    explained = runner.invoke(app, ["classify", "--hgvs", "NM_000059.4:c.5946del", "--explain"])
    assert explained.exit_code == 0, explained.stdout
    assert "Likely pathogenic" in explained.stdout
    assert "Research tool only" in explained.stdout
    dumped = runner.invoke(app, ["classify", "--hgvs", "NM_000059.4:c.2311G>A", "--json"])
    assert dumped.exit_code == 0
    payload = json.loads(dumped.stdout)
    assert payload["conflicting"] is True
    refused = runner.invoke(app, ["classify", "--hgvs", "NM_001005237.2:c.200A>G"])
    assert refused.exit_code == 0
    assert "INSUFFICIENT EVIDENCE" in refused.stdout


def test_cli_unknown_hgvs() -> None:
    result = runner.invoke(app, ["classify", "--hgvs", "NM_999999.1:c.1A>G"])
    assert result.exit_code == 2


def test_batch_five_rows() -> None:
    path = Path(__file__).resolve().parents[2] / "data" / "sample" / "demo.vcf"
    rows = parse_vcf(path)
    assert len(rows) == 5
    pairs = classify_vcf(path)
    labels = {
        row.row_id: (
            "insufficient"
            if result.insufficient_evidence
            else ("conflicting" if result.conflicting else result.classification)
        )
        for row, result in pairs
    }
    assert labels["S1"] == "Likely pathogenic"
    assert labels["S2"] == "Benign"
    assert labels["S3"] == "conflicting"
    assert labels["S5"] == "insufficient"
    batched = runner.invoke(app, ["batch"])
    assert batched.exit_code == 0
    assert "INSUFFICIENT EVIDENCE" in batched.stdout


def test_literature_never_applies_without_citation() -> None:
    call = literature_call("NM_000059.4:c.5946del", "PS3")
    assert call.applied is False
    assert "cache" in ",".join(call.sources)


def test_api_classify() -> None:
    client = TestClient(api_app)
    health = client.get("/health")
    assert health.status_code == 200
    assert "licensed molecular geneticist" in health.json()["disclaimer"]
    response = client.post("/classify", json={"hgvs": "NM_000059.4:c.5946del"})
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "Likely pathogenic"
    assert "trace" in body
    assert body["disclaimer"].startswith("Research tool only")
    missing = client.post("/classify", json={"hgvs": "NM_999999.1:c.1A>G"})
    assert missing.status_code == 404


def test_resolve_probe_variant() -> None:
    variant, vid = resolve_variant("NM_000059.4:c.1001A>G")
    assert variant.gene == "BRCA2"
    assert vid == "BA1-BOTH-01"
