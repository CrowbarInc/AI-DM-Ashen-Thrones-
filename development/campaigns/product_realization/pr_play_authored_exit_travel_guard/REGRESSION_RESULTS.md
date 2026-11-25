# Regression results

Provider calls stayed disabled in these runs. Experimental physical adjudication stayed unset. No test was skipped, deleted, or weakened.

## Combined selection

The command is the established selection in `artifacts/pr_play_ordinary_semantic_admission/combined_verified_command.txt`, with output redirected to this milestone.

| | Before (predecessor junit) | After |
|---|---:|---:|
| Passed | 405 | 408 |
| Failed | 20 | 17 |
| Errors | 0 | 0 |
| Skipped | 0 | 0 |
| Total | 425 | 425 |
| Duration | 488.644 s | 798.880 s |

JUnit: `artifacts/pr_play_post_repair_bottleneck_assessment/combined.xml` and `artifacts/pr_play_authored_exit_travel_guard/combined_after.xml`.

Resolved identities:

- `tests.test_pr_play_79df3_classification::test_duplicate_refusal_does_not_publish`
- `tests.test_pr_play_79df3_classification::test_two_refusals_then_gameplay_advances`
- `tests.test_pr_play_79df3_classification::test_save_reload_keeps_the_preceding_publication`

These three send "Good day, Gate Guard." under a zero provider limit and require the prior publication and turn counter to stay put. They pass on this run. New failure identities: none.

The other 17 failures are the same names as the predecessor's remaining list, including the two `test_pr_play_39_action_admission` sequence tests. Those two still fail with `KeyError: 'resolved_transition'`, which is the predecessor's failure message. The patrol travel in that test still logs a transition to `old_milestone` before the response-shape assertion.

A separate attempt to rerun the combined selection against git HEAD was invalid. HEAD of `deterministic_conversational_decision` does not accept the `character` argument the current `game/api.py` passes. The predecessor junit is the before measurement. `combined_before_basetemp_invalid.xml` is an earlier setup error from a missing basetemp directory and is not a result.

## Focused preservation

The established focused command from the predecessor, with a new junit path. 611 passed, 0 failed, 0 errors, 0 skipped. Duration 2093.046 s. Predecessor focused result: 611 passed. JUnit: `artifacts/pr_play_authored_exit_travel_guard/focused_after.xml`.

## Travel modules

`tests/test_pr_play_39_action_admission.py`, `tests/test_pr_play_40_scenario_generalization.py`, `tests/test_pr_play_42_evidence_boundaries.py`, and `tests/test_pr_br_continuation26_semantic_closure.py`.

44 tests, 40 passed, 4 failed, 0 errors. JUnit: `artifacts/pr_play_authored_exit_travel_guard/travel_modules.xml`.

The two action-admission failures are the inherited combined identities above. Scenario generalization and evidence-boundary tests passed, including authored exits, unknown destinations, and the merchant-follow case that must not select the north lane.

`test_j1_through_j6_controls` and `test_r1_through_r20_matrix` fail because "I approach the traveler." is contract operation `unresolved` and "If the guard refuses, I'll look for shelter nearby." selects resolver `generation`. Those outcomes come from the existing operation fallthrough and the existing conditional-sentence commitment. This milestone's diff does not edit that fallthrough. The tests are outside the combined selection. They are recorded here and were not reclassified as passes.
