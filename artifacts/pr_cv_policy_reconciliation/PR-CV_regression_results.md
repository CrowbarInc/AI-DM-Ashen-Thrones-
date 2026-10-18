# PR-CV Regression Results

Focused PR-BT before:

- `tests/test_pr_bt_policy_instruction_deduplication.py` + `tests/test_pr_bt_selective_epistemic_guidance.py`: 3 passed / 3 failed.

Focused PR-BT after:

- Command: `.\.venv\Scripts\python.exe -m pytest tests\test_pr_bt_policy_instruction_deduplication.py tests\test_pr_bt_selective_epistemic_guidance.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cv_focused3`
- Result: 8 passed.

Selected deterministic regression command:

- Command included PR-CT, PR-CP, PR-BY retry/narration-only, PR-CC, PR-CE, PR-CK, PR-CN, authored-knowledge, C18/C19/authority, claim-composition, lexical-scope, and social-answer files.
- Result: 274 passed / 3 failed.
- The three failures were in `tests/test_authored_knowledge_realization.py`; rerunning that file alone reproduced the inherited baseline of 14 passed / 2 failed.

Authored-knowledge realization alone:

- Command: `.\.venv\Scripts\python.exe -m pytest tests\test_authored_knowledge_realization.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cv_authored`
- Result: 14 passed / 2 failed.
- Failed:
  - `test_http_notice_question_communicates_patrol_fact`
  - `test_http_read_notice_board_speaks_written_clue`

Shared turn pipeline:

- Command: `.\.venv\Scripts\python.exe -m pytest tests\test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cv_shared`
- Result: 41 passed / 24 failed.
- This matches the inherited PR-CU baseline.

Live provider calls: 0.
