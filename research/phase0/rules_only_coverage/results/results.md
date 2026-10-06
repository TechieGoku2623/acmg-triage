# rules_only_coverage results

Rules-computable: 8/28 = 0.286

Zero-LLM (rules + catalog): 17/28 = 0.607

Literature/LLM: 11/28

Rules-only concordance vs VCEP gold: 67/100 = 0.670

Rules-only is the published baseline. Phase 3 must beat this concordance (0.670) with literature nodes enabled, and must report the disabled-LLM score as this number.

## Code computability

| code | computability | default strength | direction |
| --- | --- | --- | --- |
| PVS1 | rules | very_strong | pathogenic |
| PS1 | catalog | strong | pathogenic |
| PS2 | literature_llm | strong | pathogenic |
| PS3 | literature_llm | strong | pathogenic |
| PS4 | literature_llm | strong | pathogenic |
| PM1 | catalog | moderate | pathogenic |
| PM2 | rules | moderate | pathogenic |
| PM3 | literature_llm | moderate | pathogenic |
| PM4 | rules | moderate | pathogenic |
| PM5 | catalog | moderate | pathogenic |
| PM6 | literature_llm | moderate | pathogenic |
| PP1 | literature_llm | supporting | pathogenic |
| PP2 | catalog | supporting | pathogenic |
| PP3 | rules | supporting | pathogenic |
| PP4 | literature_llm | supporting | pathogenic |
| PP5 | catalog | supporting | pathogenic |
| BA1 | rules | stand_alone | benign |
| BS1 | rules | strong | benign |
| BS2 | catalog | strong | benign |
| BS3 | literature_llm | strong | benign |
| BS4 | literature_llm | strong | benign |
| BP1 | catalog | supporting | benign |
| BP2 | literature_llm | supporting | benign |
| BP3 | catalog | supporting | benign |
| BP4 | rules | supporting | benign |
| BP5 | literature_llm | supporting | benign |
| BP6 | catalog | supporting | benign |
| BP7 | rules | supporting | benign |

## Confusion matrix (rules-only vs gold class)

| gold \ pred | Pathogenic | Likely pathogenic | Uncertain significance | Likely benign | Benign | Conflicting |
| --- | --- | --- | --- | --- | --- | --- |
| Pathogenic | 0 | 0 | 0 | 0 | 0 | 0 |
| Likely pathogenic | 0 | 0 | 0 | 0 | 0 | 0 |
| Uncertain significance | 0 | 18 | 51 | 0 | 0 | 0 |
| Likely benign | 0 | 0 | 0 | 0 | 0 | 0 |
| Benign | 0 | 0 | 5 | 7 | 8 | 0 |
| Conflicting | 0 | 0 | 3 | 0 | 0 | 8 |
