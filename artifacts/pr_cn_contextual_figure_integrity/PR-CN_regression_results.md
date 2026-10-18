# PR-CN Regression Results

Focused PR-CN and updated PR-CM diagnostic:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cn_contextual_figure_integrity.py tests\\test_pr_cm_passive_pressure_contract.py::test_diagnostic_scene_stall_fallback_stores_guard_lead_subject -q --tb=short`
- Result: 14 passed.

Existing contextual-lead tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_prompt_and_guard.py -q --tb=short`
- Result: 56 passed.

Grounded-observation tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_prompt_and_guard.py::test_remember_recent_contextual_leads_extracts_named_and_positioned_live_leads tests\\test_grounded_observation_non_invention.py -q --tb=short`
- Result: 12 passed / 2 failed.
- Failures:
  - `test_frontier_gate_post_return_observe_does_not_invent_confrontation`
  - `test_milestone_examine_does_not_keep_invented_inscription`

Passive-pressure fallback tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_final_emission_passive_scene_pressure.py tests\\test_final_emission_scene_facts.py -q --tb=short`
- Result: 8 passed.

PR-CM passive-world contract tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cm_passive_pressure_contract.py -q --tb=short`
- Result: 4 passed / 1 failed.
- Failure:
  - `test_repeated_quiet_waits_ground_stall_without_a_new_event`

PR-CK resolver-selection tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ck_ordinary_resolver_selection.py -q --tb=short`
- Result: 30 passed.

Prompt-context tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_prompt_context.py -q --tb=short`
- Result: 115 passed.

Persistence tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_save_load.py tests\\test_activate_scene_validation_and_get_persistence.py -q --tb=short`
- Result: 13 passed.

Immutable-response and GM-resolution-decision tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_br_continuation18_immutable_boundary.py tests\\test_pr_br_gm_resolution_decision.py -q --tb=short`
- Result: 30 passed.

Authority and C19/C18-adjacent tests:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_br_c19_free_text_authority.py tests\\test_pr_br_continuation19_hard_authority.py tests\\test_state_authority.py -q --tb=short`
- Result: 41 passed / 1 failed.
- Failure:
  - `test_raw_chat_stub_authority_and_contracts`

Entire shared turn-pipeline file:
- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_turn_pipeline_shared.py -q --tb=short`
- Result: 41 passed / 24 failed.
- Baseline comparison: unchanged from inherited 41 passed / 24 failed.

Broad regression:
- Not run.
