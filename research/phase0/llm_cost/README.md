# llm_cost

## What is measured

Token counts and dollar cost per variant for the three literature-only nodes (PS3, BS3, PP4), across five published model price tiers. Local prompt-render and tokenize latency. Provider round-trip latency is **unmeasured** (no live API calls).

## Why it decides something

The LLM is restricted to literature evidence. Model family is expensive to reverse once traces and caches exist. This measurement decides the default demo model (cheapest tier whose prompt fits) and whether literature nodes can stay on a small model.

## How to run

```bash
uv run python research/phase0/llm_cost/run.py
```

Seed: 0. Prompts and excerpts are committed under `probe_set/`. Tokenization uses `tiktoken` `cl100k_base` for every model so the comparison isolates price, not tokenizer drift.

## What is unmeasured

- Actual API latency and error rates
- Cache-hit rate on a live literature corpus
- Quality of the extracted `EvidenceResult` (that is a Phase 3 eval, not a cost harness)
