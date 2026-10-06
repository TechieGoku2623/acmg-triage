from __future__ import annotations

from acmg_triage.config import get_settings
from acmg_triage.logging import configure_logging


def test_settings_point_at_committed_sample_dir() -> None:
    settings = get_settings()
    assert (settings.sample_dir / "variants.json").is_file()
    assert (settings.research_dir / "run_all.py").is_file()


def test_configure_logging_does_not_raise() -> None:
    configure_logging()
