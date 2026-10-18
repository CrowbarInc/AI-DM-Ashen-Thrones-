# 20 — Source and Evidence Inventory

source_changes.json: cycle-relative modified/new source hashes and active-data integrity. before_hashes.json + working_tree_before.txt + environment.json: actual starting worktree. before_sources/, diffs/, sources/: baseline/final production sources, cycle-only patches, modified/new tests and live runner.

baseline_local_junit.xml, post_junit.xml, post_final_junit.xml, final_junit.xml and console files: baseline, intermediate failures, final relevant-family and targeted/holdout evidence. holdout_first_* preserves the first frozen failure. regression_selection.json and regression_comparison.json retain identities. setup_baseline.py records the freeze. frozen_holdouts.json / freeze.json and live_plan.json / live_freeze.json retain immutable inputs.

baseline_reproduction.json / post_reproduction.json: complete controlled api.chat outputs and state/retention snapshots. baseline_historical_reproduction.json: exact historical matched security pair. reproduce.py reruns the three controls. persistence_matrix.py / persistence_results.json: six actual-storage controlled roundtrips.

live_qualification.json: complete 27-turn fresh HTTP results, history changes, commitment/world diffs, adoption decisions, timing and save/load. live_usage.jsonl / live_console.txt / live_status.json: provider accounting and failures. performance.json, state_audit.json, live_failure_audit.json and acceptance_gates.json: derived assessments. build_review.py generates all 20 reports and established CURRENT_REVIEW package. artifact_inventory.json lists hashes of packaged evidence. Disposable saves, credentials, caches and pytest temporary roots are excluded.

Reproduction commands from repository root (PowerShell; .venv/Scripts/python.exe):

```
.venv/Scripts/python.exe artifacts/pr_eg_r2c/reproduce.py post
.venv/Scripts/python.exe artifacts/pr_eg_r2c/persistence_matrix.py
$selection = Get-Content artifacts/pr_eg_r2c/regression_selection.json | ConvertFrom-Json
& .venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r2c_speech_adoption.py
.venv/Scripts/python.exe tools/validate_pr_eg_r2c.py live
.venv/Scripts/python.exe artifacts/pr_eg_r2c/build_review.py
```

The live command spends configured-provider requests and overwrites its transcript; copy existing evidence before a future rerun. The baseline setup command must not be rerun on the modified source and represented as a pre-change baseline. No recorded replay is claimed as fresh evidence.
