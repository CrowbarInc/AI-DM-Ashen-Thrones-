PR-DU Regression Results

Focused PR-DU:
.\.venv\Scripts\python.exe -m pytest tests\test_pr_du_player_pipeline.py -q --tb=short --basetemp=codex_pytest_tmp_prdu10
Result: 3 passed.

PR-DU + inherited PR-DQ/DR/DS:
.\.venv\Scripts\python.exe -m pytest tests\test_pr_du_player_pipeline.py tests\test_pr_dq_vertical_slice.py tests\test_pr_dq_ic_ooc_messages.py tests\test_pr_dr_live_vertical_slice.py tests\test_pr_ds_operation_compatibility.py -q --tb=short --basetemp=codex_pytest_tmp_prdu_final
Result: 45 passed.

Attempted broader authority/conversation batch:
tests/test_exploration_resolution.py tests/test_scene_transition_authority.py tests/test_state_authority.py tests/test_conversational_memory_window.py
Result: inconclusive; run was interrupted after no output. No failure details were emitted.

Attempted FastAPI TestClient transport:
Result: TestClient hung before route execution in Windows socketpair/anyio portal startup. Focused tests call game.api.chat directly.
