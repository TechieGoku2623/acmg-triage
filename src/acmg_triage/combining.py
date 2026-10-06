"""Declarative ACMG/AMP 2015 combining table.

Richards et al., Genet Med 2015;17:405-424, Tables 5. The table is data, not
nested conditionals, so tests can diff it against the published rows.

This module does not implement later Bayesian point-based systems (Tavtigian
2018/2020). Conflict policy: any pathogenic-leaning call plus any benign-leaning
call yields Conflicting, except BA1 stand-alone which short-circuits to Benign
before other codes are considered.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field

from acmg_triage.codes import CODE_INDEX, Direction, Strength
from acmg_triage.schemas import Classification, EvidenceCall

Bucket = Literal["stand_alone", "very_strong", "strong", "moderate", "supporting"]


class CombiningRule(BaseModel):
    """One row of the published combining table."""

    label: Classification
    direction: Direction
    min_counts: dict[Bucket, int]
    citation: str = "Richards 2015 Table 5"


# Pathogenic / likely pathogenic rows. A row matches when every listed bucket
# meets its minimum. Extra evidence in other buckets does not block a match.
PATHOGENIC_RULES: tuple[CombiningRule, ...] = (
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"very_strong": 1, "strong": 1},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"very_strong": 1, "moderate": 2},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"very_strong": 1, "moderate": 1, "supporting": 1},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"very_strong": 1, "supporting": 2},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"strong": 2},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"strong": 1, "moderate": 3},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"strong": 1, "moderate": 2, "supporting": 2},
    ),
    CombiningRule(
        label="Pathogenic",
        direction="pathogenic",
        min_counts={"strong": 1, "moderate": 1, "supporting": 4},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"very_strong": 1, "moderate": 1},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"strong": 1, "moderate": 1},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"strong": 1, "supporting": 2},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"moderate": 3},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"moderate": 2, "supporting": 2},
    ),
    CombiningRule(
        label="Likely pathogenic",
        direction="pathogenic",
        min_counts={"moderate": 1, "supporting": 4},
    ),
)

BENIGN_RULES: tuple[CombiningRule, ...] = (
    CombiningRule(
        label="Benign",
        direction="benign",
        min_counts={"stand_alone": 1},
    ),
    CombiningRule(
        label="Benign",
        direction="benign",
        min_counts={"strong": 2},
    ),
    CombiningRule(
        label="Likely benign",
        direction="benign",
        min_counts={"strong": 1, "supporting": 1},
    ),
    CombiningRule(
        label="Likely benign",
        direction="benign",
        min_counts={"supporting": 2},
    ),
)


class CombiningResult(BaseModel):
    classification: Classification
    pathogenic_counts: dict[str, int]
    benign_counts: dict[str, int]
    matched_rule: str | None
    short_circuited_ba1: bool = False
    conflicting: bool = False
    applied_codes: list[str] = Field(default_factory=list)
    skipped_codes: list[str] = Field(default_factory=list)


def _counts(calls: list[EvidenceCall], direction: Direction) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for call in calls:
        if call.applied and call.direction == direction and call.strength is not None:
            counter[call.strength] += 1
    return {
        "stand_alone": counter["stand_alone"],
        "very_strong": counter["very_strong"],
        "strong": counter["strong"],
        "moderate": counter["moderate"],
        "supporting": counter["supporting"],
    }


def _matches(counts: dict[str, int], rule: CombiningRule) -> bool:
    return all(counts.get(bucket, 0) >= minimum for bucket, minimum in rule.min_counts.items())


def _best_label(
    counts: dict[str, int], rules: tuple[CombiningRule, ...]
) -> tuple[Classification | None, str | None]:
    for rule in rules:
        if _matches(counts, rule):
            mins = ", ".join(f"{k}>={v}" for k, v in rule.min_counts.items())
            return rule.label, f"{rule.label}: {mins}"
    return None, None


def combine(calls: list[EvidenceCall], *, honor_ba1_short_circuit: bool = True) -> CombiningResult:
    """Apply the declarative 2015 table to a list of evidence calls."""

    applied = [c for c in calls if c.applied]
    skipped = [c.code for c in calls if not c.applied]
    ba1 = next((c for c in applied if c.code == "BA1"), None)
    if honor_ba1_short_circuit and ba1 is not None:
        return CombiningResult(
            classification="Benign",
            pathogenic_counts=_counts([], "pathogenic"),
            benign_counts=_counts([ba1], "benign"),
            matched_rule="BA1 stand-alone short-circuit",
            short_circuited_ba1=True,
            applied_codes=["BA1"],
            skipped_codes=sorted({*skipped, *[c.code for c in applied if c.code != "BA1"]}),
        )

    p_counts = _counts(applied, "pathogenic")
    b_counts = _counts(applied, "benign")
    p_label, p_rule = _best_label(p_counts, PATHOGENIC_RULES)
    b_label, b_rule = _best_label(b_counts, BENIGN_RULES)

    has_p = any(c.direction == "pathogenic" for c in applied)
    has_b = any(c.direction == "benign" for c in applied)
    if has_p and has_b:
        return CombiningResult(
            classification="Conflicting",
            pathogenic_counts=p_counts,
            benign_counts=b_counts,
            matched_rule=None,
            conflicting=True,
            applied_codes=[c.code for c in applied],
            skipped_codes=skipped,
        )

    if p_label is not None:
        return CombiningResult(
            classification=p_label,
            pathogenic_counts=p_counts,
            benign_counts=b_counts,
            matched_rule=p_rule,
            applied_codes=[c.code for c in applied],
            skipped_codes=skipped,
        )
    if b_label is not None:
        return CombiningResult(
            classification=b_label,
            pathogenic_counts=p_counts,
            benign_counts=b_counts,
            matched_rule=b_rule,
            applied_codes=[c.code for c in applied],
            skipped_codes=skipped,
        )
    return CombiningResult(
        classification="Uncertain significance",
        pathogenic_counts=p_counts,
        benign_counts=b_counts,
        matched_rule=None,
        applied_codes=[c.code for c in applied],
        skipped_codes=skipped,
    )


def calls_from_codes(
    codes: list[str],
    strengths: dict[str, Strength] | None = None,
) -> list[EvidenceCall]:
    """Build evidence calls from code names, honoring optional strength overrides."""

    overrides = strengths or {}
    calls: list[EvidenceCall] = []
    for code in codes:
        spec = CODE_INDEX[code]
        strength = overrides.get(code, spec.default_strength)
        calls.append(
            EvidenceCall(
                code=code,
                applied=True,
                strength=strength,
                direction=spec.direction,
                rationale="gold or predicted code list",
                sources=[],
            )
        )
    return calls
