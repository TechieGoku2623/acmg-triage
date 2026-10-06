"""The 28 ACMG/AMP 2015 evidence codes and how each can be computed.

Richards et al., Genet Med 2015;17:405-424. This module does not implement
the later ClinGen SVI strength modifications; those live on gold labels.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Direction = Literal["pathogenic", "benign"]
Strength = Literal["stand_alone", "very_strong", "strong", "moderate", "supporting"]
Computability = Literal["rules", "catalog", "literature_llm"]


class CodeSpec(BaseModel):
    """Declarative description of one ACMG/AMP evidence code."""

    code: str
    direction: Direction
    default_strength: Strength
    computability: Computability
    rationale: str


# 28 codes from Richards 2015 Table 3 / Table 4. PP5 and BP6 are retained
# because the published table includes them; ClinGen later deprecated both.
ACMG_2015_CODES: tuple[CodeSpec, ...] = (
    CodeSpec(
        code="PVS1",
        direction="pathogenic",
        default_strength="very_strong",
        computability="rules",
        rationale="Null variant in a gene where LOF is a known mechanism; PVS1 decision tree.",
    ),
    CodeSpec(
        code="PS1",
        direction="pathogenic",
        default_strength="strong",
        computability="catalog",
        rationale="Same amino acid change as an established pathogenic variant.",
    ),
    CodeSpec(
        code="PS2",
        direction="pathogenic",
        default_strength="strong",
        computability="literature_llm",
        rationale="De novo with confirmed parentage; almost always in free text.",
    ),
    CodeSpec(
        code="PS3",
        direction="pathogenic",
        default_strength="strong",
        computability="literature_llm",
        rationale="Well-established functional studies; literature interpretation.",
    ),
    CodeSpec(
        code="PS4",
        direction="pathogenic",
        default_strength="strong",
        computability="literature_llm",
        rationale="Prevalence in affecteds statistically increased; case-control papers.",
    ),
    CodeSpec(
        code="PM1",
        direction="pathogenic",
        default_strength="moderate",
        computability="catalog",
        rationale="Mutational hotspot or critical domain without benign variation; domain catalog.",
    ),
    CodeSpec(
        code="PM2",
        direction="pathogenic",
        default_strength="moderate",
        computability="rules",
        rationale="Absent / extremely low frequency in population databases; gnomAD AF.",
    ),
    CodeSpec(
        code="PM3",
        direction="pathogenic",
        default_strength="moderate",
        computability="literature_llm",
        rationale="For recessive disorders, detected in trans with a pathogenic variant.",
    ),
    CodeSpec(
        code="PM4",
        direction="pathogenic",
        default_strength="moderate",
        computability="rules",
        rationale="Protein-length change from in-frame indel or stop-loss.",
    ),
    CodeSpec(
        code="PM5",
        direction="pathogenic",
        default_strength="moderate",
        computability="catalog",
        rationale="Novel missense at a residue where a different pathogenic missense is known.",
    ),
    CodeSpec(
        code="PM6",
        direction="pathogenic",
        default_strength="moderate",
        computability="literature_llm",
        rationale="Assumed de novo without confirmation of paternity and maternity.",
    ),
    CodeSpec(
        code="PP1",
        direction="pathogenic",
        default_strength="supporting",
        computability="literature_llm",
        rationale="Co-segregation with disease in multiple affected family members.",
    ),
    CodeSpec(
        code="PP2",
        direction="pathogenic",
        default_strength="supporting",
        computability="catalog",
        rationale="Missense in a gene with low benign missense rate.",
    ),
    CodeSpec(
        code="PP3",
        direction="pathogenic",
        default_strength="supporting",
        computability="rules",
        rationale="Multiple lines of computational evidence; in-silico score thresholds.",
    ),
    CodeSpec(
        code="PP4",
        direction="pathogenic",
        default_strength="supporting",
        computability="literature_llm",
        rationale="Phenotype highly specific for a disease with a single genetic etiology.",
    ),
    CodeSpec(
        code="PP5",
        direction="pathogenic",
        default_strength="supporting",
        computability="catalog",
        rationale="Reputable source reports pathogenic without evidence; ClinGen deprecated.",
    ),
    CodeSpec(
        code="BA1",
        direction="benign",
        default_strength="stand_alone",
        computability="rules",
        rationale="Allele frequency above the stand-alone threshold; gnomAD AF.",
    ),
    CodeSpec(
        code="BS1",
        direction="benign",
        default_strength="strong",
        computability="rules",
        rationale="Allele frequency greater than expected for the disorder.",
    ),
    CodeSpec(
        code="BS2",
        direction="benign",
        default_strength="strong",
        computability="catalog",
        rationale="Observed in a healthy adult for a full-penetrance early-onset disorder.",
    ),
    CodeSpec(
        code="BS3",
        direction="benign",
        default_strength="strong",
        computability="literature_llm",
        rationale="Well-established functional studies show no damaging effect.",
    ),
    CodeSpec(
        code="BS4",
        direction="benign",
        default_strength="strong",
        computability="literature_llm",
        rationale="Lack of segregation in affected members of a family.",
    ),
    CodeSpec(
        code="BP1",
        direction="benign",
        default_strength="supporting",
        computability="catalog",
        rationale="Missense in a gene where primarily truncating variants cause disease.",
    ),
    CodeSpec(
        code="BP2",
        direction="benign",
        default_strength="supporting",
        computability="literature_llm",
        rationale="Observed in trans with a pathogenic variant for a dominant disorder, or in cis.",
    ),
    CodeSpec(
        code="BP3",
        direction="benign",
        default_strength="supporting",
        computability="catalog",
        rationale="In-frame deletion/insertion in a repetitive region without known function.",
    ),
    CodeSpec(
        code="BP4",
        direction="benign",
        default_strength="supporting",
        computability="rules",
        rationale="Multiple lines of computational evidence suggest no impact; in-silico scores.",
    ),
    CodeSpec(
        code="BP5",
        direction="benign",
        default_strength="supporting",
        computability="literature_llm",
        rationale="Variant found in a case with an alternate molecular basis for disease.",
    ),
    CodeSpec(
        code="BP6",
        direction="benign",
        default_strength="supporting",
        computability="catalog",
        rationale="Reputable source reports benign without evidence; ClinGen deprecated.",
    ),
    CodeSpec(
        code="BP7",
        direction="benign",
        default_strength="supporting",
        computability="rules",
        rationale="Synonymous variant with no predicted splice impact.",
    ),
)


CODE_INDEX: dict[str, CodeSpec] = {spec.code: spec for spec in ACMG_2015_CODES}

RULES_CODES: tuple[str, ...] = tuple(s.code for s in ACMG_2015_CODES if s.computability == "rules")
CATALOG_CODES: tuple[str, ...] = tuple(
    s.code for s in ACMG_2015_CODES if s.computability == "catalog"
)
LITERATURE_CODES: tuple[str, ...] = tuple(
    s.code for s in ACMG_2015_CODES if s.computability == "literature_llm"
)


class ComputabilitySplit(BaseModel):
    n_total: int = Field(default=28)
    n_rules: int
    n_catalog: int
    n_literature_llm: int
    rules_fraction: float
    zero_llm_fraction: float
    rules_codes: tuple[str, ...]
    catalog_codes: tuple[str, ...]
    literature_codes: tuple[str, ...]


def computability_split() -> ComputabilitySplit:
    """Count how many of the 28 codes can run without an LLM."""

    n_rules = len(RULES_CODES)
    n_catalog = len(CATALOG_CODES)
    n_lit = len(LITERATURE_CODES)
    return ComputabilitySplit(
        n_rules=n_rules,
        n_catalog=n_catalog,
        n_literature_llm=n_lit,
        rules_fraction=n_rules / 28,
        zero_llm_fraction=(n_rules + n_catalog) / 28,
        rules_codes=RULES_CODES,
        catalog_codes=CATALOG_CODES,
        literature_codes=LITERATURE_CODES,
    )
