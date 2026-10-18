# PR-CI Regression Results

Focused target HTTP tests:

`python -m pytest tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b tests/test_social_question_relevance_answer_selection.py::test_general_http_relevant_hook_still_lands tests/test_social_question_relevance_answer_selection.py::test_general_http_unauthorized_no_leak tests/test_social_question_relevance_answer_selection.py::test_general_http_first_ask -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_targets5`

Result: 4 passed.

Lower-level + target tests:

`python -m pytest tests/test_social_question_relevance_answer_selection.py::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance ... -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_lower`

Result: 5 passed.

Entire social relevance file:

`python -m pytest tests/test_social_question_relevance_answer_selection.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_file`

Result: 25 passed.

Social / PR-CC / PR-CE / PR-BY / PR-BW:

`python -m pytest tests/test_social.py tests/test_social_exchange_emission.py tests/test_pr_cc_social_reply_reconciliation.py tests/test_pr_ce_subjective_preference_classification.py tests/test_pr_by_narration_only_retry_contract.py tests/test_pr_bw_narration_only_envelope.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_reg1`

Result: passed.

Immutable / final emission:

`python -m pytest tests/test_pr_br_continuation18_immutable_boundary.py tests/test_turn_packet_stage_diff_integration.py tests/test_final_emission_gate.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_reg3`

Result: 27 passed.

Authority / C18-adjacent:

`python -m pytest tests/test_pr_br_gm_resolution_decision.py tests/test_pr_br_decision_owned_realization_claims.py tests/test_pr_br_decision_semantic_fidelity_slice3.py tests/test_pr_br_structured_realization_envelope.py tests/test_pr_br_resolution_contract.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_reg4`

Result: passed.

Turn-pipeline broad focused file:

`python -m pytest tests/test_final_emission_gate.py tests/test_turn_pipeline_shared.py tests/test_pr_br_continuation18_immutable_boundary.py tests/test_turn_packet_stage_diff_integration.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ci_reg2`

Result: failed due to 33 failures in `tests/test_turn_pipeline_shared.py`. The other three files in that command passed when rerun separately. The failures are broad routing/retry/social-pressure expectations present in the dirty workspace and are not evidence of a PR-CI authority leak.

Broad regression:

Not run.

