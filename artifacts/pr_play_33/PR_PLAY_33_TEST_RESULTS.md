# Verification

Command: `.venv/Scripts/python.exe -m pytest tests/test_pr_play_33_process_ownership.py tests/test_playtest_startup_readiness.py --basetemp=development/tmp/pr_play_33_process --junitxml=artifacts/pr_play_33/process_tests.xml -ra`

Result: **24 passed**, 0 failed, 0 errors, 0 skipped. No retries or environment failures. Raw output and JUnit XML included. Tests remain offline; real small probe workers use no application/provider imports. Provider restriction preservation is checked in the child environment; PID/path/isolation mismatches are refused before HTTP.

Command: `.venv/Scripts/python.exe artifacts/pr_play_33/investigate.py`

Result: four process topology/exit/cleanup cases passed, with native Windows ancestry evidence and no remaining observed processes. No provider credentials, network or gameplay initialization.

Command: `.venv/Scripts/python.exe artifacts/pr_play_33/readiness.py`

Initial and final result: **exit 1, diagnostic AssertionError**, no retry. The actual module worker completed strict PID/isolation attestation and HTTP readiness (200). The controller then caught an AssertionError inside the diagnostic wait wrapper (native parent/child and safety checks); the exact assertion is unavailable because the snapshot was not persisted. It exported BLOCKED/application_startup_failure and completed owned-process cleanup. The outer diagnostic then asserted absence of session.json; isolated bootstrap session exists with turn_counter=0 and campaign_started=false. Both failures are disclosed. Of four planned controls, the first failed and the other three were never attempted. Its evidence is retained, with no failure hidden by retries. No planned controlled KeyboardInterrupt occurred, and no gameplay action loop was entered. The raw controller verdict must not be presented as a successful readiness matrix or gameplay verdict.

No full gameplay, opening-generation or PR-PLAY-32 live-focused suite was run. Those would exceed the zero-provider/no-gameplay scope. No provider requests or tokens were consumed by this investigation. Assistant/tool orchestration token use is separate and not measured by the application ledger.
