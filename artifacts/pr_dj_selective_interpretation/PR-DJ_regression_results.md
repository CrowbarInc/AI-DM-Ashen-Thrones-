# PR-DJ Regression Results

Focused PR-DJ: python -m pytest tests/test_pr_dj_selective_interpretation.py -q -> 9 passed, 1 warning.

PR-DG experimental interface: python -m pytest tests/test_pr_dg_architecture_preflight.py -q -> 2 passed, 1 warning.

PR-DE affordability: python -m pytest tests/test_pr_de_exact_contract_deduplication.py -q -> 6 passed, 1 warning.

Routing and authority: python -m pytest tests/test_pr_ck_ordinary_resolver_selection.py tests/test_pr_cx_authority_assurance.py -q -> 39 passed, 1 warning.

Shared turn pipeline: python -m pytest tests/test_turn_pipeline_shared.py -q --tb=short -> 65 collected; 41 passed, 24 failed, 1 warning. Failures are in pre-existing shared social/final-emission expectations and are outside PR-DJ isolated experiment code.

Combined adjacent run: python -m pytest tests/test_pr_dg_architecture_preflight.py tests/test_pr_de_exact_contract_deduplication.py tests/test_pr_ck_ordinary_resolver_selection.py tests/test_pr_cx_authority_assurance.py tests/test_turn_pipeline_shared.py -q -> failed due to the same 24 tests/test_turn_pipeline_shared.py failures.
