"""Process configuration. No secrets are required for Phase 0."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    env: str = Field(default="dev")
    repo_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    pretty_logs: bool = True

    @property
    def sample_dir(self) -> Path:
        return self.repo_root / "data" / "sample"

    @property
    def research_dir(self) -> Path:
        return self.repo_root / "research" / "phase0"

    @property
    def catalog_path(self) -> Path:
        return self.sample_dir / "catalog.json"

    @property
    def literature_cache_path(self) -> Path:
        return self.sample_dir / "literature_cache.json"

    @property
    def traces_dir(self) -> Path:
        return self.repo_root / "var" / "traces"

    @property
    def probe_set_path(self) -> Path:
        return self.research_dir / "criterion_agreement" / "probe_set" / "variants.json"


def get_settings() -> Settings:
    return Settings()
