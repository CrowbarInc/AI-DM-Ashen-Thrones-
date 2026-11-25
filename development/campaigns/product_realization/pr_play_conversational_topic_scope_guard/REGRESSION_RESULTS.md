# Regression results

Combined selection from the coverage-contract command, plus `tests/test_compound_action_admission.py`. JUnit: `artifacts/pr_play_conversational_topic_scope_guard/combined_after.xml`.

| Run | Tests | Passed | Failed |
|---|---:|---:|---:|
| Predecessor, without the compound module | 425 | 408 | 17 |
| This milestone | 472 | 455 | 17 |

The 17 failure identities are the same list as `artifacts/pr_play_actionable_request_coverage_contract/combined_after_local_result.json`. The extra 47 tests are the compound-admission module. They passed. No assertion was deleted or weakened. Frozen fixtures were not edited.

`ASHEN_DISABLE_PROVIDER_CALLS` was unset, matching the predecessor. Live interpretation, expression generation, and provider retries were disabled. Experimental physical adjudication was unset. No retry tier was added.

Focused areas covered by that selection: continuity, actionable admission, travel and retreat, destination and transition publication, NPC handoff, perception non-invention, inventory reference wording, marking publication, and the compound-admission tests. The inherited failures stay in reference-surface grounding, one patrol-travel admission sequence, the raw chat stub, perception listen/speech, the operational-refusal classifier, context-projection keys, and the manual-play latency key. Those identities were already failing before this change.
