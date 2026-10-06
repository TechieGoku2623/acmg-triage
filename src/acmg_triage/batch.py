"""Small batch VCF reader. Five designed rows; no live annotation."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from acmg_triage.classify import classify_hgvs
from acmg_triage.schemas import ClassificationResult


class VcfRow(BaseModel):
    chrom: str
    pos: int
    row_id: str
    ref: str
    alt: str
    hgvs: str
    gene: str
    sample: str


def parse_vcf(path: Path) -> list[VcfRow]:
    rows: list[VcfRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 8:
            raise ValueError(f"malformed VCF line: {line}")
        info = dict(item.split("=", 1) for item in parts[7].split(";") if "=" in item)
        hgvs = info.get("HGVS")
        if not hgvs:
            raise ValueError(f"VCF row {parts[2]} missing INFO/HGVS")
        rows.append(
            VcfRow(
                chrom=parts[0],
                pos=int(parts[1]),
                row_id=parts[2],
                ref=parts[3],
                alt=parts[4],
                hgvs=hgvs,
                gene=info.get("GENE", ""),
                sample=info.get("SAMPLE", ""),
            )
        )
    return rows


def classify_vcf(path: Path) -> list[tuple[VcfRow, ClassificationResult]]:
    return [(row, classify_hgvs(row.hgvs)) for row in parse_vcf(path)]
