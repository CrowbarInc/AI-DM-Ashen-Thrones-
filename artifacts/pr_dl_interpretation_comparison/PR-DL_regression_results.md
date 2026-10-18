# PR-DL Regression Results

Focused suites:

Command: python -m pytest tests/test_pr_dl_interpretation_comparison.py tests/test_pr_dk_escalation_routing.py tests/test_pr_dj_selective_interpretation.py tests/test_pr_dg_architecture_preflight.py tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py tests/test_pr_cx_authority_assurance.py --tb=no
plugins: anyio-4.13.0
collected 47 items

tests\test_pr_dl_interpretation_comparison.py ........                   [ 17%]
tests\test_pr_dk_escalation_routing.py ..                                [ 21%]
tests\test_pr_dj_selective_interpretation.py .........                   [ 40%]
tests\test_pr_dg_architecture_preflight.py ..                            [ 44%]
tests\test_model_routing_escalation.py ..........                        [ 65%]
tests\test_model_routing_runtime.py .......                              [ 80%]
tests\test_pr_cx_authority_assurance.py .........                        [100%]

============================= 47 passed in 2.42s ==============================
Shared pipeline progress marks: 41 passed, 24 failed, 65 collected. Exit code 1. Timeout 180 seconds was not reached.

Shared turn-pipeline suite:

- Command: `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line`
- Timeout: 180 seconds.
- The process finished inside the timeout with exit code 1.
- The captured progress line and short summary are in `artifacts/pr_dl_interpretation_comparison/pipeline_stdout.txt`.
- Result: failed. This run is not a pass.
- PR-DK had previously recorded the same suite as incomplete after an interrupted wait. This PR-DL run completed and failed. The failures were not repaired.

Inherited failures were left in place. No production code was changed to chase them.
