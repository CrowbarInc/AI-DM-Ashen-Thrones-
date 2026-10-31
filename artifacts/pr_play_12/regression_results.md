# Consolidated final results

| Lane | Selected pass | Fail | PR11 pass / fail | Same-case supplement |
| --- | --- | --- | --- | --- |
| harness | 35 | 0 | 35 / 0 | [] |
| gameplay | 33 | 0 | 33 / 0 | [] |
| rules_persistence | 53 | 0 | 53 / 0 | [] |
| conversation | 35 | 0 | 35 / 0 | [] |
| provider | 88 | 1 | 88 / 1 | [] |
| diagnostics | 81 | 0 | 81 / 0 | ['tests.test_pr_play_06_opening_budget::test_opening_fixtures[minimal]', 'tests.test_pr_play_07_semantic_acceptance::test_capture_requires_controlled_scope[diagnostics]'] |
| structured | 60 | 1 | 60 / 1 | [] |
| opening | 23 | 3 | 23 / 3 | [] |
| world | 123 | 0 | 123 / 0 | ['tests.test_atgb_r2_04_question_evidence_contract::test_historical_control_through_current_request_and_host[0]', 'tests.test_atgb_r2_04_question_evidence_contract::test_historical_control_through_current_request_and_host[1]', 'tests.test_atgb_r2_04_question_evidence_contract::test_historical_control_through_current_request_and_host[2]', 'tests.test_atgb_r2_04_question_evidence_contract::test_historical_control_through_current_request_and_host[3]'] |
| export_atgb | 55 | 1 | 55 / 1 | ['tests.test_atgb_infrastructure::test_provider_disabled_host_uses_chat_and_isolates_state'] |
| overlay | 88 | 0 | 88 / 0 | [] |
| hidden_faction | 78 | 0 | 78 / 0 | [] |
| claim_authority | 126 | 8 | 126 / 8 | [] |

These are final selected case outcomes, not a sum of every rerun. Initial and superseded attempts remain in the raw logs. Same-case original-source controls use the same unchanged production source and no live providers. Four world cases, two diagnostic setups and one provider-disabled export case are resolved this way. Fourteen failing IDs match the baseline exactly.

| Failure | Classification |
| --- | --- |
| tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution | preexisting failure |
| tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid | preexisting failure |
| tests.test_start_campaign_api::test_start_campaign_emits_opening_and_sets_started | preexisting failure |
| tests.test_start_campaign_api::test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text | preexisting failure |
| tests.test_start_campaign_api::test_start_campaign_promotes_valid_upstream_prepared_scene_opening | preexisting failure |
| tests.test_atgb_accounting::test_readiness_verifies_repaired_dispatch_coverage | preexisting failure |
| tests.test_pr_br_claim_control_slice2::test_false_positive_controls_remain_speakable | preexisting failure |
| tests.test_realization_provenance::test_call_gpt_provider_failure_metadata_has_provider_family | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_general_written_surface_question_discovers_authored_clue | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_general_visible_evidence_may_be_reported | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_general_valid_target_no_evidence_is_grounded_absence | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_general_requested_identity_absent_does_not_mint_person | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_general_observe_empty_target_does_not_invent | preexisting failure |
| tests.test_investigation_result_provenance_non_invention::test_frontier_gate_t15_look_toward_does_not_mint_personnel_timing | preexisting failure |
