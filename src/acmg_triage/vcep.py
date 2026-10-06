"""Gene-specific VCEP overlay. Reports default and overlay; never silently picks."""

from __future__ import annotations

from acmg_triage.codes import CODE_INDEX
from acmg_triage.rules import (
    DEFAULT_BA1_AF,
    DEFAULT_BP4_REVEL,
    DEFAULT_BS1_AF,
    DEFAULT_PM2_AF,
    DEFAULT_PP3_REVEL,
    NULL_CONSEQUENCES,
    apply_default_rules,
)
from acmg_triage.schemas import EvidenceCall, OverlayDiff, ProbeVariant


def _call(code: str, applied: bool, rationale: str, strength: str | None = None) -> EvidenceCall:
    spec = CODE_INDEX[code]
    return EvidenceCall(
        code=code,
        applied=applied,
        strength=strength or spec.default_strength,  # type: ignore[arg-type]
        direction=spec.direction,
        rationale=rationale,
        sources=["acmg_triage.vcep"],
    )


def apply_vcep_overlay(variant: ProbeVariant) -> list[EvidenceCall]:
    """Re-evaluate overlay-sensitive codes using committed VCEP fields."""

    calls: list[EvidenceCall] = []
    ba1_cut = variant.vcep_ba1_af if variant.vcep_ba1_af is not None else DEFAULT_BA1_AF
    bs1_cut = variant.vcep_bs1_af if variant.vcep_bs1_af is not None else DEFAULT_BS1_AF
    pp3_cut = variant.vcep_pp3_revel if variant.vcep_pp3_revel is not None else DEFAULT_PP3_REVEL
    bp4_cut = variant.vcep_bp4_revel if variant.vcep_bp4_revel is not None else DEFAULT_BP4_REVEL

    if variant.gnomad_af >= ba1_cut:
        calls.append(_call("BA1", True, f"gnomAD AF {variant.gnomad_af:.6g} >= VCEP BA1 {ba1_cut}"))
    else:
        calls.append(_call("BA1", False, f"gnomAD AF {variant.gnomad_af:.6g} < VCEP BA1 {ba1_cut}"))

    if bs1_cut <= variant.gnomad_af < ba1_cut:
        calls.append(_call("BS1", True, f"gnomAD AF {variant.gnomad_af:.6g} >= VCEP BS1 {bs1_cut}"))
    else:
        calls.append(
            _call(
                "BS1",
                False,
                f"gnomAD AF {variant.gnomad_af:.6g} outside VCEP [{bs1_cut}, {ba1_cut})",
            )
        )

    if variant.vcep_pm2_requires_absent:
        pm2_applied = variant.gnomad_af == 0.0
        why = "VCEP PM2 requires absence from gnomAD"
    else:
        pm2_applied = variant.gnomad_af == 0.0 or variant.gnomad_af < DEFAULT_PM2_AF
        why = f"VCEP PM2 uses default extremely-low cutoff {DEFAULT_PM2_AF}"
    pm2_strength = "supporting" if variant.vcep_pm2_supporting_only else None
    calls.append(
        _call(
            "PM2",
            pm2_applied,
            f"{why}; AF {variant.gnomad_af:.6g}",
            strength=pm2_strength,
        )
    )

    if variant.consequence in NULL_CONSEQUENCES and variant.lof_mechanism_established:
        strength = variant.vcep_pvs1_max_strength
        extra = ""
        if variant.last_exon and strength is not None:
            extra = f" last-exon capped at {strength}"
        elif variant.last_exon:
            extra = " last-exon; no VCEP cap recorded"
        calls.append(_call("PVS1", True, f"{variant.consequence} in LOF gene.{extra}", strength))
    else:
        calls.append(
            _call(
                "PVS1",
                False,
                f"consequence={variant.consequence} lof={variant.lof_mechanism_established}",
            )
        )

    if variant.consequence in {"inframe_indel", "stop_lost"}:
        calls.append(_call("PM4", True, f"length-changing consequence {variant.consequence}"))
    else:
        calls.append(
            _call("PM4", False, f"consequence {variant.consequence} is not a length change")
        )

    if variant.revel is not None and variant.revel >= pp3_cut:
        calls.append(_call("PP3", True, f"REVEL {variant.revel:.3f} >= VCEP PP3 {pp3_cut}"))
    else:
        shown = "None" if variant.revel is None else f"{variant.revel:.3f}"
        calls.append(_call("PP3", False, f"REVEL {shown} below VCEP PP3 {pp3_cut}"))

    if variant.revel is not None and variant.revel <= bp4_cut:
        calls.append(_call("BP4", True, f"REVEL {variant.revel:.3f} <= VCEP BP4 {bp4_cut}"))
    else:
        shown = "None" if variant.revel is None else f"{variant.revel:.3f}"
        calls.append(_call("BP4", False, f"REVEL {shown} above VCEP BP4 {bp4_cut}"))

    splice = variant.spliceai_max
    if variant.consequence == "synonymous" and splice is not None and splice < 0.10:
        calls.append(_call("BP7", True, f"synonymous and SpliceAI {splice:.3f} < 0.10"))
    else:
        calls.append(_call("BP7", False, f"consequence={variant.consequence} spliceai={splice}"))
    return calls


def overlay_diffs(variant: ProbeVariant) -> list[OverlayDiff]:
    default = {c.code: c for c in apply_default_rules(variant)}
    overlay = {c.code: c for c in apply_vcep_overlay(variant)}
    diffs: list[OverlayDiff] = []
    for code in sorted(set(default) | set(overlay)):
        d = default[code]
        o = overlay[code]
        if d.applied != o.applied or d.strength != o.strength or bool(variant.clingen_vcep):
            diffs.append(
                OverlayDiff(
                    code=code,
                    default_applied=d.applied,
                    overlay_applied=o.applied,
                    default_strength=d.strength,
                    overlay_strength=o.strength,
                    default_rationale=d.rationale,
                    overlay_rationale=o.rationale,
                )
            )
    return diffs
