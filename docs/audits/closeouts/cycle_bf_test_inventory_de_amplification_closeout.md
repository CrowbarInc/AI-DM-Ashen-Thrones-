# Cycle BF — Test Inventory De-Amplification Closeout

**Date:** 2026-06-11  
**Status:** Complete (BF1–BF9)

---

## Final outcome

Cycle BF continued Cycle AQ’s inventory compression by **stripping derived heuristics from committed governance JSON**, **deriving them at `tools/test_audit.py --check`**, and **deduplicating CI** so ownership/inventory gates run once in `convergence-checks.yml` instead of in both convergence and content-lint workflows.

The committed artifact remains `tests/test_inventory_governance.json`. Full diagnostic output is still `artifacts/test_inventory_full.json` (`--full`, gitignored).

---

## Blocks completed (BF1–BF9)

| Block | Goal | Outcome |
| --- | --- | --- |
| **BF1** | Reduce test-module amplification | Shared `test_audit_module` + `full_inventory` fixtures in `tests/test_ownership_registry.py` — one `pytest --collect-only` per module run |
| **BF2** | Unit-test slim governance builders | `tests/test_test_audit_tool.py` covers `build_governance_payload`, row-shape guards, and derived-at-check validators without full-suite collect |
| **BF3** | Runbook / consumer map refresh | `tests/TEST_AUDIT.md`, `tests/README_TESTS.md`, `docs/cycles/cycle_aq_inventory_consumers.json` aligned to post-AQ governance vs full split |
| **BF4** | Derive collect counts at check | Removed `files[].pytest_collected` / `collected_nodeids` from committed rows; validated from full audit at `--check` |
| **BF5** | Derive in-file duplicate bases at check | Removed `files[].collected_duplicate_base_names` from committed rows; validated from full audit at `--check` |
| **BF6** | Derive architecture layers at check | Removed `files[].likely_architecture_layer` from committed rows; layer alignment uses `full_inventory_by_path` |
| **BF7** | Path-only committed rows | Removed `files[].marker_set`; bumped `inventory_schema_version` to **3**; marker governance derived at `--check` |
| **BF8** | CI de-amplification | Removed redundant `tests/test_ownership_registry.py` step from `content-lint.yml` |
| **BF9** | Closeout + regression guards | This document; workflow guard test; validation sign-off |

Prior compression baseline: `docs/cycles/cycle_aq_test_inventory_compression_closeout.md`.

---

## Before / after committed `files[]` row shape

### After AQ9 (pre-BF4)

```json
{
  "path": "tests/test_final_emission_gate.py",
  "marker_set": ["unit"],
  "collected_duplicate_base_names": [],
  "likely_architecture_layer": "gate",
  "pytest_collected": 42
}
```

### After BF6 (path + markers only)

```json
{
  "path": "tests/test_final_emission_gate.py",
  "marker_set": ["unit"]
}
```

### After BF7 / BF9 (final — schema v3)

```json
{
  "path": "tests/test_final_emission_gate.py"
}
```

**Top-level committed keys:** `summary`, `files` only.

**Summary (stable):**

```json
{
  "inventory_schema_version": 3,
  "inventory_kind": "governance",
  "declared_pytest_markers": ["..."]
}
```

**Registry-owned file count:** 45 rows (direct owners, neighbors, cross-file duplicate paths). Whole suite: 324 test modules / 4564 collected items (derived at `--check`).

---

## Derived-at-check validations

`python tools/test_audit.py --check` (or `py -3 tools/test_audit.py --check`) rebuilds the full inventory in memory, compares normalized governance JSON, then validates:

| Concern | Validator |
| --- | --- |
| Per-test marker coverage + file-level marker unions | `_validate_derived_marker_governance` |
| Registry paths have `marker_set` in full audit | `_validate_derived_registry_file_marker_sets` |
| Registry paths have collect counts | `_validate_derived_registry_file_collected_counts` |
| Registry paths have duplicate-base-name lists | `_validate_derived_registry_file_duplicate_base_names` |
| Registry paths have architecture layers | `_validate_derived_registry_file_architecture_layers` |
| Cross-file duplicate allowlist | `_validate_derived_cross_file_duplicate_governance` |
| Committed path set vs registry | `_validate_governance_committed_file_paths` |
| Committed row shape (path-only) | `_validate_governance_file_row_shape` |
| Full-suite counts | `_validate_derived_full_suite_counts` |
| Full-only triage aggregates | `_validate_full_diagnostic_triage_aggregates` |

`tests/test_ownership_registry.py` complements `--check` with responsibility-registry rules; it loads committed path-only JSON and derives heuristics via `full_inventory` fixture (`build_inventory_payload()`).

---

## CI ownership (post-BF8)

| Workflow | Inventory / ownership steps |
| --- | --- |
| **`.github/workflows/convergence-checks.yml`** | **Owner** — `python -m pytest tests/test_ownership_registry.py -q` and `python tools/test_audit.py --check` |
| **`.github/workflows/content-lint.yml`** | Planner convergence + content/doc lint only — **must not** rerun ownership registry |

Do not re-add `tests/test_ownership_registry.py` to `content-lint.yml` without updating this closeout and `docs/convergence_ci_inventory.md` with explicit justification.

---

## Regression guards (do not re-amplify)

1. **Committed `files[]` rows:** `path` only (`GOVERNANCE_FILE_FIELDS` in `tools/test_audit.py`).
2. **Do not recommit:** `marker_set`, `pytest_collected`, `collected_nodeids`, `collected_duplicate_base_names`, `likely_architecture_layer`, `ownership_registry_positions`, or other diagnostic fields on governance rows.
3. **Do not recommit top-level:** `tests[]`, `ownership_registry_index`, `cross_file_duplicate_test_names`, `block_b_overlap_clusters`, `import_hub_modules`.
4. **Pytest enforcement:** `tests/test_ownership_registry.py` — `test_governance_file_rows_omit_*`, `test_governance_rejects_stored_*`, `test_governance_inventory_contains_required_fields`.
5. **Tool enforcement:** `tools/test_audit.py` — `_validate_governance_file_row_shape` on committed + fresh payloads.
6. **CI enforcement:** `tests/test_test_audit_tool.py` — `test_content_lint_workflow_does_not_rerun_ownership_registry`.

Regenerate after registry/path edits: `py -3 tools/test_audit.py`.

---

## Validation commands / results (BF9 closeout)

Run from repository root:

```bash
py -3 tools/test_audit.py --check
py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q
```

| Command | BF9 result |
| --- | --- |
| `py -3 tools/test_audit.py --check` | **Exit 0** — 4564 tests derived, 45 registry-owned files / 324 total |
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **96 passed** (includes CI workflow guard) |

---

## Related artifacts

- `docs/convergence_ci_inventory.md` — seam matrix (test ownership owned by convergence-checks only)
- `docs/cycles/cycle_aq_test_inventory_compression_closeout.md` — AQ baseline
- `docs/cycles/cycle_aq_inventory_consumers.json` — consumer map (update when CI or schema changes)
- `tests/TEST_AUDIT.md` — operator runbook
