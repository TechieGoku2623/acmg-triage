export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo record demo-shots

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research demo
	$(UV) run ruff format --check src tests research demo
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py
	$(UV) run python research/phase3/run.py
	$(UV) run python research/phase0/render_docs.py

eval:
	$(UV) run python research/phase0/criterion_agreement/run.py
	$(UV) run python research/phase0/llm_cost/run.py
	$(UV) run python research/phase0/rules_only_coverage/run.py
	$(UV) run python research/phase3/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run acmg demo-plan --dry-run
	$(UV) run acmg classify --hgvs "NM_000059.4:c.5946del" --explain
	$(UV) run acmg classify --hgvs "NM_000059.4:c.1114A>C" --explain
	$(UV) run acmg classify --hgvs "NM_000059.4:c.2311G>A" --explain
	$(UV) run acmg classify --hgvs "NM_001005237.2:c.200A>G"
	$(MAKE) eval

demo-shots:
	$(UV) run --with pyyaml python demo/verify_shots.py

record:
	bash demo/record.sh
	bash demo/render.sh
