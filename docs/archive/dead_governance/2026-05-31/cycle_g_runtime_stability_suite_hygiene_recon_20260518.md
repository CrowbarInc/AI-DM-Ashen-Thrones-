# Cycle G Runtime Stability / Full-Suite Hygiene Recon

Date: 2026-05-19

Scope: reconnaissance only. No production behavior or test expectations were intentionally changed.

## Test Commands Run

Documented normal full-lane command:

```powershell
pytest
```

In this shell, `pytest` and `py -3` were not on `PATH`, and the local `.venv` launchers point at a missing interpreter. Operational equivalent used for collection/execution:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest
```

Raw output:

- `audits/cycle_g_full_suite_baseline_20260518.txt`

Diagnostic rerun with local pytest temp root, to separate repo failures from the inaccessible user temp directory:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest --basetemp=codex_pytest_tmp_cycle_g_full
```

Raw output:

- `audits/cycle_g_full_suite_basetemp_20260518.txt`

Focused probe commands:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_diegetic_fallback_narration.py::test_final_emission_opening_repair_debug_labels_legacy_diegetic_fallback_boundary -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_diegetic_node
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_diegetic_fallback_narration.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_diegetic_file
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_final_emission_debt_retirement.py::test_final_emission_modules_forbidden_substring_snapshot -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_debt_node
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_final_emission_debt_retirement.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_debt_file
```

Subset probes:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_final_emission_gate.py::test_canonical_upstream_prepared_direct_tuple_has_no_compatibility_local_ownership tests/test_final_emission_gate.py::test_canonical_opening_failure_recovers_via_upstream_prepared_payload_when_present tests/test_final_emission_gate.py::test_fail_closed_sealed_gate_missing_curated_facts_has_explicit_metadata tests/test_final_emission_gate.py::test_fail_closed_sealed_gate_with_empty_curated_facts -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_opening_subset
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_diegetic_fallback_narration.py tests/test_final_emission_gate.py::test_canonical_upstream_prepared_direct_tuple_has_no_compatibility_local_ownership tests/test_final_emission_gate.py::test_fail_closed_sealed_gate_missing_curated_facts_has_explicit_metadata -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_opening_mixed
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_final_emission_debt_retirement.py tests/test_final_emission_gate.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_g_debt_gate_subset
```

## Full-Suite Failure Summary

Baseline command without explicit local `--basetemp`:

- Result: `2 failed, 3695 passed, 35 skipped, 446 errors in 108.43s`.
- Error class: all inspected setup errors share `PermissionError: [WinError 5] Access is denied: 'C:\Users\Master Mandalcio\AppData\Local\Temp\pytest-of-Master Mandalcio'` from pytest `tmp_path` basetemp discovery.
- Interpretation: environment temp-root hygiene issue, not evidence of production regression or per-test assertion failure.

Diagnostic full suite with local `--basetemp`:

- Result: `2 failed, 4141 passed, 35 skipped in 59.92s`.
- Failures:
  - `tests/test_diegetic_fallback_narration.py::test_final_emission_opening_repair_debug_labels_legacy_diegetic_fallback_boundary`
  - `tests/test_final_emission_debt_retirement.py::test_final_emission_modules_forbidden_substring_snapshot`

## Alone-vs-Suite Matrix

| Test / cluster | Full suite with local basetemp | Node alone | Containing file alone | Nearby subset | Classification |
|---|---|---|---|---|---|
| Temp root / `tmp_path` setup | 446 errors without local basetemp | Not meaningful per-node; any `tmp_path` user can error before test body | Not meaningful | Local `--basetemp` removes this class | c) environment-level temp-root access issue |
| `test_final_emission_opening_repair_debug_labels_legacy_diegetic_fallback_boundary` | Fails | Fails | Fails (`..F..`) | Fails in mixed subset; newer canonical opening subset passes | b) deterministic alone |
| `test_final_emission_modules_forbidden_substring_snapshot` | Fails | Fails | Fails (`.F..`) | Fails with `test_final_emission_gate.py` present | b) deterministic alone |

No failing assertion currently looks suite-only, order-sensitive, or dependent on another test file once the temp-root environment issue is isolated.

## Failure Classification Table

| Failure | Symptom | Likely cause | Evidence | Do Not Fix Yet note |
|---|---|---|---|---|
| Pytest temp root setup errors | `PermissionError` while pytest scans `AppData\Local\Temp\pytest-of-Master Mandalcio` | shared-state pollution | The inaccessible shared pytest temp root causes setup failures across unrelated tests using `tmp_path`; local `--basetemp` eliminates all 446 errors. | Do not change production code. Prefer test runner/local config hygiene or a repo-scoped basetemp convention if this is accepted as a repo-local stability fix. |
| Diegetic fallback legacy boundary test | Expected deterministic opening prose, got `[opening_fallback_failed_closed: empty_curated_facts]` | stale expectation | The test directly calls `_enforce_response_type_contract` without running `maybe_attach_upstream_prepared_opening_fallback_payload`; newer canonical helpers in `tests/test_final_emission_gate.py` explicitly attach first and pass. Gate cleanup docs describe direct helper tests as legacy/attach-skipping fixtures. | Do not re-enable gate-local opening prose composition just to satisfy this stale direct-call test. That would undo fail-closed locality and upstream-prepared ownership. |
| Final emission debt snapshot | Snapshot omits `final_emission_sealed_fallback.py` and `final_emission_visibility_fallback.py`, but both files now exist | stale expectation | Cycle D/E audit docs identify those extracted helper modules as intentional ownership moves; failure is a file-list snapshot drift, not a forbidden-symbol hit. | Do not move code back into `final_emission_gate.py` or broaden runtime behavior. This should be a narrow audit snapshot update if the helper modules remain prose-free and debt-free. |

## Suspected Pollution Vectors

- Pytest basetemp root is shared outside the repo and currently inaccessible. This is the only confirmed suite-hygiene/shared-state vector from this recon.
- Full suite writes tracked runtime snapshots/logs under `data/` during execution (`data/combat.json`, `data/session.json`, `data/session_log.jsonl`, `data/world.json`). These were restored after the run. This is existing suite churn risk and should remain on the hygiene radar even though it did not cause the two assertion failures.
- `tests/conftest.py` mutates environment at session scope for upstream preflight/dashboard behavior. This did not appear causal for the current failures, but it is a relevant shared-state surface for future Cycle G probes.
- `game/final_emission_gate.py` uses per-output `_gate_turn_packet_cache` fields, but the inspected failures do not indicate leaked singleton/module state.
- The failing test files do not use `tmp_path`, random, time, UUID, global logging mutation, or un-restored monkeypatches in the failing paths.

## Files Recommended for GPT Review

### Temp Root / Full-Suite Runner Hygiene

- `pytest.ini`
- `tests/README_TESTS.md`
- `tests/conftest.py`
- `audits/cycle_g_full_suite_baseline_20260518.txt`
- `audits/cycle_g_full_suite_basetemp_20260518.txt`

### Opening Fallback Legacy Boundary Stale Test

- `tests/test_diegetic_fallback_narration.py`
- `tests/test_final_emission_gate.py`
- `game/final_emission_gate.py`
- `game/upstream_response_repairs.py`
- `game/opening_deterministic_fallback.py`
- `game/final_emission_meta.py`
- `docs/gate_cleanup_inventory.md`
- `audits/cycle_f_opening_fallback_owner_routing_recon_20260518.md`
- `audits/cycle_f_opening_fallback_owner_map_20260518.md`
- `audits/cycle_g_diegetic_node_20260518.txt`
- `audits/cycle_g_diegetic_file_20260518.txt`
- `audits/cycle_g_opening_subset_20260518.txt`
- `audits/cycle_g_opening_mixed_subset_20260518.txt`

### Final Emission Debt Snapshot Drift

- `tests/test_final_emission_debt_retirement.py`
- `game/final_emission_contract.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `docs/final_emission_debt_retirement.md`
- `audits/cycle_d_sealed_fallback_contraction_closure_2026-05-13.md`
- `audits/cycle_d_visibility_fallback_contraction_closure_2026-05-13.md`
- `audits/cycle_e_adjacent_fallback_family_ownership_recon_2026-05-17.md`
- `audits/cycle_g_debt_node_20260518.txt`
- `audits/cycle_g_debt_file_20260518.txt`
- `audits/cycle_g_debt_gate_subset_20260518.txt`

## Recommended Next Implementation Blocks

1. **Repo-Scoped Pytest Temp Root Hygiene**
   - Scope: add or document a repo-local pytest temp root for Windows/Codex runs, ideally without altering production code or masking true `tmp_path` misuse.

2. **Opening Fallback Legacy Direct-Call Test Realignment**
   - Scope: update the stale direct `_enforce_response_type_contract` test to either use the gate-aligned attach helper or assert the intentional fail-closed behavior for attach-skipping direct calls. Preserve structural metadata assertions; do not restore compatibility-local prose synthesis.

3. **Final Emission Debt Snapshot Module List Refresh**
   - Scope: add the extracted sealed/visibility helper modules to the static debt snapshot with empty expected forbidden-symbol sets after verifying they contain no forbidden debt symbols. Do not weaken the forbidden-symbol structural assertion.

4. **Tracked Runtime Snapshot Churn Recon**
   - Scope: separately inspect why full-suite execution mutates committed `data/*.json` and `data/session_log.jsonl`; prefer isolated temp state or cleanup fixtures over production behavior changes.

## Stop Point

No implementation changes are recommended inside this recon block. The current actionable failures are hygiene/stale-test issues, not evidence that production runtime behavior should change.
