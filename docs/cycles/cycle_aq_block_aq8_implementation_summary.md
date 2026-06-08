# Cycle AQ / Block AQ8 — Registry-Owned Governance File Rows

**Date:** 2026-06-06  
**Status:** Complete

---

## Summary

Reduced committed `tests/test_inventory_governance.json` by storing `files[]` rows only for registry-owned paths (41 registry paths + 4 cross-file duplicate files = 45 rows). Non-registry file metadata is derived from fresh full audit output during `--check`. Registry direct/neighbor checks, direct-owner layer alignment, marker consistency, and cross-file duplicate allowlist enforcement are unchanged.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | Added `governance_committed_file_paths()`, `_validate_governance_committed_file_paths()`; `build_governance_payload()` filters to registry + cross-file dup paths; `--check` validates path coverage |
| `tests/test_inventory_governance.json` | Regenerated with 45 registry-owned `files[]` rows |
| `tests/test_ownership_registry.py` | Added `_allowed_governance_committed_paths()`; rejects non-governance file rows; new registry-only file tests |
| `tests/test_test_audit_tool.py` | Fixtures use registry path; tests for filtering, missing-path failure, path validation |

---

## Governance size before / after

| Metric | Before (AQ7) | After (AQ8) | Delta |
| --- | ---: | ---: | ---: |
| File size | 81,563 bytes (~0.08 MB) | 15,202 bytes (~0.01 MB) | **−66,361 bytes (~81.4%)** |
| Lines (approx.) | ~2,862 | ~527 | **−81.6%** |

**Cumulative from AQ5 baseline:** 914,308 → 15,202 bytes (**~98.3%** smaller).

---

## Committed `files[]` row count before / after

| | Before (AQ7) | After (AQ8) |
| --- | ---: | ---: |
| `files[]` rows | 307 | **45** |
| Registry-owned paths | 41 (subset of 307) | 41 (all committed) |
| Cross-file dup-only paths | included in 307 | 4 additional (not in registry) |

Committed path set = ownership registry `files_roles` keys ∪ files referenced in `cross_file_duplicate_test_names`.

---

## Non-registry file rows: derived, not committed

Confirmed:

- Committed governance JSON has **45** `files[]` rows (registry + cross-file dup paths only).
- Full diagnostic (`artifacts/test_inventory_full.json`) retains **307** `files[]` rows with complete per-file metadata.
- `--check` validates whole-suite coverage via `summary.test_file_count` vs full inventory file count and runs marker union checks on all full-inventory files.

Example non-registry paths present only in full output: `tests/test_world_state.py`, `tests/test_narrative_planning.py` (also a cross-file dup path — committed for allowlist context).

---

## Governance behavior preserved

| Check | Mechanism |
| --- | --- |
| Registry direct/neighbor path presence | `collect_ownership_governance_errors` + committed registry rows |
| Direct-owner layer alignment | `files[].likely_architecture_layer` on registry rows |
| Cross-file duplicate allowlist | `cross_file_duplicate_test_names` (committed, unchanged) |
| Per-test marker coverage | Derived at `--check` from full inventory (AQ6) |
| Whole-suite file coverage | `_validate_governance_committed_file_paths()` + `_validate_derived_marker_governance()` at `--check` |
| Triage aggregates | Full diagnostic only (AQ7) |

**New guards:** governance `files[]` must not include non-governance paths; missing registry-owned paths fail `--check`.

---

## Commands run

```powershell
py -3 tools/test_audit.py
py -3 tools/test_audit.py --check
py -3 tools/test_audit.py --full
py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q
```

---

## Test results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **61 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4365 tests derived, 45 registry-owned / 307 total files) |
| `py -3 tools/test_audit.py --full` | **Exit 0** (307 files in full diagnostic) |

### New / updated tests

- `test_governance_committed_files_exclude_non_registry_paths`
- `test_governance_committed_files_include_all_registry_paths`
- `test_governance_rejects_non_registry_committed_file_row`
- `test_governance_payload_excludes_non_registry_files`
- `test_run_inventory_check_fails_when_registry_path_missing`
- `test_validate_governance_committed_file_paths_detects_missing_registry_path`

---

## Remaining AQ closeout candidates

1. **Derive `cross_file_duplicate_test_names` at `--check`** — Small (~7 entries); could remove from committed JSON if allowlist drift is validated purely from full audit output.
2. **Shrink `summary` fields** — Counts like `pytest_collected_items` / `test_file_count` are derivable from live collect; could retain only `inventory_schema_version`, `inventory_kind`, and `declared_pytest_markers`.
3. **Doc pointer updates** — `tests/TEST_AUDIT.md`, `cycle_aq_inventory_consumers.json`, `tests/README_TESTS.md` still describe pre-AQ8 committed shape (non-blocking).
4. **Optional `--check-full` in CI** — Nightly full diagnostic drift job; not required for PR gate.
5. **Schema version bump to v3** — Document registry-only `files[]` semantics if external consumers exist (none in-repo beyond governance tests).
