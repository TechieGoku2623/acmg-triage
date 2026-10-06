"""Data contracts for probe records, evidence calls, and classification trails."""

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


class NodeTrace(BaseModel):
    """One graph node execution record."""

    node: str
    code: str | None = None
    applied: bool | None = None
    skipped: bool = False
    rationale: str
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    sources: list[str] = Field(default_factory=list)


class OverlayDiff(BaseModel):
    """Default 2015 call versus gene-specific VCEP overlay for one code."""

    code: str
    default_applied: bool
    overlay_applied: bool
    default_strength: Strength | None = None
    overlay_strength: Strength | None = None
    default_rationale: str
    overlay_rationale: str


class DecisionTrace(BaseModel):
    """Persisted classification trail. Inputs, codes, rationale, cost, latency."""

    hgvs: str
    gene: str
    sample_id: str | None = None
    inputs: dict[str, object] = Field(default_factory=dict)
    catalog_covered: bool
    insufficient_evidence: bool = False
    classification: Classification | None = None
    default_classification: Classification | None = None
    overlay_classification: Classification | None = None
    conflicting: bool = False
    short_circuited_ba1: bool = False
    applied_codes: list[str] = Field(default_factory=list)
    skipped_codes: list[str] = Field(default_factory=list)
    calls: list[EvidenceCall] = Field(default_factory=list)
    overlay_diffs: list[OverlayDiff] = Field(default_factory=list)
    nodes: list[NodeTrace] = Field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    disclaimer: str


class ClassificationResult(BaseModel):
    """Public classify payload: full trail plus the safety disclaimer."""

    hgvs: str
    gene: str
    sample_id: str | None = None
    classification: Classification | None = None
    default_classification: Classification | None = None
    overlay_classification: Classification | None = None
    insufficient_evidence: bool = False
    conflicting: bool = False
    short_circuited_ba1: bool = False
    matched_rule: str | None = None
    applied_codes: list[str] = Field(default_factory=list)
    skipped_codes: list[str] = Field(default_factory=list)
    calls: list[EvidenceCall] = Field(default_factory=list)
    overlay_diffs: list[OverlayDiff] = Field(default_factory=list)
    nodes: list[NodeTrace] = Field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    confidence: float = 0.0
    disclaimer: str
    trace: DecisionTrace
