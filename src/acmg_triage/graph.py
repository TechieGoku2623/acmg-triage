"""Thin typed graph: one node per rules code, cache-only literature nodes.

LangGraph-shaped runner over existing ``apply_default_rules``, ``apply_vcep_overlay``,
``literature_nodes``, and ``combine``. No live LLM. Typed state. Decision trace
is assembled here and persisted by ``classify``.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from pydantic import BaseModel, Field

from acmg_triage.catalog import coverage_for
from acmg_triage.codes import RULES_CODES
from acmg_triage.combining import combine
from acmg_triage.literature import LITERATURE_NODES, literature_call
from acmg_triage.rules import apply_default_rules
from acmg_triage.schemas import (
    Classification,
    EvidenceCall,
    NodeTrace,
    OverlayDiff,
    ProbeVariant,
)
from acmg_triage.vcep import apply_vcep_overlay, overlay_diffs

NodeFn = Callable[["GraphState"], "GraphState"]


class GraphState(BaseModel):
    """Typed graph state passed between nodes."""

    variant: ProbeVariant
    catalog_covered: bool = False
    catalog_rationale: str = ""
    insufficient_evidence: bool = False
    ba1_short_circuit: bool = False
    default_by_code: dict[str, EvidenceCall] = Field(default_factory=dict)
    overlay_by_code: dict[str, EvidenceCall] = Field(default_factory=dict)
    literature: list[EvidenceCall] = Field(default_factory=list)
    final_calls: list[EvidenceCall] = Field(default_factory=list)
    skipped_codes: list[str] = Field(default_factory=list)
    overlay_diffs: list[OverlayDiff] = Field(default_factory=list)
    nodes: list[NodeTrace] = Field(default_factory=list)
    classification: Classification | None = None
    default_classification: Classification | None = None
    overlay_classification: Classification | None = None
    conflicting: bool = False
    matched_rule: str | None = None
    cost_usd: float = 0.0
    latency_ms: float = 0.0


def _trace(
    state: GraphState,
    node: str,
    rationale: str,
    *,
    code: str | None = None,
    applied: bool | None = None,
    skipped: bool = False,
    latency_ms: float = 0.0,
) -> None:
    state.nodes.append(
        NodeTrace(
            node=node,
            code=code,
            applied=applied,
            skipped=skipped,
            rationale=rationale,
            latency_ms=latency_ms,
            cost_usd=0.0,
            sources=["graph"],
        )
    )


def node_catalog(state: GraphState) -> GraphState:
    t0 = time.perf_counter()
    cov = coverage_for(state.variant.gene)
    state.catalog_covered = cov.covered
    state.catalog_rationale = cov.rationale
    if not cov.covered:
        state.insufficient_evidence = True
        state.classification = None
    _trace(
        state,
        "catalog",
        cov.rationale,
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return state


def _rules_node(code: str) -> NodeFn:
    def _node(state: GraphState) -> GraphState:
        t0 = time.perf_counter()
        if state.insufficient_evidence:
            _trace(
                state,
                f"rules_{code}",
                "Not run: insufficient catalog coverage.",
                code=code,
                skipped=True,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
            return state
        if state.ba1_short_circuit and code != "BA1":
            state.skipped_codes.append(code)
            _trace(
                state,
                f"rules_{code}",
                "Skipped after BA1 stand-alone short-circuit.",
                code=code,
                skipped=True,
                applied=False,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
            return state
        call = state.default_by_code[code]
        if code == "BA1" and call.applied:
            state.ba1_short_circuit = True
        _trace(
            state,
            f"rules_{code}",
            call.rationale,
            code=code,
            applied=call.applied,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return state

    _node.__name__ = f"node_{code.lower()}"
    return _node


def node_vcep(state: GraphState) -> GraphState:
    t0 = time.perf_counter()
    if state.insufficient_evidence:
        _trace(
            state,
            "vcep_overlay",
            "Not run: insufficient catalog coverage.",
            skipped=True,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return state
    state.overlay_diffs = overlay_diffs(state.variant)
    n_diff = sum(
        1
        for d in state.overlay_diffs
        if d.default_applied != d.overlay_applied or d.default_strength != d.overlay_strength
    )
    _trace(
        state,
        "vcep_overlay",
        (
            f"VCEP {state.variant.clingen_vcep or 'none'}: "
            f"{n_diff} codes differ from default 2015. Both reported."
        ),
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return state


def _lit_node(code: str) -> NodeFn:
    def _node(state: GraphState) -> GraphState:
        t0 = time.perf_counter()
        if state.insufficient_evidence:
            _trace(
                state,
                f"literature_{code}",
                "Not run: insufficient catalog coverage.",
                code=code,
                skipped=True,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
            return state
        skipped = state.ba1_short_circuit
        call = literature_call(state.variant.hgvs, code, skipped=skipped)
        state.literature.append(call)
        state.cost_usd += 0.0
        _trace(
            state,
            f"literature_{code}",
            call.rationale,
            code=code,
            applied=call.applied,
            skipped=skipped,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return state

    _node.__name__ = f"node_lit_{code.lower()}"
    return _node


def node_combine(state: GraphState) -> GraphState:
    t0 = time.perf_counter()
    if state.insufficient_evidence:
        _trace(
            state,
            "combine",
            "No ACMG tier: insufficient evidence (no catalog coverage).",
            skipped=True,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return state

    default_calls = list(state.default_by_code.values())
    overlay_calls = list(state.overlay_by_code.values())
    default_result = combine(default_calls)
    overlay_result = combine(overlay_calls)
    state.default_classification = default_result.classification
    state.overlay_classification = overlay_result.classification

    # Primary trail is default 2015 + literature (cache). VCEP is reported, not silent.
    lit_applied = [c for c in state.literature if c.applied]
    if state.ba1_short_circuit:
        state.final_calls = [state.default_by_code["BA1"]]
        result = combine(default_calls)
        extra_skip = [c for c in LITERATURE_NODES]
        state.skipped_codes = sorted(set(result.skipped_codes + extra_skip + state.skipped_codes))
    else:
        state.final_calls = [c for c in default_calls if c.applied] + lit_applied
        result = combine(default_calls + state.literature)
        state.skipped_codes = sorted(set(result.skipped_codes + state.skipped_codes))

    state.classification = result.classification
    state.conflicting = result.conflicting or result.classification == "Conflicting"
    state.matched_rule = result.matched_rule
    state.ba1_short_circuit = result.short_circuited_ba1 or state.ba1_short_circuit
    _trace(
        state,
        "combine",
        result.matched_rule
        or (
            "CONFLICTING EVIDENCE" if state.conflicting else f"2015 table → {result.classification}"
        ),
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return state


RULE_NODES: dict[str, NodeFn] = {code: _rules_node(code) for code in RULES_CODES}
# BA1 first so the short-circuit can skip the rest.
NODE_ORDER: list[tuple[str, NodeFn]] = [
    ("catalog", node_catalog),
    ("BA1", RULE_NODES["BA1"]),
    *[(code, RULE_NODES[code]) for code in RULES_CODES if code != "BA1"],
    ("vcep", node_vcep),
    *[(f"lit_{code}", _lit_node(code)) for code in LITERATURE_NODES],
    ("combine", node_combine),
]


def run_graph(variant: ProbeVariant) -> GraphState:
    """Execute the thin graph. Cost is always 0 (cache / rules only)."""

    t0 = time.perf_counter()
    default_calls = apply_default_rules(variant)
    overlay_calls = apply_vcep_overlay(variant)
    state = GraphState(
        variant=variant,
        default_by_code={c.code: c for c in default_calls},
        overlay_by_code={c.code: c for c in overlay_calls},
    )
    for _name, fn in NODE_ORDER:
        state = fn(state)
    state.latency_ms = (time.perf_counter() - t0) * 1000
    state.cost_usd = 0.0
    return state
