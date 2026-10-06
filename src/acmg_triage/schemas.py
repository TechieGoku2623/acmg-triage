"""Data contracts for Phase 0 probe records and evidence calls."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from acmg_triage.codes import Direction, Strength

Consequence = Literal[
    "frameshift",
    "stop_gained",
    "missense",
    "synonymous",
    "inframe_indel",
    "splice_acceptor",
    "splice_donor",
    "intronic",
    "stop_lost",
]

Classification = Literal[
    "Pathogenic",
    "Likely pathogenic",
    "Uncertain significance",
    "Likely benign",
    "Benign",
    "Conflicting",
]


class EvidenceCall(BaseModel):
    """One applied or declined ACMG/AMP evidence code."""

    code: str
    applied: bool
    strength: Strength | None = None
    direction: Direction | None = None
    rationale: str
    sources: list[str] = Field(default_factory=list)


class ProbeVariant(BaseModel):
    """One committed probe record for Phase 0 harnesses.

    Gold codes are VCEP-style published assignments, not the output of the
    default 2015 rule implementations in ``acmg_triage.rules``.
    """

    variant_id: str
    hgvs: str
    gene: str
    consequence: Consequence
    gnomad_af: float = Field(ge=0.0, le=1.0)
    revel: float | None = Field(default=None, ge=0.0, le=1.0)
    spliceai_max: float | None = Field(default=None, ge=0.0, le=1.0)
    lof_mechanism_established: bool
    last_exon: bool = False
    clingen_vcep: str | None = None
    vcep_ba1_af: float | None = None
    vcep_bs1_af: float | None = None
    vcep_pm2_requires_absent: bool = False
    vcep_pm2_supporting_only: bool = False
    vcep_pp3_revel: float | None = None
    vcep_bp4_revel: float | None = None
    vcep_pvs1_max_strength: Strength | None = None
    gold_codes: list[str]
    gold_strengths: dict[str, Strength] = Field(default_factory=dict)
    gold_class: Classification
    gold_source: str
    cohort: str
    notes: str = ""


class SampleVariant(BaseModel):
    """One of the five designed demo variants."""

    sample_id: str
    hgvs: str
    gene: str
    path_exercised: str
    why_present: str
    expected_behavior: str
    features: ProbeVariant
