# Regression results

Focused: 746/749 passed, 3 failures, 0 errors; 0 new failures. Additional failed-examination boundary: 1 passed. PR55 holdout wrapper: 1/1 passed. Broader authority assurance: 9/9 failures involving hard_validation_attempt_1. Full suite NOT TESTED.

Historical focused baseline: 741 passed / 3 known failures. PR62 focused selection
adds five tests; one failed-examination boundary runs separately. Coverage spans
PR55–61, authority, geography, mandatory coverage, authorized inventory projection,
persistent effects, isolation, fallback and accounting. H41 and unauthorized
inventory/persistent controls retain rejection. Legitimate paraphrase and
authorized inventory expectations retain their existing assertions.

Initial iteration: 739 passed / 10 failures. Six exposed unintended offline
preview wording changes; fixed by limiting new fallback to experimental
publication. One new test incorrectly required fresh-runtime initialization to
stay identical before/after; corrected to compare full completed authority with
ordinary deterministic control. Existing tests/validators were not weakened.
Three other failures are the recorded baseline. Initial log/XML are preserved.
The earlier target-label allowlist error was fixed before the live run.

Exact commands/failure IDs are in regression_summary_final.json and XML/logs.
The established runner snapshots/restores protected generated historical evidence
that tests touch. Nine broader hard_validation_attempt_1 failures remain unrelated
and unrepaired. No full-suite or independent unseen-generalization claim.
