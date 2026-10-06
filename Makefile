export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research
	$(UV) run ruff format --check src tests research
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py

eval:
	$(UV) run python research/phase0/criterion_agreement/run.py
	$(UV) run python research/phase0/llm_cost/run.py
	$(UV) run python research/phase0/rules_only_coverage/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run acmg demo-plan --dry-run

record:
	@echo "Asciinema recordings are a Phase 3 deliverable (demo/*.cast)."
	@echo "Phase 0 has no classify CLI to record."
