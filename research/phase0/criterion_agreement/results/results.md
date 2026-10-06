# criterion_agreement results

n = 100 committed probe variants.

Ship default-only: BP4

Needs VCEP overlay: PVS1, PM2, PP3, BA1, BS1

| code | gold+ | TP | FP | FN | precision | recall | F1 | strength mismatches | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PVS1 | 18 | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 | 8 | needs VCEP overlay |
| PM2 | 60 | 60 | 10 | 0 | 0.857 | 1.000 | 0.923 | 60 | needs VCEP overlay |
| PM4 | 0 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0 | unmeasured (no gold positives) |
| PP3 | 14 | 8 | 0 | 6 | 1.000 | 0.571 | 0.727 | 0 | needs VCEP overlay |
| BA1 | 20 | 8 | 0 | 12 | 1.000 | 0.400 | 0.571 | 0 | needs VCEP overlay |
| BS1 | 10 | 0 | 7 | 10 | 0.000 | 0.000 | 0.000 | 0 | needs VCEP overlay |
| BP4 | 28 | 28 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0 | default-only |
| BP7 | 0 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0 | unmeasured (no gold positives) |
