# 27 — Regression Review

The 14 R6-R2-R2 failures were re-read, not rewritten, and not re-executed in this cycle. Production modules were not edited here, so the prior execution remains the latest run.

Contract-expectation changes, safe unknown instead of player clarification, authorization still rejected: the three `test_forged_authority_or_entity_rejected` cases, both `test_bad_prior_target_cannot_launder_history` cases, and seven `test_untrusted_operations_fail_closed_without_losing_focus` cases (`forged`, `cross_conversation`, `stale`, `speaker`, `field`, `operation`, `unwitnessed`, `substitution` — eight parametrized ids, all in that family). These are legitimate disposition changes if the product wants fail-closed unknown rather than a clarification prompt. They are still red tests.

`test_unqualified_historical_id_cannot_override_focus` is a stricter design choice than the no-silent-topic-override invariant. It needs an explicit product decision before anyone relaxes or keeps it.

Five inherited failures remain outside this cycle: three reference-eligibility holdouts, expression sufficiency, and the immutable preseal ignorance case. They were not corrected.
