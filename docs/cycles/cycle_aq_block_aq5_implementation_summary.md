# Cycle AQ / Block AQ5 — Derive File Registry Positions

**Date:** 2026-06-05  
**Status:** Complete

---

## Summary

Removed `files[].ownership_registry_positions` from committed `tests/test_inventory_governance.json`. Registry positions are derived at runtime via `build_ownership_registry_index()` (parameterized by the active responsibility registry). Governance checks validate registry-owned paths against inventory file rows without requiring stored positions.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | Dropped `ownership_registry_positions` from `GOVERNANCE_FILE_FIELDS`; full diagnostic rows still include it |
| `tests/test_ownership_registry.py` | `build_ownership_registry_index(registry=…)`; governance errors reject stored positions; new derived-path tests |
| `tests/test_inventory_governance.json` | Regenerated without per-file `ownership_registry_positions` |
| `tests/test_test_audit_tool.py` | Minimal fixtures and governance payload test updated |

---

## Governance size before / after

| Metric | Before (AQ4) | After (AQ5) | Delta |
| --- | ---: | ---: | ---: |
| File size | 933,009 bytes (~0.89 MB) | 914,308 bytes (~0.87 MB) | **−18,701 bytes (~2.0%)** |

Confirmed: **zero** occurrences of `ownership_registry_positions` in committed governance JSON.

---

## Governance behavior preserved

| Check | Mechanism |
| --- | --- |
| Registry direct/neighbor paths in inventory | Existing `_paths_for_group` loop + new derived `files_roles` path check |
| Direct-owner layer alignment | `files[].likely_architecture_layer` (unchanged) |
| Marker / duplicate-base-name fields | `files[].marker_set`, `collected_duplicate_base_names` (unchanged) |
| Cross-file duplicate allowlist | `cross_file_duplicate_test_names` (unchanged) |
| Per-test marker rows | `tests[]` (unchanged; deferred block) |

**New guards:** governance inventory must **not** store `ownership_registry_positions` on any file row.

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **48 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4352 tests, 307 files) |

### New / updated tests

- `test_governance_file_rows_omit_registry_positions`
- `test_derived_registry_paths_present_in_inventory`
- `test_governance_rejects_stored_registry_positions`
- `test_inventory_block_b_schema_v2_coherence` — derived paths must exist in inventory (no stored position compare)
- `test_governance_inventory_contains_required_fields` — asserts positions absent

---

## Remaining committed duplication candidates

1. **`tests[]`** (~4,352 `{nodeid, marker_set}` rows) — largest remaining bulk; next AQ block candidate.
2. **`block_b_overlap_clusters` / `import_hub_modules`** — diagnostic triage aggregates; could move to full-only output.
3. **`cross_file_duplicate_test_names`** — small; allowlist reasons remain Python-only.
4. **Summary count fields in `summary`** — derivable from live pytest collect; could shrink to schema version + counts only.
5. **Doc references** — `tests/TEST_AUDIT.md` still mentions legacy embedded index / `test_inventory.json` paths (non-blocking).

Full diagnostic (`--full`) still writes `files[].ownership_registry_positions` in `artifacts/test_inventory_full.json`.
