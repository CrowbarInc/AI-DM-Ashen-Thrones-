# 07 — Regression Evidence

Authoritative final command (PowerShell, repository root):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_atgb_r1_04_readiness.py tests/test_atgb_r1_02_revision_boundary.py tests/test_state_authority.py -q --tb=short --basetemp=development/tmp/atgb_r1_04_release --junitxml=artifacts/atgb/atgb_r1_04/final.xml > artifacts/atgb/atgb_r1_04/final.txt 2>&1
$LASTEXITCODE | Set-Content artifacts/atgb/atgb_r1_04/final_exit.txt
```

Exit 0: 167 passed, zero failures/errors/skips. New readiness 36; existing R1-02
105; existing state-authority 26. One Starlette TestClient deprecation warning.
New tests cover import unset/enable/disable and reverse order in fresh subprocesses,
legacy import detection, normal/failure restoration, sequential modes, valid
pending production routing, preflight failures, three frozen mechanical correction
inputs through direct chat, and provider-failure no-execution safeguards.

Initial 28-test readiness slice passed. Expanded implementation and final model
assertions supersede that earlier count; intermediate final/verified runs also
passed. commands.json preserves exact initial, interrupted and final commands.
final.xml/final.txt/final_exit.txt are the authoritative completed record.

The existing HTTP authorization module was attempted together with R1-02 and state
tests. It stalled at the existing TestClient boundary and was interrupted with
Ctrl-C (tool process exit 1). No completed totals/JUnit file; no count of product
failures inferred. Progress output is retained in regression.txt. This matches
the prior reported environment limitation but its exact cause is not established.
No automatic timeout was configured. New subprocess isolation checks use explicit
30-second timeouts; none expired. Full repository regression was not run.

This is scoped structural regression evidence, not a full-suite green result or
proof of conversational adequacy. Existing frozen holdout data, expectations,
production orchestration, experimental candidates and unrelated tests unchanged.
