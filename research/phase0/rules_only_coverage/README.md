# rules_only_coverage

## What is measured

1. What fraction of the 28 Richards 2015 codes are computable with zero LLM involvement (rules + catalog vs literature).
2. Concordance of a rules-only classifier (default 2015 computational codes + the declarative combining table) against VCEP-style gold classifications on the same 100-variant probe set used by `criterion_agreement`.

## Why it decides something

This is the baseline the full system must beat. If rules-only concordance is already high, literature nodes are optional. If it is low, the LLM path has a job — but only on the codes tagged `literature_llm`.

## How to run

```bash
uv run python research/phase0/rules_only_coverage/run.py
```

The combining table is `src/acmg_triage/combining.py`. Tests diff that structure against the published rows.
