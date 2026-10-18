# PR-EC preimplementation baseline

Captured before any PR-EC production edits. The working tree was already dirty from earlier product-realization work. This baseline is the behavior of that tree, not a clean `HEAD` checkout.

## Repository revision

- Branch: `feature/product-realization`
- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- HEAD subject: PR-BN bounded DM improvisational authority
- Tracking: `origin/feature/product-realization` (ahead 1)
- Working tree: dirty. `git status --short` reported 427 lines. `git diff --stat HEAD` reported 68 tracked files changed (14468 insertions, 3871 deletions) plus a large set of untracked PR artifacts. Those files were not cleaned.

## Environment

- OS: Windows 10.0.26200
- Python: 3.12.0 (`.\.venv\Scripts\python.exe`)
- pytest: 9.1.1
- Provider: disabled. No live model calls.
- Reproducible enough to compare later failures test-by-test: yes. The command completed and wrote JUnit XML.
- Known nondeterminism: Windows `PermissionError: [WinError 5]` during atomic `session.json` replace. One baseline failure had this signature and later reproduced on a different test, then passed in isolation.

## Command

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_ea_conversational_orchestration.py tests\test_pr_eb_conversational_continuity.py tests\test_turn_pipeline_shared.py tests\test_pr_du_player_pipeline.py tests\test_pr_dq_ic_ooc_messages.py tests\test_social.py tests\test_pr_br_qualifier_movement_mixed_intent.py tests\test_exploration_resolution.py tests\test_exploration_skill_checks.py tests\test_unparsed_movement_state_narration_integrity.py tests\test_save_load.py tests\test_runtime_persistence_regression_suite_obj14.py tests\test_final_emission_gate.py tests\test_final_emission_response_type.py --tb=line -q --basetemp=codex_pytest_tmp_pr_ec_baseline --junitxml=artifacts/pr_ec_movement_partial_intent/baseline_junit.xml --override-ini="addopts="
```

## Counts and timing

- Collected: 244
- Passed: 214
- Failed: 30
- Warnings: 1 (Starlette/httpx deprecation)
- pytest time: 18.51s
- Wall clock: 19270 ms
- Exit code: 1

Coverage of the required families: PR-EA orchestration, PR-EB continuity, movement/exploration, social dialogue, final emission (`test_final_emission_gate.py`, `test_final_emission_response_type.py`, plus final-emission assertions inside the turn pipeline), persistence/save-load, and `/api/chat` integration. The full historical final-emission corpus was not run; the gate and response-type files plus the shared pipeline are the comparison set.

## Failed tests

1. `tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape` — resolution for `hello there` was not `None`.
2. `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]` — unexpected phrase `for a breath, the scene holds`.
3. `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]` — `PermissionError: [WinError 5]` renaming `session.json`.
4. `tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback` — `reply_kind` `unknown` not in `{answer, explanation, refusal}`.
5. `tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback` — missing `retry_strategy:selected=unresolved_question`.
6. `tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only` — `len([]) == 2`.
7. `tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first` — `len([]) == 2`.
8. `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback` — `len([]) == 2`.
9. `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback` — captured prompt count `1 == 2`.
10. `tests.test_turn_pipeline_shared::test_chat_repeated_social_questions_keep_npc_uncertainty_voice` — `tavern runner` absent from narration.
11. `tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication` — resolution for an audience request was not `None`.
12. `tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange` — kind `question`, expected `social_probe`.
13. `tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata` — missing category `roll_requirement_query`.
14. `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[...]` — four parametrized cases, `AssertionError`.
15. `tests.test_turn_pipeline_shared::test_chat_action_outcome_contract_survives_inside_active_social_scene` — `desk` absent; scene-hold filler present.
16. `tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane` — missing category `roll_requirement_query`.
17. `tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels` — unexpected phrase `planner:`.
18. `tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit` — unexpected phrase `from here, no certain answer presents itself`.
19. `tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit` — `AssertionError`.
20. `tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract` — identical interruption line compared unequal.
21. `tests.test_turn_pipeline_shared::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair` — `any(...)` is false.
22. `tests.test_turn_pipeline_shared::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical` — `tavern runner` absent.
23. `tests.test_turn_pipeline_shared::test_pipeline_strict_social_ragged_stranger_fallback_repaired` — `speaker_contract_enforcement_reason` is `None`.
24. `tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent` — `any([False])`.
25. `tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages` — resolution kind `None`, expected `observe`.
26. `tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution` — resolution kind `None`, expected `observe`.
27. `tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration` — `resolved_exploration_action` absent from the prompt trace.

Items 14's four parameter cases are four of the 30 failures. Exact parameter ids are in `artifacts/pr_ec_movement_partial_intent/baseline_junit.xml`.

## Suites that passed inside this run

PR-EA orchestration, PR-EB continuity, social unit tests in `tests/test_social.py`, movement qualifier tests, unparsed-movement narration tests, exploration skill checks, save/load, runtime persistence, final-emission gate, and final-emission response type all passed. The 30 failures are concentrated in shared chat social/final-emission/retry behavior and four exploration chat routing tests.

## Baseline decision

The baseline is sufficient. Failures are identified, signatures are stored, and the same command can be rerun. Implementation was allowed to proceed. Unrelated failures were not repaired to manufacture a clean baseline.
