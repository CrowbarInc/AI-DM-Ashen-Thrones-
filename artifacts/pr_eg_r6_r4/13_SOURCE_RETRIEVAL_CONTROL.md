# 13 — Source Retrieval Control

Core eligible sets are identical and contain at most two records, so retrieval recall of eligible records into the experiment payload is 100% by construction. This is a control, not evidence of production retrieval quality. Restricted, NPC-unknown, wrong-context and non-world provenance records are omitted before provider calls.

Production focus, 800-character filtering, first-12 selection and four-proposition generation are separate recall bottlenecks. Supplemental scaling probes use 1/4/12/32 eligible records with the answering source last. Read per-case source selections and token costs; these are isolated stress probes, not a corpus-level retrieval estimate. No full source index has been built or migrated.
