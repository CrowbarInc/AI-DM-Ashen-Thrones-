# 23 — Source and Evidence Inventory

Evidence classes: STATIC source inspection; UNIT deterministic tests; CONTROLLED production HTTP with a stubbed expression provider; FRESH actual /api/chat with the configured model; STATE world, commitment, and delivered-history diffs; HISTORICAL the pre-repair transcript. The pre-repair transcript is not counted as the repaired qualification.

`live_qualification.json` and `live_usage.jsonl` are the repaired 27-turn production results. `live_qualification_before_name_repair.json` and `live_usage_before_name_repair.jsonl` preserve the rename defect and the earlier characterization adoption. `live_plan.json`, `live_freeze.json`, `frozen_holdouts.json`, and `freeze.json` are the untouched inputs. `baseline_relevant_junit.xml` and `final_relevant_junit.xml` are the regression runs. `regression_comparison.json`, `performance.json`, `quality.json`, `usage_totals.json`, `state_audit.json`, `integrity_checks.json`, and `acceptance_gates.json` are derived.

Reproduction from the repository root:

```
.venv/Scripts/python.exe -m pytest tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r2c_speech_adoption.py
$selection = Get-Content artifacts/pr_eg_r2c_r2/regression_selection.json | ConvertFrom-Json
& .venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r3_expressive_dialogue.py
$env:PYTHONPATH = (Get-Location).Path
.venv/Scripts/python.exe tools/validate_pr_eg_r3.py
.venv/Scripts/python.exe artifacts/pr_eg_r3/build_review.py
```

The live command spends configured-provider requests and overwrites `live_qualification.json` and appends `live_usage.jsonl`. Copy both before a rerun. Credentials, `.env`, and `disposable_state` are excluded. No recorded replay is claimed as the repaired fresh evidence.
