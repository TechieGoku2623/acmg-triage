# Sample variants

These five records are designed, not sampled. Each one exists to exercise a
path the walkthrough names. Frequencies and scores are committed stand-ins so
`make demo` and `make test` run with no network.

This directory contains no patient-identifiable data. HGVS strings are public
catalog identifiers or designed probes. This is not a ClinVar dump.

| ID | HGVS | Why it is here |
| --- | --- | --- |
| S1 | `NM_000059.4:c.5946del` | Clean pathogenic-leaning BRCA2 frameshift (6174delT). PVS1+PM2. Evidence trail, not just a label. |
| S2 | `NM_000059.4:c.1114A>C` | Common benign polymorphism (p.Asn372His). BA1 fires and the chain terminates. |
| S3 | `NM_000059.4:c.2311G>A` | Designed VUS with PM2 + BP4. Output must show CONFLICTING EVIDENCE. |
| S4 | `NM_000257.4:c.1988G>A` | MYH7 missense at AF 8e-6. Default PM2 fires; VCEP absent-only PM2 does not. |
| S5 | `NM_001005237.2:c.200A>G` | OR8U1, no ClinVar/ClinGen coverage in the sample catalog. Must refuse. |

S1 under ClinGen SVI (PM2 at supporting strength) is Uncertain significance,
not Likely pathogenic. The 2015 table has no row for 1 very strong + 1
supporting. That is an intentional teaching case, not a mislabel.

S3's HGVS is a designed probe for the conflict path. It is not a claim about
that exact ClinVar assertion.

S5 is the failing case the walkthrough is built around. A demo that only
shows S1 teaches nothing about when to trust the tool.

LLM response cache for these five is a Phase 2/3 commit. Phase 0 does not
call a model.
