# CM5 — Failure Dashboard Inventory Drift Cleanup

Date: 2026-06-27  
Scope: committed governance inventory sync only. No production behavior changes.

## Summary

Resolved the remaining `tools/test_audit.py --check` drift by regenerating `tests/test_inventory_governance.json` via the canonical audit tool workflow. Four failure-dashboard suite files (added during the CE dashboard module split) were already covered by the cross-file duplicate allowlist but had not yet been written into the committed governance artifact.

## Missing File Paths Found

Reproduced with `python tools/test_audit.py --check`:

| Path |
|---|
| `tests/test_failure_dashboard_drift.py` |
| `tests/test_failure_dashboard_orchestration.py` |
| `tests/test_failure_dashboard_recurrence.py` |
| `tests/test_failure_dashboard_stability.py` |

**Why they belong in governance:** all four share the allowlisted cross-file duplicate base name `test_compatibility_wrappers_reference_same_functions` (see `tests/ownership_registry_contract.py` `_CROSS_FILE_DUPLICATE_ALLOWLIST`). `governance_committed_file_paths()` includes every file listed in derived `cross_file_duplicate_test_names` blocks, so a fresh regen correctly adds these four paths.

## How Inventory Was Updated

**Method:** canonical regen — `python tools/test_audit.py` (not hand-edited).

The tool:

1. Built a full diagnostic payload via `build_inventory_payload()` (pytest collect-only + registry index derivation).
2. Extracted slim governance rows via `build_governance_payload()` — only `GOVERNANCE_FILE_FIELDS` (`path` only per file row).
3. Wrote `tests/test_inventory_governance.json`.

**Diff:** +12 lines (+4 file rows), no summary schema changes, no derived fields committed:

- No `tests[]` / per-test rows
- No `marker_set`, `pytest_collected`, `collected_duplicate_base_names`, or `ownership_registry_positions` on file rows
- No triage aggregates or registry embed in committed JSON

Registry-owned file count: **64 → 68** (+4 failure-dashboard suite paths).

## Validation Commands and Results

| Command | Result |
|---|---|
| `python tools/test_audit.py --check` | **Pass** — `Inventory check OK` (6225 tests derived, 68 registry-owned files / 446 total) |
| `python -m pytest tests/test_test_audit_tool.py -q` | **45 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **58 passed** |
| `python -m pytest tests/test_compat_import_governance.py tests/test_gate_context_ownership_guards.py tests/test_gate_delegate_closeout_locks.py -q` | **159 passed** (26 + 33 + 100) |

## `tools/test_audit.py --check` Status

**Green.** No remaining inventory drift from the four failure-dashboard files.

## Remaining Failures

None introduced or left by CM5.

## Success Criteria Met

- `python tools/test_audit.py --check` passes.
- Ownership registry and extracted governance test files still pass.
- Inventory remains slim and policy-compliant (`path`-only file rows, stable summary fields only).
- No production behavior changes.
