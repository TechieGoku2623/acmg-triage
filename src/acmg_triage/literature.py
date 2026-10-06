"""Cache-only literature nodes (PS3, BS3, PP4). Never a live API."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from acmg_triage.codes import CODE_INDEX
from acmg_triage.config import get_settings
from acmg_triage.schemas import EvidenceCall

LITERATURE_NODES: tuple[str, ...] = ("PS3", "BS3", "PP4")


@lru_cache(maxsize=1)
def load_cache() -> dict[str, Any]:
    return json.loads(get_settings().literature_cache_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def literature_call(hgvs: str, code: str, *, skipped: bool = False) -> EvidenceCall:
    """Return a cache-only evidence call. Uncited applied=true is not allowed."""

    spec = CODE_INDEX[code]
    cache = load_cache()
    entries = cache.get("entries", {})
    variant_entry = entries.get(hgvs, {})
    raw = variant_entry.get(code)
    if skipped:
        return EvidenceCall(
            code=code,
            applied=False,
            strength=spec.default_strength,
            direction=spec.direction,
            rationale="Skipped after BA1 stand-alone short-circuit. No literature-node call.",
            sources=["literature_cache", "ba1_short_circuit"],
        )
    if raw is None:
        return EvidenceCall(
            code=code,
            applied=False,
            strength=spec.default_strength,
            direction=spec.direction,
            rationale=(
                f"No committed cache entry for {code} on {hgvs}. Live literature API is forbidden."
            ),
            sources=["literature_cache"],
        )
    applied = bool(raw.get("applied"))
    excerpt_id = raw.get("excerpt_id")
    span = raw.get("span")
    if applied and not (excerpt_id and span):
        raise RuntimeError(
            f"uncited {code} applied=true for {hgvs}; cache must carry excerpt_id and span"
        )
    sources = ["literature_cache"]
    if excerpt_id:
        sources.append(f"excerpt:{excerpt_id}")
    rationale = str(raw.get("rationale", "cache entry"))
    if span:
        rationale = f"{rationale} Span: {span}"
    return EvidenceCall(
        code=code,
        applied=applied,
        strength=spec.default_strength,
        direction=spec.direction,
        rationale=rationale,
        sources=sources,
    )


def literature_nodes(hgvs: str, *, skipped: bool = False) -> list[EvidenceCall]:
    return [literature_call(hgvs, code, skipped=skipped) for code in LITERATURE_NODES]
