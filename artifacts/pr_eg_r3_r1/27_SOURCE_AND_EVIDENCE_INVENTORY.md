# 27 — Source and Evidence Inventory

Evidence classes: STATIC source inspection; UNIT deterministic tests; CONTROLLED production HTTP with a stubbed expression provider; FRESH actual `/api/chat` with the configured model; STATE world, commitment, and delivered-history diffs; HISTORICAL the pre-change reproduction and the preserved first qualification.

`live_qualification.json` and `live_usage.jsonl` are the final 27-turn production results. `qualification_before_degree_repair.json`, `live_usage_before_degree_repair.jsonl`, `live_status_before_degree_repair.json`, and `live_plan_before_degree_repair.json` preserve the first sample. `live_plan.json`, `live_freeze.json`, `frozen_holdouts.json`, and `freeze.json` are the frozen inputs. `final_relevant_junit_confirm.xml` is the regression result used for the gate. `final_relevant_junit.xml` retains the two file-lock failures. `historical_reproduction_before.json` is the pre-change reproduction.

Reproduction from the repository root:

```
$env:PYTHONPATH = (Get-Location).Path
.venv/Scripts/python.exe -m pytest tests/test_pr_eg_r3_r1_expression_semantics.py tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r2c_speech_adoption.py tests/test_pr_eg_r2c_r2_reference_eligibility.py
$selection = Get-Content artifacts/pr_eg_r2c_r2/regression_selection.json | ConvertFrom-Json
.venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r3_r1_expression_semantics.py tests/test_pr_eg_r2c_r2_reference_eligibility.py --junitxml=artifacts/pr_eg_r3_r1/final_relevant_junit_confirm.xml
.venv/Scripts/python.exe tools/validate_pr_eg_r3_r1.py
.venv/Scripts/python.exe artifacts/pr_eg_r3_r1/build_review.py
```

The live command spends configured-provider requests and overwrites `live_qualification.json` and `live_usage.jsonl`. Copy both before a rerun. Credentials, `.env`, and `disposable_state` are excluded. The preserved first transcript is not the final qualification.
