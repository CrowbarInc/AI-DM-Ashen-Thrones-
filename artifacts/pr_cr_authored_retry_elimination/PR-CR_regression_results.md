# PR-CR Regression Results

No live provider calls were made.

Focused finalization:

- `.\.venv\Scripts\python.exe -m pytest tests\test_pr_cp_authorized_finalization.py -q --tb=short`
- result: 9 passed.

Focused PR-CR/adjacent suites:

- `.\.venv\Scripts\python.exe -m pytest tests\test_pr_cp_authorized_finalization.py tests\test_pr_cc_social_reply_reconciliation.py tests\test_pr_ce_subjective_preference_classification.py tests\test_pr_ck_ordinary_resolver_selection.py tests\test_pr_cn_contextual_figure_integrity.py -q --tb=short --basetemp=codex_pytest_tmp_cr_focus`
- result: 76 passed, 1 warning.

Retry / immutable / C18-C19 authority:

- `.\.venv\Scripts\python.exe -m pytest tests\test_pr_by_narration_only_retry_contract.py tests\test_pr_br_continuation18_immutable_boundary.py tests\test_pr_br_continuation19_hard_authority.py -q --tb=short`
- result: 54 passed, 1 warning.

Authored-knowledge HTTP suite:

- `.\.venv\Scripts\python.exe -m pytest tests\test_authored_knowledge_realization.py -q --tb=short --basetemp=codex_pytest_tmp_cr_authored`
- result: 14 passed, 2 failed.
- failures: `test_http_notice_question_communicates_patrol_fact`, `test_http_read_notice_board_speaks_written_clue`.
- assessment: inherited/adjacent HTTP authored-knowledge failures; not in the immutable finalization boundary changed by PR-CR.

Shared turn pipeline:

- `.\.venv\Scripts\python.exe -m pytest tests\test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_cr_shared`
- result: 41 passed, 24 failed, 1 warning.
- matches the inherited shared-pipeline failure baseline stated in the request.

Combined focused command:

- result included the same shared-pipeline failures plus the two authored-knowledge HTTP failures.

