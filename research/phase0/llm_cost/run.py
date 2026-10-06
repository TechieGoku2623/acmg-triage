"""Token cost and local latency for literature nodes. No live API calls."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_set"
RESULTS = HERE / "results"
ENC = tiktoken.get_encoding("cl100k_base")


def _render(template: str, excerpt: dict[str, str]) -> str:
    return (
        template.replace("{{CODE}}", excerpt["node"])
        .replace("{{VARIANT}}", excerpt["variant"])
        .replace("{{EXCERPT}}", excerpt["text"])
    )


def main() -> None:
    template = (PROBE / "prompt_template.txt").read_text(encoding="utf-8")
    excerpts = json.loads((PROBE / "excerpts.json").read_text(encoding="utf-8"))["excerpts"]
    pricing = json.loads((PROBE / "pricing.json").read_text(encoding="utf-8"))
    output_tokens = int(pricing["assumed_output_tokens"])

    t0 = time.perf_counter()
    prompts = [_render(template, item) for item in excerpts]
    token_counts = [len(ENC.encode(prompt)) for prompt in prompts]
    local_s = time.perf_counter() - t0

    n = len(prompts)
    mean_in = sum(token_counts) / n
    # Three literature nodes per variant in the production graph.
    input_tokens_per_variant = mean_in * 3
    variants_per_year = 10_000

    models_out: list[dict[str, Any]] = []
    rows: list[list[str]] = []
    for model in pricing["models"]:
        in_price = float(model["input_usd_per_mtok"])
        out_price = float(model["output_usd_per_mtok"])
        usd_per_variant = (
            input_tokens_per_variant / 1_000_000 * in_price
            + (output_tokens * 3) / 1_000_000 * out_price
        )
        usd_per_10k = usd_per_variant * variants_per_year
        models_out.append(
            {
                "id": model["id"],
                "input_usd_per_mtok": in_price,
                "output_usd_per_mtok": out_price,
                "mean_input_tokens_per_prompt": mean_in,
                "input_tokens_per_variant_3_nodes": input_tokens_per_variant,
                "usd_per_variant": usd_per_variant,
                "usd_per_10k_variants": usd_per_10k,
            }
        )
        rows.append(
            [
                str(model["id"]),
                f"{mean_in:.1f}",
                f"{input_tokens_per_variant:.1f}",
                f"{usd_per_variant:.6f}",
                f"{usd_per_10k:.2f}",
            ]
        )

    cheapest = min(models_out, key=lambda row: float(row["usd_per_variant"]))
    payload = {
        "n_excerpts": n,
        "tokenizer": "tiktoken cl100k_base",
        "assumed_output_tokens_per_node": output_tokens,
        "nodes_per_variant": 3,
        "local_render_and_tokenize_seconds": local_s,
        "local_ms_per_excerpt": (local_s / n) * 1000,
        "api_round_trip_latency": "unmeasured",
        "api_round_trip_latency_measurement": (
            "A live call of the same 12 prompts to each provider, recording "
            "p50/p95 RTT. Not run because this harness must work without keys."
        ),
        "decision": (
            f"Default literature model: {cheapest['id']} "
            f"(${cheapest['usd_per_variant']:.6f}/variant). "
            "Escalate to a larger tier only when the small-model cache miss "
            "fails structured-output validation."
        ),
        "models": models_out,
        "per_excerpt_input_tokens": token_counts,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        [
            "model",
            "mean input tok/prompt",
            "input tok/variant (3 nodes)",
            "USD/variant",
            "USD/10k variants",
        ],
        rows,
    )
    md = (
        "# llm_cost results\n\n"
        f"n excerpts = {n}. Local render+tokenize = {local_s * 1000:.2f} ms total. "
        "API RTT = unmeasured.\n\n"
        f"{payload['decision']}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
