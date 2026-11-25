# Regression

Selections match `artifacts/pr_play_ai_dm_reliability_rebaseline`. Providers were not called. External network attempts: 0. Provider records: 0.

Final commands:

- `python artifacts/pr_play_unmatched_person_reference/run_regression.py combined_final`
- `python artifacts/pr_play_unmatched_person_reference/run_regression.py focused_final`

| Selection | Result | Previous recorded result | New identities | Missing identities |
| --- | --- | --- | --- | --- |
| Combined | 455 passed / 17 failed (472 tests, 773.9 s) | 455 passed / 17 failed | none | none |
| Focused | 470 passed / 1 failed (471 tests, 1156.3 s) | 470 passed / 1 failed | none | none |

The focused failure is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. The assertion text was an empty resolution missing `discovered_clues`. An earlier run of the same test, before the repeat-deferral, failed on missing `resolved_transition`. Same test, same empty resolution, same identity as the inherited failure.

An intermediate combined run, before repeats of a present NPC were left on the delivered exchange, failed one extra test: `tests.test_pr_play_post_npc_handoff::test_explicit_repetition_stays_with_the_captain`. That row is not in the final failure list. The final combined identities match the previous selection.

Focused new-file coverage is outside those selections. `tests/test_unmatched_person_reference.py` passed on its own, including the velvet-inquisitor description, after the final production edit. `tests/test_pr_play_42_evidence_boundaries.py` and `tests/test_uncommitted_action_admission.py` passed with it.

`tests/test_atgb_r2_02_speech_participant_grounding.py` has three failures against `data/world.json`, which contains loft_clerk and not the frontier roster. They fail the same way when the new DM disposition is forced to return nothing. They are not in the combined or focused selection and are not counted as new selection failures.

No full-suite claim.
