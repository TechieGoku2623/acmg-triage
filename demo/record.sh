#!/usr/bin/env bash
# Write asciinema v2 JSONL casts from real command output. No credentials.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p demo

python3 - <<'PY'
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(".").resolve()
CASTS = {
    "demo/01-classify-pathogenic.cast": [
        ["uv", "run", "acmg", "classify", "--hgvs", "NM_000059.4:c.5946del", "--explain"],
    ],
    "demo/02-conflict-and-refusal.cast": [
        ["uv", "run", "acmg", "classify", "--hgvs", "NM_000059.4:c.2311G>A", "--explain"],
        ["uv", "run", "acmg", "classify", "--hgvs", "NM_001005237.2:c.200A>G"],
    ],
    "demo/03-evaluation.cast": [
        ["make", "eval"],
    ],
}


def run(cmd: list[str]) -> str:
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["PATH"] = str(Path.home() / ".local" / "bin") + ":" + env.get("PATH", "")
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    body = proc.stdout + (proc.stderr if proc.returncode else "")
    if not body.endswith("\n"):
        body += "\n"
    return f"$ {' '.join(cmd)}\n{body}"


def write_cast(path: Path, chunks: list[str]) -> None:
    header = {
        "version": 2,
        "width": 120,
        "height": 40,
        "timestamp": int(time.time()),
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    t = 0.05
    lines = [json.dumps(header, separators=(",", ":"))]
    for chunk in chunks:
        for part in chunk.splitlines(keepends=True):
            lines.append(json.dumps([round(t, 4), "o", part], separators=(",", ":")))
            t += 0.03
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


for dest, commands in CASTS.items():
    write_cast(ROOT / dest, [run(cmd) for cmd in commands])
    print(f"wrote {dest}")
PY
