# 16 — Regression results

Provider calls were disabled for every regression process.

| Lane | Collected | Passed | Failed | Notes |
| --- | --- | --- | --- | --- |
| Focused, combined process | 1085 | 1065 | 20 | Exit 1 |
| Boundary | 107 | 101 | 6 | Same six historical start/opening nodes |
| Broader | 9 | 0 | 9 | Same nine historical authority nodes |
| Isolated lifecycle and persistence | 39 | 39 | 0 | Clean process |

## Focused classification

Historical failures still present:

- `test_readiness_acceptance_is_not_live_execution`
- `test_refusal_text_with_location_repair_updates_state_and_clues`
- `test_usable_location_in_text_updates_structured_topic_and_clues`

`test_no_gameplay_wiring_or_effects` was in the old historical set and did not fail this run.

Seventeen additional focused failures were `test_pr_play_71_lifecycle`, `test_new_campaign_failure_restores_prior_runtime`, and most of `test_pr_play_71v_verification`. They occurred in the long process after an unhealthy in-process preflight cache. The identical three modules passed 39/39 when run alone with a fresh interpreter and an isolated basetemp. They are not counted as new product regressions. The combined XML is kept.

Boundary failures match the six historical start and opening expectations. Broader failures match the nine historical `hard_validation_attempt_1` KeyErrors. No new boundary or broader nodes failed.

New product regression count: 0.

The full suite and official ATGB were not run.
