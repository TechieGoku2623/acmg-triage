# Data

Phase 0 does not download ClinVar, gnomAD, dbNSFP, or VEP caches. The committed
objects are:

- `data/sample/variants.json` — five designed demo variants (see
  `data/sample/README.md`)
- `research/phase0/criterion_agreement/probe_set/variants.json` — 100 probe
  variants whose gold codes follow published ClinGen VCEP rules
- `research/phase0/llm_cost/probe_set/` — synthetic literature excerpts and a
  committed price table

No patient-identifiable data. No restricted-access corpus. License notes for
the production sources (ClinVar, gnomAD v4, dbNSFP, Ensembl VEP, ClinGen) are
in `docs/phase-0/research-memo.md` §3.

Full-database redistribution is out of scope. Ingest in later phases writes a
manifest (source URL, retrieval timestamp, row count, sha256) and keeps raw
files in gitignored bronze storage.
