from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo.lib.shots import all_commands, gif_beat_id, load_shots, wrap_caption  # noqa: E402


def test_shots_yaml_is_the_video_source() -> None:
    data = load_shots(ROOT / "demo" / "script" / "shots.yaml")
    assert data["title"] == "acmg-triage"
    commands = all_commands(data)
    ids = [shot["id"] for shot in commands]
    assert ids == [
        "01-pathogenic",
        "02-ba1",
        "03-conflict",
        "04-insufficient",
        "05-results",
    ]
    assert gif_beat_id(data) == "03-conflict"
    assert any(shot.get("failure_beat") for shot in commands)
    for shot in commands:
        wrap_caption(str(shot["caption"]))
        assert shot["command"]
        assert float(shot.get("hold", 0)) >= 2.5
