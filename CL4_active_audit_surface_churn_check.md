# CL4 Active Audit Surface Churn Check

## Files searched

- `docs/audits/`
- `artifacts/golden_replay/`
- `tools/`
- `tests/helpers/failure_dashboard_*`
- `tests/helpers/replay_drift_*`
- `tests/helpers/replay_bug_recurrence_*`
- `tests/helpers/replacement_attribution_inventory.py`
- `tests/helpers/failure_classification_alignment.py`
- `tests/helpers/synthetic_replay_evidence_bridge.py`
- Active tests that validate projection/audit/report surfaces.

Search targets included:

- `golden_replay_projection_extractors._build_projection_status`
- `golden_replay_projection_extractors._unavailable_paths_for_projection`
- `golden_replay_projection_extractors.protected_path_is_represented_in_observed_turn`
- `project_turn_observation _build_projection_status`
- `presence policy ... extractor`
- `unavailable policy ... extractor`
- `projection_owner="tests.helpers.golden_replay_projection_extractors"`

## Stale ownership references found

| Finding | Classification | Action |
|---|---|---|
| `tests/helpers/synthetic_replay_evidence_bridge.py` labeled `raw_signal_presence` and `normalized_signal_presence` as sourced by `project_turn_observation _build_projection_status` with `projection_owner="tests.helpers.golden_replay_projection_extractors"` | Active tested contract (`tests/test_cf7_synthetic_row_classifier_evidence_bridge.py`) and active generated/report-facing bridge matrix | Updated to `project_turn_observation presence policy _build_projection_status` and `projection_owner="tests.helpers.golden_replay_projection_presence"` |
| `docs/audits/CF7_synthetic_row_classifier_evidence_bridge.md` listed `raw_signal_presence`, `normalized_signal_presence` live source as bare `_build_projection_status` | Active audit-facing mirror of the CF7 bridge matrix | Updated to `golden_replay_projection_presence._build_projection_status` |
| `docs/audits/CF_replay_projection_responsibility_discovery.md` says the extractor owns presence classification, missing-source routing, and unavailable paths | Historical audit note only; describes pre-CL extraction concentration | Left unchanged |
| `docs/audits/CF3_raw_normalized_fem_field_matrix.md` and `docs/audits/CF5_projection_test_failure_locality.md` contain bare `_build_projection_status` references | Historical audit notes only; not active ownership contracts | Left unchanged |
| `docs/audits/BU_caller_fan_in.csv` and `docs/audits/BU_import_fan_in_fan_out.csv` contain old extractor symbol fan-in rows | Generated historical fan-in snapshots used by unrelated hotspot tools; not conceptual ownership labels | Left unchanged |
| `tools/ce5_split_golden_replay_projection.py` contains old split-script import text for `_build_projection_status` and representation helpers | Historical split tooling / stale script surface; not an active generated report path for CL4 | Left unchanged |
| `tests/helpers/synthetic_replay_evidence_bridge.py` still labels flat protected defaults with `projection_owner="tests.helpers.golden_replay_projection_extractors"` | Active tested contract, but not stale: this row refers to value extraction/default projection, not presence/unavailable policy | Intentionally left unchanged |

## Files changed

- `tests/helpers/synthetic_replay_evidence_bridge.py`
- `docs/audits/CF7_synthetic_row_classifier_evidence_bridge.md`

No runtime files were changed. No generated artifact refresh command was run; the CF7 audit doc change was a targeted one-line ownership-label correction matching the active helper.

## Files intentionally left unchanged as historical-only

- `docs/audits/CF_replay_projection_responsibility_discovery.md`
- `docs/audits/CF3_raw_normalized_fem_field_matrix.md`
- `docs/audits/CF5_projection_test_failure_locality.md`
- `docs/audits/BU_caller_fan_in.csv`
- `docs/audits/BU_import_fan_in_fan_out.csv`
- `tools/ce5_split_golden_replay_projection.py`

## Validation commands run and results

Requested command failed because `python` is not on PATH in this PowerShell session:

```powershell
python -m pytest tests/test_cf2_protected_field_routing.py tests/test_cf3_raw_normalized_fem_field_matrix.py tests/test_cf4_trace_nest_dotted_path_contract.py -q
```

Successful equivalent with bundled runtime Python:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_cf2_protected_field_routing.py tests\\test_cf3_raw_normalized_fem_field_matrix.py tests\\test_cf4_trace_nest_dotted_path_contract.py -q
```

Result: `123 passed`.

Report/artifact suite because an active report-facing helper/doc was touched:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_failure_dashboard_report.py tests\\test_replacement_attribution_inventory.py tests\\test_golden_replay_artifact_manifest.py tests\\test_cf6_generated_projection_artifact_governance.py -q
```

Result: `110 passed`.

Focused CF7 bridge test:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_cf7_synthetic_row_classifier_evidence_bridge.py -q
```

Result: `15 passed`.

Projection helper guard, run because the workspace already contains CL2/CL3 projection-helper changes:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_modules.py tests\\test_golden_replay_projection_presence_integration.py -q
```

Result: `51 passed`.

## Recommendation for next block

CL5 should be a no-op unless a specific active generator is selected for refresh. The remaining stale-looking extractor ownership references are historical discovery snapshots, generated fan-in data, compatibility imports, or value-extraction ownership labels rather than active presence/unavailable policy ownership.
