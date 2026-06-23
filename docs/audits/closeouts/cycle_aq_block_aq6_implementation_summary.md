# Cycle AQ / Block AQ6 — Derive Per-Test Marker Coverage

**Date:** 2026-06-06  
**Status:** Complete

---

## Summary

Removed `tests[]` from committed `tests/test_inventory_governance.json`. Per-test `{nodeid, marker_set}` coverage is now derived from fresh audit output during `--check` via `derive_per_test_marker_rows()` and validated with `_validate_derived_marker_governance()`. File-level `files[].marker_set` remains in the committed artifact for governance. Full diagnostic output (`--full`) still retains the complete `tests[]` array.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | Dropped `tests[]` from `build_governance_payload()`; added `derive_per_test_marker_rows()`, `_validate_derived_marker_governance()`; `--check` validates derived marker coverage after governance compare |
| `tests/test_inventory_governance.json` | Regenerated without `tests[]` |
| `tests/test_ownership_registry.py` | Governance no longer requires committed per-test rows; rejects stored `tests[]`; `test_inventory_per_test_rows_include_marker_set` derives from fresh audit |
| `tests/test_test_audit_tool.py` | Minimal governance fixtures omit `tests[]`; full fixtures retain `tests[]`; new derive/validate helper tests |

---

## Governance size before / after

| Metric | Before (AQ5) | After (AQ6) | Delta |
| --- | ---: | ---: | ---: |
| File size | 914,308 bytes (~0.87 MB) | 109,934 bytes (~0.10 MB) | **−804,374 bytes (~88.0%)** |
| Lines (approx.) | ~28,300 | ~3,541 | **−87.5%** |

Confirmed: **zero** occurrences of `"tests"` key in committed governance JSON.

---

## Governance behavior preserved

| Check | Mechanism |
| --- | --- |
| File-level marker governance | `files[].marker_set` (committed, unchanged) |
| Per-test marker coverage | Derived at `--check` from full in-memory inventory |
| Marker consistency | `_validate_derived_marker_governance()` ensures every test has `marker_set` and file unions match |
| Registry direct/neighbor paths | Derived `files_roles` + inventory file rows (unchanged) |
| Direct-owner layer alignment | `files[].likely_architecture_layer` (unchanged) |
| Cross-file duplicate allowlist | `cross_file_duplicate_test_names` (unchanged) |

**New guards:** governance inventory must **not** store top-level `tests[]`.

**Full diagnostic:** `--full` output still includes complete `tests[]` with all per-test diagnostic fields.

---

## Commands run

```powershell
py -3 tools/test_audit.py
py -3 tools/test_audit.py --check
py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q
```

---

## Test results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **52 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4356 tests derived, 307 files) |

### New / updated tests

- `test_governance_file_rows_omit_committed_per_test_rows`
- `test_governance_rejects_stored_per_test_rows`
- `test_inventory_per_test_rows_include_marker_set` — now derives from `build_inventory_payload()`
- `test_derive_per_test_marker_rows_from_full_payload`
- `test_validate_derived_marker_governance_detects_file_union_mismatch`
- `test_governance_inventory_contains_required_fields` — asserts `tests` absent
- `test_build_governance_payload_strips_diagnostic_fields` — asserts `tests` absent from governance

---

## Remaining compression candidates

1. **`block_b_overlap_clusters` / `import_hub_modules`** — diagnostic triage aggregates; could move to full-only output.
2. **`cross_file_duplicate_test_names`** — small; allowlist reasons remain Python-only.
3. **Registry-only `files[]`** — Commit rows only for ~41 registry paths instead of all 307 modules.
4. **Summary count fields** — derivable from live pytest collect; could shrink to schema version + counts only.
5. **Doc references** — `tests/TEST_AUDIT.md`, `cycle_aq_inventory_consumers.json` still mention committed `tests[]` (non-blocking).
