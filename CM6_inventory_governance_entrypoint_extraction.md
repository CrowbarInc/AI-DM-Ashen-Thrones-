# CM6 — Inventory Governance EntryPoint Extraction

Date: 2026-06-27  
Scope: test file redistribution only. No production behavior changes. No inventory inclusion policy broadening.

## Summary

Moved **35** inventory/audit-schema pytest entrypoints from `tests/test_ownership_registry.py` into `tests/test_inventory_governance.py`. Helper logic remains in `tests/ownership_inventory_governance.py` and `tools/test_audit.py` (docstring and CI references updated).

Builds on CM5 (failure-dashboard inventory drift cleanup).

## New File Created

| File | Role |
|---|---|
| `tests/test_inventory_governance.py` | **325 lines**, **35** pytest entrypoints — owns committed inventory JSON shape, slim-artifact policy, derived-field omission/rejection, synthetic mutation tests, and live derived-metadata checks |

## Registry File Reduction

| Metric | After CM5 | After CM6 | CM6 Delta |
|---|---:|---:|---:|
| Lines | 819 | 551 | **−268** |
| Pytest entrypoints | 58 | 23 | **−35** |

| Metric | Original (pre-CM1) | After CM6 | Total Delta |
|---|---:|---:|---:|
| Lines | 2,357 | 551 | **−1,806** |
| Pytest entrypoints | 217 | 23 | **−194** |

## Tests Moved (35 total; names unchanged)

**Schema / slim JSON shape (4):**  
`test_inventory_schema_version_matches_audit_tool`, `test_governance_inventory_contains_required_fields`, `test_governance_summary_contains_stable_metadata_only`, `test_governance_committed_files_exclude_non_registry_paths`

**Omitted derived fields — positive checks (7):**  
`test_governance_omits_cross_file_duplicate_test_names`, `test_governance_file_rows_omit_committed_per_test_rows`, `test_governance_file_rows_omit_marker_set`, `test_governance_file_rows_omit_likely_architecture_layer`, `test_governance_file_rows_omit_collected_duplicate_base_names`, `test_governance_file_rows_omit_pytest_collected`, `test_governance_file_rows_omit_registry_positions`, `test_governance_omits_triage_aggregates`

**Synthetic rejection / mutation tests (11):**  
`test_governance_rejects_stored_cross_file_duplicate_test_names`, `test_governance_rejects_stored_per_test_rows`, `test_governance_rejects_stored_marker_set`, `test_governance_rejects_stored_likely_architecture_layer`, `test_governance_rejects_stored_collected_duplicate_base_names`, `test_governance_rejects_stored_pytest_collected`, `test_governance_rejects_non_registry_committed_file_row`, `test_governance_rejects_stored_triage_aggregates`, `test_governance_rejects_stored_registry_positions`, `test_governance_rejects_duplicate_direct_owner`, `test_governance_rejects_missing_inventory_path`, `test_governance_rejects_sharp_direct_owner_layer_mismatch`

**Derived metadata / live audit coherence (9):**  
`test_inventory_block_b_schema_v2_coherence`, `test_evaluator_neighbor_may_have_general_inventory_layer`, `test_direct_owner_general_disallowed_when_declared_layer_set`, `test_inventory_per_test_rows_include_marker_set`, `test_governance_registry_paths_have_derived_marker_sets`, `test_governance_registry_paths_have_derived_architecture_layers`, `test_governance_registry_paths_have_derived_duplicate_base_names`, `test_governance_registry_paths_have_live_collected_counts`, `test_cross_file_duplicate_allowlist_from_derived_full_audit`, `test_canonical_validation_layers_importable`

*(Note: 35 entrypoints total — grouped above for readability; all names preserved exactly.)*

## Tests Intentionally Left in Registry (6 inventory-related + 17 domain)

| Test | Why retained |
|---|---|
| `test_registry_defines_all_required_groups` | Registry source-of-truth identity |
| `test_governance_committed_files_include_all_registry_paths` | Registry ↔ committed inventory integration |
| `test_derived_registry_paths_present_in_inventory` | Registry paths inventory-backed; spot-checks gate direct-owner role + derived layer |
| `test_derived_registry_index_matches_live_registry` | Live registry index derivation (not JSON policy) |
| `test_ownership_registry_governance` | End-to-end `collect_ownership_governance_errors` integration against live registry + inventory |
| `test_allowlist_entries_have_non_empty_reasons` | Cross-file duplicate allowlist in `ownership_registry_contract` (registry contract, not JSON shape) |
| `test_*` domain locks (BA-7, AD-3, BI-8, …) | Direct-owner / neighbor / import-guard source-of-truth (unchanged) |

## Duplicates vs `tests/test_test_audit_tool.py`

| Overlap area | Resolution |
|---|---|
| `validate_governance_*` / `build_governance_payload_*` unit tests | **Remain in `test_test_audit_tool.py`** — audit-tool function behavior with synthetic payloads |
| Committed JSON policy + live inventory reads | **Moved to `test_inventory_governance.py`** — exercises `collect_ownership_governance_errors` and live `test_inventory_governance.json` |
| `test_cross_file_duplicate_allowlist_from_derived_full_audit` vs `test_validate_derived_cross_file_duplicate_governance_uses_allowlist` | **Both retained** — inventory file validates live full-audit output; audit-tool file validates helper in isolation |

No redundant tests removed; responsibilities split per task guidance.

## References Updated

| File | Change |
|---|---|
| `tests/ownership_inventory_governance.py` | Module docstring — enforcement entrypoints now `tests/test_inventory_governance.py` |
| `tests/test_ownership_registry.py` | Removed inventory schema block; pointer to `tests/test_inventory_governance.py`; trimmed imports/fixtures |
| `tests/test_test_audit_tool.py` | `test_convergence_checks_workflow_owns_inventory_governance` asserts new file in CI workflow |
| `.github/workflows/convergence-checks.yml` | Pytest step runs registry + inventory governance files |
| `docs/convergence_ci_inventory.md` | CI table and command references updated |

**Not broadened:** governance `files[]` inclusion policy, registry paths, allowlists, inventory JSON contents.

## Validation Commands and Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_inventory_governance.py -q` | **35 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **23 passed** |
| `python -m pytest tests/test_test_audit_tool.py -q` | **45 passed** |
| `python tools/test_audit.py --check` | **Pass** |
| `python -m pytest tests/test_compat_import_governance.py tests/test_gate_context_ownership_guards.py tests/test_gate_delegate_closeout_locks.py -q` | **159 passed** |

## Remaining Failures

None.

## Success Criteria Met

- Inventory/audit-schema coverage intact (35/35 in focused file + 6 integration tests in registry).
- Registry no longer hosts detailed inventory schema and synthetic mutation tests.
- All targeted test files and `tools/test_audit.py --check` pass.
- Registry file now primarily direct-owner source-of-truth, neighbor integration, and domain guard locks (23 entrypoints).
