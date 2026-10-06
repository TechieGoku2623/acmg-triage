"""Committed gene catalog coverage. Not a live ClinVar / ClinGen query."""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import BaseModel, Field

from acmg_triage.config import get_settings


class GeneCoverage(BaseModel):
    gene: str
    covered: bool
    clingen_vcep: str | None = None
    source: str = "committed sample catalog"
    rationale: str


class CatalogSnapshot(BaseModel):
    snapshot_id: str
    genes: dict[str, GeneCoverage] = Field(default_factory=dict)
    disclaimer: str = ""


@lru_cache(maxsize=1)
def load_catalog() -> CatalogSnapshot:
    raw = json.loads(get_settings().catalog_path.read_text(encoding="utf-8"))
    genes: dict[str, GeneCoverage] = {}
    for symbol, item in raw["genes"].items():
        genes[symbol] = GeneCoverage(
            gene=symbol,
            covered=bool(item["covered"]),
            clingen_vcep=item.get("clingen_vcep"),
            source=str(item.get("source", "committed sample catalog")),
            rationale=(
                f"{symbol} is in the committed catalog snapshot "
                f"({item.get('clingen_vcep') or 'no VCEP name'})."
            ),
        )
    return CatalogSnapshot(
        snapshot_id=str(raw["snapshot_id"]),
        genes=genes,
        disclaimer=str(raw.get("disclaimer", "")),
    )


def coverage_for(gene: str) -> GeneCoverage:
    catalog = load_catalog()
    if gene in catalog.genes and catalog.genes[gene].covered:
        return catalog.genes[gene]
    return GeneCoverage(
        gene=gene,
        covered=False,
        clingen_vcep=None,
        source="committed sample catalog",
        rationale=(
            f"{gene} has no catalog coverage in the committed snapshot "
            "(no ClinGen VCEP and no ClinVar expert-panel record). "
            "Insufficient evidence; do not guess an ACMG tier."
        ),
    )
