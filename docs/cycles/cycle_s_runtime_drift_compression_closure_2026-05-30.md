# Cycle S - Runtime Drift Compression Closure

Date: 2026-05-30

## 1. Executive Summary

Cycle S completed runtime drift compression as advisory/reporting-first work. The cycle added structured rerun comparison, opt-in successful-run scorecards, semantic delta frequency projection from existing metadata, an advisory scenario-spine artifact comparator, a deterministic seed seam audit, and protected-manifest policy language.

The protected replay hard gate was preserved. Cycle S strengthened observability and reduced one isolated source of process-randomized variance without adding broad runtime rewrites, exact prose gates, semantic judges, snapshot churn, or assertion loosening.

## 2. Original Goal

Cycle S set out to reduce nondeterministic replay drift and make legal rerun variance measurable before considering any thresholds.

The original measurement targets were:

- Reduce nondeterministic replay drift.
- Measure speaker drift.
- Measure route drift.
- Measure fallback escalation drift.
- Measure continuity phrasing drift.
- Measure semantic delta frequency.
- Reduce "technically legal but different" rerun variance.

## 3. Blocks Completed

### S1 - Golden Rerun Drift Scorecard

Purpose: Add a report-only comparator for two golden replay observation lists, covering speaker, route, fallback, text fingerprint, scaffold predicate, and runtime-lineage deltas.

Files changed/added:

- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`

Result: Golden replay observations can now be compared as successful-run scorecard data without creating a protected assertion or exact prose gate.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s1_marker
```

### S2 - Long-Session Rerun Artifact Writer

Purpose: Add opt-in artifact writing for successful golden replay rerun drift scorecards.

Files changed/added:

- `tests/conftest.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_golden_replay.py`

Result: Local runs can write `artifacts/golden_replay/rerun_drift_scorecard.json` and `artifacts/golden_replay/rerun_drift_scorecard.md` without changing CI pass/fail behavior.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py tests/test_golden_replay.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s2_marker
```

### S3 - Semantic Delta Frequency Projection

Purpose: Project existing response-delta / FEM metadata into golden replay observations and rerun summaries.

Files changed/added:

- `tests/helpers/golden_replay.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_golden_replay.py`

Result: Golden replay summaries and rerun scorecards now report response-delta checked/failed/repaired counts, kind counts, unknown counts, echo-overlap bands, and response-delta frequency deltas. This uses existing metadata only; no semantic similarity judge or semantic rewrite behavior was added.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_long_session_replay_summary_renderer_surfaces_operator_metrics -q
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s3_marker
```

### S4 - Scenario-Spine Rerun Delta Advisory

Purpose: Add a small comparator for two existing scenario-spine artifact directories from the same spine/branch.

Files changed/added:

- `tools/compare_scenario_spine_reruns.py`
- `tests/test_run_scenario_spine_validation.py`
- `docs/scenario_spine_validation.md`

Result: Operators can compare `transcript.json`, `session_health_summary.json`, `runtime_lineage_summary.json`, and optional `branch_divergence.json` from two artifact directories. The tool reports identity mismatches, turn count deltas, route/speaker/fallback deltas, health deltas, warning deltas, runtime-lineage deltas, and compact text fingerprint deltas. It remains advisory and is not wired into CI hard gates.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_run_scenario_spine_validation.py tests/test_scenario_spine_eval.py -q
```

### S5 - Deterministic Seed Seam Audit

Purpose: Audit replay-sensitive paths for process-randomized seed seams and address the known narrator-neutral fallback seed seam if safe.

Files changed/added:

- `game/speaker_contract_enforcement.py`
- `tests/test_runtime_drift_seed_audit.py`

Result: The isolated narrator-neutral fallback seed no longer uses Python `hash(...)`; it uses a stable SHA-256 fingerprint. A focused audit test now checks replay-sensitive speaker/fallback/final-emission paths for `hash()`, `random`, `uuid`, and `time` seed material.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_drift_seed_audit.py tests/test_speaker_contract_enforcement.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py tests/test_speaker_contract_enforcement.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s5_marker
```

### S6 - Protected Manifest Drift Policy Addendum

Purpose: Document Cycle S drift policy so new rerun drift tools remain advisory/report-only until repeated evidence justifies hard thresholds.

Files changed/added:

- `docs/testing/protected_replay_manifest.md`
- `docs/scenario_spine_validation.md`
- `docs/cycles/cycle_s_runtime_drift_compression_recon_2026-05-30.md`

Result: The protected replay manifest now states that rerun scorecards are advisory, exact prose identity is not a default protected gate, semantic delta frequency uses existing response-delta/FEM metadata only, scenario-spine rerun comparison is advisory, stable-seed audits protect replay-sensitive paths, and future hard thresholds require repeated evidence plus explicit manifest review.

Validation run:

```powershell
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s6_marker
```

## 4. Files Added / Modified

### Helpers / Tests

- `tests/conftest.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_runtime_drift_seed_audit.py`

### Tools

- `tools/compare_scenario_spine_reruns.py`

### Docs

- `docs/cycles/cycle_s_runtime_drift_compression_recon_2026-05-30.md`
- `docs/cycles/cycle_s_runtime_drift_compression_closure_2026-05-30.md`
- `docs/scenario_spine_validation.md`
- `docs/testing/protected_replay_manifest.md`

### Runtime Code

- `game/speaker_contract_enforcement.py`

## 5. Validation Summary

Known passing commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s1_marker
.\.venv\Scripts\python.exe -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py tests/test_golden_replay.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s2_marker
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_long_session_replay_summary_renderer_surfaces_operator_metrics -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s3_marker
.\.venv\Scripts\python.exe -m pytest tests/test_run_scenario_spine_validation.py tests/test_scenario_spine_eval.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_drift_seed_audit.py tests/test_speaker_contract_enforcement.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py tests/test_speaker_contract_enforcement.py -q
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s5_marker
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --basetemp=codex_pytest_tmp_cycle_s6_marker
```

During S3 validation, a couple of Windows temp-dir `PermissionError` failures occurred while pytest was atomically replacing JSON files under temporary directories. Immediate retries passed, so these were treated as non-blocking transient filesystem locks rather than Cycle S regressions.

## 6. Drift Compression Achieved

Cycle S achieved drift compression through measurement, artifact stability, and one narrow deterministic seed fix:

- Replay reruns now have structured comparison through the golden rerun comparator.
- Successful reruns can emit opt-in scorecards for local operator review.
- Semantic delta frequency is measured from existing response-delta/FEM metadata.
- Scenario-spine reruns can be compared advisory-only from artifact directories.
- A replay-sensitive process-randomized seed seam was removed from narrator-neutral speaker fallback behavior.
- Protected gates were not loosened.

## 7. Remaining Known Drift Seams

Remaining seams are intentionally conservative:

- Live model prose variance remains upstream.
- Exact prose identity remains intentionally non-gated by default.
- Scenario-spine rerun comparison remains advisory.
- Future hard thresholds require repeated evidence, explicit review, and protected-manifest updates.

## 8. Risks Avoided

Cycle S avoided:

- Broad runtime rewrites.
- Snapshot churn.
- New semantic judge behavior.
- Exact prose gates.
- CI hard-gate expansion without evidence.
- Assertion loosening.

## 9. Final Assessment

- Goal achieved: Yes.
- Protected replay impact: strengthened observability, no loosening.
- CI impact: existing hard gate preserved.
- Runtime impact: one narrow deterministic seed fix only.
- Maintenance impact: improved operator diagnostics and policy clarity.

## 10. Recommended Next Step

Commit Cycle S.

Before starting another implementation cycle, run a fresh scorecard audit to establish current advisory drift evidence from the completed tooling.
