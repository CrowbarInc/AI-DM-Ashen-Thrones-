# PR-CK regression results

Live provider calls: 0. No run was timed out or interrupted. Broad repository regression was not run.

## 1. Focused resolver selection

`tests/test_pr_ck_ordinary_resolver_selection.py`

30 passed, 0 failed, 0 skipped, 0 errors.

## 2. Cluster A tests in the shared pipeline

Passed:

- `test_action_and_chat_investigate_both_mark_runtime_discovery_memory`
- `test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `test_chat_targeted_retry_scene_stall_only`
- `test_chat_passive_scene_prefers_already_introduced_suspicious_figure`
- `test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere`
- `test_action_and_chat_mutate_runtime_before_request_build` (chat and action)

Still failing, and not claimed as the same selection defect:

- `test_chat_single_wait_in_tense_scene_forces_interaction_pressure` — pressure beat lacks the required concrete phrase
- `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere` — same pressure-phrase assertion
- `test_chat_mixed_turn_preserves_embedded_adjudication_metadata` — clue is discovered; embedded category is still absent (PR-CJ cluster H)
- `test_chat_mixed_scene_object_investigation_question_recovers_action_outcome` studies param — clue is discovered; response-type metadata still fails (PR-CJ cluster G)
- `test_chat_action_outcome_contract_survives_inside_active_social_scene` — clue is discovered; player text is still the provider stub

## 3. Entire shared turn pipeline

`tests/test_turn_pipeline_shared.py`

38 passed, 27 failed, 0 skipped, 0 errors. About 10.8 seconds.

PR-CJ baseline: 32 passed, 33 failed.

The six tests that left the failure list are the cluster A selection repairs above. No shared-pipeline test that passed under PR-CJ fails now. The other 27 failures are the remaining PR-CJ clusters. They are not all cluster A. Names are in `shared_failures.txt`.

## 4–12. Adjacent suites

| Suite | Result |
| --- | --- |
| Social relevance `test_social_question_relevance_answer_selection.py` | 25 passed, 0 failed |
| Social routing `test_directed_social_routing.py` | 34 passed, 0 failed |
| Listen question not social `test_listen_question_not_social_capture.py` | 8 passed, 0 failed |
| PR-CC `test_pr_cc_social_reply_reconciliation.py` | 11 passed, 0 failed |
| PR-CE `test_pr_ce_subjective_preference_classification.py` | 13 passed, 0 failed |
| PR-BY `test_pr_by_narration_only_retry_contract.py` | 22 passed, 0 failed |
| PR-BW `test_pr_bw_narration_only_envelope.py` | 5 passed, 0 failed |
| Immutable C18 `test_pr_br_continuation18_immutable_boundary.py` | 21 passed, 0 failed |
| Semantic ownership and structural subject | 9 passed and 13 passed, 0 failed |
| Decision `test_pr_br_gm_resolution_decision.py` | 9 passed, 0 failed |
| Decision claims, fidelity, envelope, resolution contract, stage diff, final emission gate | 104 passed, 0 failed |

Combined junit for the first block of these suites: `pytest_focused_regression.xml`, 200 passed, 0 failed.
