# Cycle AQ / Block AQ3 — Slim Governance Inventory Split

**Date:** 2026-06-05  
**Status:** Complete

---

## Summary

Split committed inventory into a slim governance artifact (`tests/test_inventory_governance.json`) and an optional full diagnostic payload (`artifacts/test_inventory_full.json`, gitignored). Default `py -3 tools/test_audit.py` writes governance only; `--full` writes diagnostic output. CI `--check` validates the governance artifact (unchanged workflow command).

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | `build_governance_payload()`, `--full`, `--output`, `--check-full`; default write/check targets governance JSON |
| `tests/test_inventory_governance.json` | **New** committed slim artifact |
| `tests/test_inventory.json` | **Removed** from repo (replaced by governance artifact) |
| `tests/test_ownership_registry.py` | Reads `test_inventory_governance.json`; added `test_governance_inventory_contains_required_fields` |
| `tests/test_test_audit_tool.py` | Updated for governance check flow; added slim/full generation tests |
| `.gitignore` | Ignore `artifacts/test_inventory_full.json` |

**Unchanged:** CI workflow command (`python tools/test_audit.py --check`), schema version (v2), governance assertion semantics.

---

## Committed inventory size before / after

| Artifact | Size | Lines (approx.) |
| --- | ---: | ---: |
| `tests/test_inventory.json` (before) | 5,461,291 bytes (~5.21 MB) | ~128,469 |
| `tests/test_inventory_governance.json` (after) | 950,632 bytes (~0.91 MB) | ~29,346 |
| **Reduction** | **~82.6%** | **~77.2%** |

Full diagnostic (local / `--full`, not committed): ~5,467,432 bytes (~5.21 MB).

---

## Fields kept in slim governance artifact

**Top-level**

| Field | Purpose |
| --- | --- |
| `summary` | Counts, schema version, declared markers; `inventory_kind: "governance"` |
| `files[]` | Slim per-module rows (see below) |
| `tests[]` | `{nodeid, marker_set}` only |
| `ownership_registry_index` | Embedded registry snapshot for drift checks |
| `block_b_overlap_clusters` | Schema v2 governance coherence |
| `import_hub_modules` | Schema v2 governance coherence |
| `cross_file_duplicate_test_names` | Allowlist governance |

**`files[]` row fields**

- `path`
- `marker_set`
- `ownership_registry_positions`
- `collected_duplicate_base_names`
- `likely_architecture_layer`
- `pytest_collected`

---

## Fields moved to full diagnostic output only

Written with `--full` or `--output PATH` to `artifacts/test_inventory_full.json`:

| Category | Examples |
| --- | --- |
| Per-file duplication | `collected_nodeids`, `collected_test_names` |
| Per-file heuristics | `architecture_layer_scores`, `overlap_hints`, `game_import_modules`, `game_import_roots`, `primary_feature_area_breakdown`, `bucket_distribution`, … |
| Per-test diagnostics | `brittleness`, `assertion_style`, `feature_areas`, `file_overlap_hints`, `keyword_overlap_hints`, … |
| Triage aggregates | `feature_areas_by_distinct_files`, `feature_area_primary_counts`, `top_high_brittleness_files`, `counts_by_majority_file_bucket`, … |
| Summary diagnostics | `files_with_shadowed_duplicate_test_defs`, `counts_by_primary_bucket`, … |

---

## Commands

| Command | Behavior |
| --- | --- |
| `py -3 tools/test_audit.py` | Write governance JSON (default) |
| `py -3 tools/test_audit.py --check` | Verify governance JSON (CI) |
| `py -3 tools/test_audit.py --full` | Write governance + full diagnostic |
| `py -3 tools/test_audit.py --check --check-full` | Verify full diagnostic at `--output` or default artifacts path |

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **45 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4349 tests, 307 files) |

---

## Follow-up compression candidates (not done in AQ3)

1. **Registry-only `files[]`** — Commit rows only for ~41 registry paths instead of all 307 modules (requires governance test adjustment for path presence semantics).
2. **Drop `tests[]` from governance** — Rely on `files[].marker_set` only; retire `test_inventory_per_test_rows_include_marker_set` or narrow scope.
3. **Derive `ownership_registry_index` at check time** — Remove embedded registry duplicate from committed JSON.
4. **Doc pointer updates** — `tests/TEST_AUDIT.md`, `docs/convergence_ci_inventory.md` still reference `test_inventory.json` in places (non-blocking).
5. **`--check-full` in CI** — Optional nightly job for diagnostic drift; not needed for normal PR gate.

---

## Inventory counts (current)

| Metric | Value |
| --- | ---: |
| Test files | 307 |
| Collected items | 4,349 |
| Schema version | 2 |
