# Phase 0 harnesses

`make research` runs these in order:

1. `criterion_agreement/probe_set/build.py` — rebuild the committed 100-variant gold set
2. `criterion_agreement/run.py` — per-code precision/recall
3. `llm_cost/run.py` — literature-node token cost
4. `rules_only_coverage/run.py` — 28-code computability + rules-only concordance
5. `render_docs.py` — write `docs/phase-0/research-memo.md`, `docs/EVALUATION.md`, and the measured tables in `README.md`

No number in the memo is typed by hand. If a quantity cannot be produced here, the memo says **unmeasured** and names the measurement that would settle it.
