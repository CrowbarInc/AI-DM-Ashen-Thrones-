# PR-CT Regression Results

Focused PR-CT prompt-contract tests: `3 passed`.

Focused authority/regression sample without authored-knowledge file:
`.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ct_safe_prompt_deduplication.py tests\\test_pr_cp_authorized_finalization.py tests\\test_pr_by_narration_only_retry_contract.py tests\\test_pr_cc_social_reply_reconciliation.py tests\\test_pr_ce_subjective_preference_classification.py tests\\test_pr_ck_ordinary_resolver_selection.py tests\\test_pr_cn_contextual_figure_integrity.py tests\\test_pr_br_continuation18_immutable_boundary.py tests\\test_pr_br_continuation19_hard_authority.py -q --basetemp=codex_pytest_tmp_pr_ct_regression2` => `133 passed`, 1 Starlette/httpx deprecation warning.

Inherited/unrelated failures observed:

- `tests/test_pr_bt_policy_instruction_deduplication.py`: 2 failed, 4 passed in combined run. Failures were P2 narration-only rule-presence expectations and P3 falling below the older 12k char threshold.
- `tests/test_authored_knowledge_realization.py`: 3 failures in a broader sample. The failing assertions expect authored patrol/notice facts in deterministic fallback output and are not caused by removed provider prompt instructions.

Broader requested suites were not fully run in this bounded pass. Existing inherited shared pipeline baseline from PR-CS: `41 passed / 24 failed`. No live provider calls were made.
