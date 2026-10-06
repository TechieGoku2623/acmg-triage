"""Optional FastAPI surface. Demo does not start this server."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from acmg_triage import SAFETY_DISCLAIMER
from acmg_triage.classify import classify_hgvs

app = FastAPI(
    title="acmg-triage",
    description=SAFETY_DISCLAIMER,
    version="0.1.0",
)


class ClassifyRequest(BaseModel):
    hgvs: str = Field(min_length=3)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": SAFETY_DISCLAIMER}


@app.post("/classify")
def classify_endpoint(body: ClassifyRequest) -> dict[str, Any]:
    """Return the full evidence trail plus the safety disclaimer."""

    try:
        result = classify_hgvs(body.hgvs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = result.model_dump()
    payload["disclaimer"] = SAFETY_DISCLAIMER
    return payload
