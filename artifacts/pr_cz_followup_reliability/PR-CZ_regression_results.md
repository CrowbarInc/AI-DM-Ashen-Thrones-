# PR-CZ Regression Results

Commands run:
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cz_followup_reliability.py -q --tb=short`
  - 10 passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py tests\\test_pr_ck_ordinary_resolver_selection.py -q --tb=short`
  - 78 passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ct_safe_prompt_deduplication.py tests\\test_pr_cp_authorized_finalization.py tests\\test_pr_ce_subjective_preference_classification.py tests\\test_pr_cn_contextual_figure_integrity.py tests\\test_pr_by_narration_only_retry_contract.py tests\\test_pr_br_continuation18_immutable_boundary.py tests\\test_pr_br_continuation19_hard_authority.py tests\\test_pr_br_c19_free_text_authority.py -q --tb=short`
  - 97 passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_turn_pipeline_shared.py -q --tb=short`
  - 45 passed / 24 failed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_authored_knowledge_realization.py -q --tb=short`
  - 14 passed / 2 failed.

Inherited baseline:
- Shared pipeline before: 41 passed / 24 failed.
- Shared pipeline after: 45 passed / 24 failed.

Missing named suites:
- No `tests/test_immutable_valid_response.py` path exists; immutable coverage used `tests/test_pr_br_continuation18_immutable_boundary.py`.
- No `tests/test_pr_cr_authored_retry_elimination.py` path exists; retry coverage used `tests/test_pr_by_narration_only_retry_contract.py`.

