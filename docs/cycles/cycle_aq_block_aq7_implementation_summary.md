# Cycle AQ / Block AQ7 — Full-Only Triage Aggregates

**Date:** 2026-06-06  
**Status:** Complete

---

## Summary

Removed diagnostic-only triage aggregates `block_b_overlap_clusters` and `import_hub_modules` from committed `tests/test_inventory_governance.json`. These sections remain in full diagnostic output (`py -3 tools/test_audit.py --full`). Cross-file duplicate allowlist governance via `cross_file_duplicate_test_names` is unchanged and still committed. `--check` validates that full in-memory inventory retains triage aggregates via `_validate_full_diagnostic_triage_aggregates()`.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | Dropped `block_b_overlap_clusters` / `import_hub_modules` from `build_governance_payload()`; added `_validate_full_diagnostic_triage_aggregates()`; `--check` validates full-only aggregates after governance compare |
| `tests/test_inventory_governance.json` | Regenerated without triage aggregates |
| `tests/test_ownership_registry.py` | Governance rejects stored triage aggregates; schema coherence test derives clusters/hubs from fresh full audit |
| `tests/test_test_audit_tool.py` | Governance fixtures omit triage aggregates; full fixtures retain them; new validation test |

---

## Governance size before / after

| Metric | Before (AQ6) | After (AQ7) | Delta |
| --- | ---: | ---: | ---: |
| File size | 109,934 bytes (~0.10 MB) | 81,563 bytes (~0.08 MB) | **−28,371 bytes (~25.8%)** |
| Lines (approx.) | ~3,541 | ~2,862 | **−19.2%** |

Confirmed: **zero** occurrences of `block_b_overlap_clusters` or `import_hub_modules` in committed governance JSON.

---

## Fields removed from committed governance JSON

| Field | Status |
| --- | --- |
| `block_b_overlap_clusters` | **Removed** — full diagnostic only |
| `import_hub_modules` | **Removed** — full diagnostic only |
| `cross_file_duplicate_test_names` | **Retained** — required for allowlist governance |
| `tests[]` | Still absent (AQ6) |
| `files[].marker_set` | Still retained |

---

## Full diagnostic output confirmation

`py -3 tools/test_audit.py --full` writes `artifacts/test_inventory_full.json` with both removed aggregates present:

- `block_b_overlap_clusters` (includes `dense_ownership_theme_by_architecture_layer`, `cross_file_duplicate_test_base_names`, etc.)
- `import_hub_modules`

---

## Governance behavior preserved

| Check | Mechanism |
| --- | --- |
| Cross-file duplicate allowlist | `cross_file_duplicate_test_names` (committed, unchanged) |
| Registry direct/neighbor paths | Derived `files_roles` + inventory file rows (unchanged) |
| Direct-owner layer alignment | `files[].likely_architecture_layer` (unchanged) |
| Per-test marker coverage | Derived at `--check` (AQ6, unchanged) |
| Triage aggregate structure | `_validate_full_diagnostic_triage_aggregates()` at `--check`; `test_inventory_block_b_schema_v2_coherence` derives from full audit |

**New guards:** governance inventory must **not** store `block_b_overlap_clusters` or `import_hub_modules`.

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **55 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4359 tests derived, 307 files) |
| `py -3 tools/test_audit.py --full` | **Exit 0** (full diagnostic includes triage aggregates) |

### New / updated tests

- `test_governance_omits_triage_aggregates`
- `test_governance_rejects_stored_triage_aggregates`
- `test_validate_full_diagnostic_triage_aggregates`
- `test_inventory_block_b_schema_v2_coherence` — derives clusters/hubs from `build_inventory_payload()`
- `test_governance_inventory_contains_required_fields` — asserts triage aggregates absent
- `test_build_governance_payload_strips_diagnostic_fields` — asserts triage aggregates absent from governance

---

## Remaining compression candidates

1. **Registry-only `files[]`** — Commit rows only for ~41 registry-owned paths instead of all 307 modules. Largest remaining bulk (~80 KB is mostly `files[]` slim rows). Would require adjusting path-presence semantics: non-registry test files would no longer appear in committed governance, but registry direct/neighbor checks would still pass.
2. **`cross_file_duplicate_test_names`** — Small (~7 entries); could be derived at `--check` like markers, but currently committed for allowlist drift detection without full pytest collect in ownership pytest alone.
3. **Summary count fields** — `pytest_collected_items`, `test_file_count`, etc. are derivable from live collect; could shrink to schema version + `inventory_kind` only.
4. **Doc references** — `tests/TEST_AUDIT.md`, `cycle_aq_inventory_consumers.json` still mention committed triage aggregates (non-blocking).

**Cumulative AQ6+AQ7 reduction from AQ5 baseline:** 914,308 → 81,563 bytes (**~91.1%** smaller than pre-AQ6 governance).
