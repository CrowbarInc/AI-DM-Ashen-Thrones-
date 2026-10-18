# PR-CX Regression Results

No live provider calls.

Focused PR-CX/PR-CW:

- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_focus`
- Result: 48 passed.

Named deterministic authority suites:

- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py tests\\test_pr_cp_authorized_finalization.py tests\\test_pr_ce_subjective_preference_classification.py tests\\test_pr_ck_ordinary_resolver_selection.py tests\\test_pr_br_continuation18_immutable_boundary.py tests\\test_pr_br_continuation19_hard_authority.py tests\\test_bounded_improvisation_authority.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_named`
- Result: 137 passed.

Shared turn-pipeline suite:

- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_shared`
- Result: 41 passed / 24 failed.
- This matches the inherited PR-CW shared-pipeline baseline: 41 passed / 24 failed.

Selected combined run:

- Command: `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py tests\\test_pr_cp_authorized_finalization.py tests\\test_pr_ce_subjective_preference_classification.py tests\\test_pr_ck_ordinary_resolver_selection.py tests\\test_pr_br_continuation18_immutable_boundary.py tests\\test_pr_br_continuation19_hard_authority.py tests\\test_bounded_improvisation_authority.py tests\\test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_regression2`
- Result: named suites pass; shared suite retains 24 failures.

Dedicated PR-CV and PR-CR filenames were not present in this checkout under `tests/`.

