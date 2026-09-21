# Commands Executed

All pytest commands used `.venv\Scripts\python.exe`.

```text
.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only tests/test_social_destination_redirect_leads.py::test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry tests/test_social_destination_redirect_leads.py::test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows tests/test_social_destination_redirect_leads.py::test_destination_lead_distinct_from_existing_milestone_pending -q --tb=short --junitxml=artifacts/policy_resolution/pre_policy_focused.xml --basetemp=codex_pytest_tmp_policy_pre

$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe artifacts/policy_resolution/_rc21_diag.py

.\.venv\Scripts\python.exe -m pytest -q --tb=line --junitxml=artifacts/policy_resolution/pre_policy_baseline.xml --basetemp=codex_pytest_tmp_policy_pre_full

.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only tests/test_social_destination_redirect_leads.py::test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry tests/test_social_destination_redirect_leads.py::test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows tests/test_social_destination_redirect_leads.py::test_destination_lead_distinct_from_existing_milestone_pending -q --tb=line --junitxml=artifacts/policy_resolution/post_policy_focused.xml --basetemp=codex_pytest_tmp_policy_post_focus

.\.venv\Scripts\python.exe -m pytest -q --tb=line --junitxml=artifacts/policy_resolution/post_policy_analysis_baseline.xml --basetemp=codex_pytest_tmp_policy_post_full
```

The temporary RC-21 diagnostic script was deleted after its snapshot was captured in `rc21_runtime_snapshot.json`.
