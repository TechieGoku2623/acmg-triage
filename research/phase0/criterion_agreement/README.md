# criterion_agreement

## What is measured

Per-code precision and recall of the default ACMG/AMP 2015 computational rules against 100 committed probe variants whose gold codes follow published ClinGen VCEP assignments (ENIGMA BRCA1/2 frequency cutoffs, ClinGen SVI PM2-as-supporting, last-exon PVS1 downgrade).

## Why it decides something

A code that the default rules cannot recover against VCEP gold is not reliable enough to ship without the gene-specific specification table. This measurement decides which of the eight rules-computable codes enter Phase 2 as default-only, and which are blocked on a VCEP overlay.

## How to run

```bash
uv run python research/phase0/criterion_agreement/run.py
```

Seed: 0. The probe set is committed under `probe_set/variants.json` and is not regenerated at run time.

## Gold-label source

Gold codes are assigned by the committed probe builder (`probe_set/build.py`) using published VCEP thresholds, not by `acmg_triage.rules`. The two implementations are intentionally different. This is not a live dump of the ClinGen Evidence Repository; replacing the probe set with 100 erepo-exported variants is the measurement that would retire that limitation.
