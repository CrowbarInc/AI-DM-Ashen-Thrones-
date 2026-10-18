# PR-DK Regression Results

Environment: `ASHEN_DISABLE_LIVE_INTERPRETATION=1`.

Focused PR-DK tests:

- Command: `python -m pytest tests/test_pr_dk_escalation_routing.py -q`
- Result: 2 passed, 1 warning.

PR-DJ adapter/routing and PR-DG architecture preflight:

- Command: `python -m pytest tests/test_pr_dj_selective_interpretation.py tests/test_pr_dg_architecture_preflight.py -q`
- Result: 11 passed, 1 warning.

Routing and authority tests:

- Command: `python -m pytest tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py tests/test_pr_cx_authority_assurance.py -q`
- Result: 26 passed.

Shared turn-pipeline tests:

- Command: `python -m pytest tests/test_turn_pipeline_shared.py -q`
- Result: incomplete. The command produced no pytest output after an extended wait and was interrupted. No failure details were emitted before interruption.

Inherited failures:

- None observed in completed suites.

New failures:

- None observed in completed suites.
