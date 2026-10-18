# 05 — Failure Taxonomy

- E01: Question interpretation incorrect.
- E02: Relevant source not retrieved.
- E03: Source proposition malformed or semantically incomplete.
- E04: Question/source role mismatch.
- E05: Relationship mismatch.
- E06: Qualifier mismatch.
- E07: Relevant source insufficient.
- E08: Complete source marked partial.
- E09: Related nonanswer marked direct.
- E10: Unsupported inference.
- E11: Source unavailable to NPC.
- E12: Source restricted.
- E13: Invalid provenance.
- E14: Host false rejection.
- E15: Host false acceptance.
- E16: Final expression mismatch.
- E17: Evaluation error.

Record the earliest demonstrated cause, retaining downstream effects separately. Source-schema failures precede host rejection. A missing requested-role binding in a source interpretation is E03, even if the source sentence is complete. This cycle does not test final expression, so E16 is not inferred from a kernel result. `per_case_results.jsonl` contains audited attribution; original run scores remain in raw files.
