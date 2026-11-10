# EXECUTIVE SUMMARY

**B — PARTIAL / FURTHER INVESTIGATION REQUIRED.** H41 changes PASS → FAIL. Its stative/permanence assertion was not extracted by the old access/environment frames; combined precedence was correct. The repair adds entity/property/result/duration comparisons before existing heuristic early exits.

Consequence validator: development 46/46 expected decisions (20/20 unauthorized blocked, 6/6 authorized accepted, 10/10 harmless accepted, 6/6 negated/hypothetical/attempted accepted, 1/1 supported existing state accepted, 3/3 ambiguous reviewed). Frozen same-session holdout: 50/50 expected decisions (15/15 unauthorized blocked, 10/10 authorized accepted, 10/10 harmless accepted, 10/10 nonactual changes accepted, 5/5 ambiguous reviewed). Zero critical false acceptances, zero false rejections and zero validation errors in these two consequence corpora.

Combined development: 45/46 expected; authorized acceptance 5/6, harmless 10/10, unauthorized blocking 20/20. D25 authorized key acquisition still fails legacy items_added validation: anchored._resolution drops effect deltas. The entry implementation reproduces the same rejection. The new frozen holdout tested the consequence validator, not the full integrated pipeline. Those boundaries prevent an A verdict. No implementation changes or holdout reruns followed the freeze.

PR58 regression: original eight retain 8/8 coverage and 7/8 combined PASS; all 43 development decisions unchanged; previous 50-case holdout changes only H41, bringing unauthorized expansions to 10/10 blocked. Its legitimate acceptance remains 14/15. Focused tests 686/689 pass; 3 known failures. PR55 wrapper 1/1 pass. Broader 0/9 pass, all known hard_validation_attempt_1 failures. Zero new test regressions.

Persistent validation 0.064 ms average / 1.254 ms max; combined 2.316 / 85.567 ms. Zero provider requests/tokens. Campaign data, quarantine and fallback source hashes unchanged. No commits or pushes.

Primary next step: PR-PLAY-60: bounded repair of resolved inventory-consequence projection into the existing combined narration validator, with a fresh frozen end-to-end corpus. Preserve quarantine and deterministic fallback; do not enable player-facing narration.
