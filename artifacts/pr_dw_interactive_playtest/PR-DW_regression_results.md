PR-DW regression results

Focused command:
`$env:ASHEN_DISABLE_LIVE_INTERPRETATION='1'; $env:ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1'; .\.venv\Scripts\python.exe -m pytest tests\test_pr_dw_disposable_data_dir.py tests\test_pr_du_player_pipeline.py tests\test_pr_dq_vertical_slice.py tests\test_pr_dq_ic_ooc_messages.py tests\test_pr_dr_live_vertical_slice.py tests\test_pr_ds_operation_compatibility.py -q --tb=short --disable-warnings --basetemp=codex_pytest_tmp_prdw_focus`

Result:
- 48 passed.

Unsupported option:
- `--timeout=120` was attempted first but pytest-timeout is not installed, so pytest rejected the option before collection.

Broader command attempted:
`.\.venv\Scripts\python.exe -m pytest tests\test_pr_do_authority_separation.py tests\test_pr_dp_contract_qualification.py tests\test_pr_cx_authority_assurance.py tests\test_social.py tests\test_social_exchange_emission.py tests\test_conversational_memory_window.py tests\test_exploration_resolution.py tests\test_exploration_skill_checks.py tests\test_turn_pipeline_shared.py -q --tb=short --disable-warnings --basetemp=codex_pytest_tmp_prdw_regression`

Broader result:
- Started and emitted progress through at least 48 percent plus additional dots.
- Stalled without additional output and was interrupted.
- No failure details were emitted before interruption.

Unexecuted/not completed:
- Full broad regression suite.
- Provider timeout/malformed response tests.
- Post-commit retry failure test.

