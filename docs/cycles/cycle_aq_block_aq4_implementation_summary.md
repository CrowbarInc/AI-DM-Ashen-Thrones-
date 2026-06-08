# Cycle AQ / Block AQ4 — Derive Ownership Registry Index

**Date:** 2026-06-05  
**Status:** Complete

---

## Summary

Removed `ownership_registry_index` from committed `tests/test_inventory_governance.json`. The index is now derived at runtime from `tests/test_ownership_registry.py::RESPONSIBILITY_REGISTRY` via `build_ownership_registry_index()`. Governance assertions remain equivalent; file-row `ownership_registry_positions` are still generated at audit time and compared against the derived index.

---

## Files changed

| File | Change |
| --- | --- |
| `tests/test_ownership_registry.py` | Added `build_ownership_registry_index()`; updated governance field tests to use derived index |
| `tools/test_audit.py` | `build_governance_payload()` omits embedded index; `_build_ownership_registry_index()` delegates to ownership module (full diagnostic only) |
| `tests/test_inventory_governance.json` | Regenerated without `ownership_registry_index` |
| `tests/test_test_audit_tool.py` | Governance payload tests assert index is omitted |

---

## Committed governance size before / after

| Metric | Before (AQ3) | After (AQ4) | Delta |
| --- | ---: | ---: | ---: |
| File size | 950,632 bytes (~0.91 MB) | 933,009 bytes (~0.89 MB) | **−17,623 bytes (~1.9%)** |

Top-level `ownership_registry_index` removed from committed JSON (confirmed: no `"ownership_registry_index"` key at document root).

---

## Behavioral preservation

| Check | Status |
| --- | --- |
| Direct-owner / neighbor path presence | Unchanged |
| Layer alignment on direct owners | Unchanged |
| Cross-file duplicate allowlist | Unchanged |
| Per-file `marker_set` / `collected_duplicate_base_names` | Unchanged |
| `files[].ownership_registry_positions` vs derived `files_roles` | Unchanged (now compares derived index) |
| Per-test `marker_set` rows (`tests[]`) | Unchanged (deferred to later block) |

**Test changes (equivalent meaning):**

- `test_inventory_embeds_neighbor_registry_index` → `test_derived_registry_index_matches_live_registry`
- `test_inventory_block_b_schema_v2_coherence` uses `build_ownership_registry_index()` instead of embedded JSON
- `test_governance_inventory_contains_required_fields` asserts `ownership_registry_index` is **absent**

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **45 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4349 tests, 307 files) |

---

## Remaining committed duplication candidates

1. **`tests[]` slim rows** (~4,349 `{nodeid, marker_set}` entries) — largest remaining committed bulk; targeted in a later AQ block.
2. **`files[].ownership_registry_positions`** — per-file copy of derived `files_roles` entries (~41 registry paths worth of data duplicated across file rows); could validate positions at check time instead of storing.
3. **`block_b_overlap_clusters` / `import_hub_modules`** — diagnostic triage aggregates; could move to full-only output if governance tests are narrowed.
4. **`cross_file_duplicate_test_names`** — small; authoritative allowlist reasons remain in Python only (unchanged).
5. **Doc references** — `tests/TEST_AUDIT.md` and related docs still mention legacy `test_inventory.json` / embedded index prose (non-blocking).

---

## Full diagnostic output

`py -3 tools/test_audit.py --full` still writes `ownership_registry_index` into `artifacts/test_inventory_full.json` for local triage.
