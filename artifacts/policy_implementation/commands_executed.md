# Commands Executed

All pytest commands used `.venv\Scripts\python.exe`.

```text
.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only tests/test_fallback_incidence_report.py::test_classifies_legacy_compatibility_local_opening_as_read_only tests/test_social_destination_redirect_leads.py -q --tb=short

.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_meta.py tests/test_fallback_incidence_report.py tests/test_final_emission_opening_fallback.py tests/test_opening_fallback_owner_bucket.py tests/test_failure_classifier.py::test_only_legacy_named_helpers_emit_compat_local_opening_authorship tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only tests/test_final_emission_meta.py::test_failure_classification_builders_access_compat_local_only_via_legacy_helpers tests/test_final_emission_meta.py::test_failure_dashboard_fixtures_access_compat_local_only_via_legacy_helpers -q --tb=line --junitxml=artifacts/policy_implementation/focused_rc10_opening.xml --basetemp=codex_pytest_tmp_polimpl_rc10

.\.venv\Scripts\python.exe -m pytest tests/test_social_destination_redirect_leads.py tests/test_social_lead_landing.py tests/test_clue_lead_registry_integration.py tests/test_lead_engine_upsert.py tests/test_lead_npc_target_authority.py tests/test_qualified_pursuit_parser.py tests/test_follow_lead_commitment_wiring.py tests/test_state_authority.py -q --tb=line --junitxml=artifacts/policy_implementation/focused_rc21_leads.xml --basetemp=codex_pytest_tmp_polimpl_rc21

.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_direct_seam.py tests/test_ownership_write_path_governance.py tests/test_scene_canon_hygiene.py tests/test_opening_start_seam_regressions.py -q --tb=line --junitxml=artifacts/policy_implementation/focused_replay_ownership.xml --basetemp=codex_pytest_tmp_polimpl_replay

.\.venv\Scripts\python.exe -m pytest -q --tb=line --junitxml=artifacts/policy_implementation/post_implementation_suite.xml --basetemp=codex_pytest_tmp_polimpl_full

.\.venv\Scripts\python.exe -m pytest tests/test_by2_protected_semantic_mutation_measurement.py::test_by2_probe_does_not_affect_final_output -q --tb=short --basetemp=codex_pytest_tmp_polimpl_by2retry

.\.venv\Scripts\python.exe -m pytest -q --tb=line --junitxml=artifacts/policy_implementation/post_implementation_suite.xml --basetemp=codex_pytest_tmp_polimpl_full2
```

The first full-suite pass collected 6,450 with one Windows `PermissionError` in `test_by2_probe_does_not_affect_final_output`. Isolated re-run passed. The second full suite is the authoritative post-policy baseline: 6,450 collected, 6,351 passed, 0 failed, 99 skipped.

Pre-policy baseline remains `artifacts/policy_resolution/pre_policy_baseline.xml` and `post_policy_analysis_baseline.xml` (6,450 / 6,347 / 4 / 99).
