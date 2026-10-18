# 22 — Legacy Regression Disposition

The 14 R6-R2-R2 identities were re-run. They still fail because the tests expect a player clarification and the host returns a safe unknown. That is the same intended fail-closed disposition recorded in `artifacts/pr_eg_r6_r2_r2/regression_comparison.json`. Assertions were not rewritten.

- Three `test_forged_authority_or_entity_rejected` cases: safety-preserving rejection.
- Two `test_bad_prior_target_cannot_launder_history` cases: safety-preserving rejection.
- Eight `test_untrusted_operations_fail_closed_without_losing_focus` cases: safety-preserving rejection. Focus is kept.
- `test_unqualified_historical_id_cannot_override_focus`: stricter than the no-silent-override rule. An unqualified historical id does not steal focus. Left for external review; not relaxed in this cycle.

Disclosure, provenance, semantic-planner, and operation suites passed apart from those 14.
