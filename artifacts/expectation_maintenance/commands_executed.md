# Commands Executed

All pytest commands used the bundled Python with `.venv/Lib/site-packages` on `PYTHONPATH`.

```text
python -m pytest -q --tb=short --junitxml=artifacts/expectation_maintenance/pre_maintenance_suite.xml --basetemp=codex_pytest_tmp_expect_pre
python -m pytest tests/test_final_emission_opening_accept_debug.py tests/test_final_emission_opening_fallback.py tests/test_semantic_mutation_attribution_cu4.py tests/test_semantic_mutation_contract_adoption.py -q --tb=short --junitxml=artifacts/expectation_maintenance/focused_rc11.xml --basetemp=codex_pytest_tmp_expect_rc11
python -m pytest tests/test_golden_replay_long_session.py tests/test_golden_replay_projection_engine.py tests/test_golden_replay_projection_fallback_integration.py -q --tb=short --junitxml=artifacts/expectation_maintenance/focused_rc13.xml --basetemp=codex_pytest_tmp_expect_rc13b
python -m pytest tests/test_failure_classification_contract.py::test_co99_failure_classification_registry_documents_governing_authority -q --tb=short --junitxml=artifacts/expectation_maintenance/focused_gd01.xml --basetemp=codex_pytest_tmp_expect_gd01
python -m py_compile tests/test_golden_replay_long_session.py tests/helpers/golden_replay.py tests/helpers/golden_replay_profiles.py tests/test_final_emission_opening_accept_debug.py tests/test_failure_classification_contract.py
python -m pytest -q --tb=short --junitxml=artifacts/expectation_maintenance/post_maintenance_suite.xml --basetemp=codex_pytest_tmp_expect_post
python tools/build_review_handoff.py --config data/validation/review_handoffs/rc11_rc13_expectation_maintenance.json --generated-at 2026-09-19T19:00:00Z
```
