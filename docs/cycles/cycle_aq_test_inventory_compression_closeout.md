# Cycle AQ — Test Inventory Compression Closeout

**Date:** 2026-06-06  
**Status:** Complete

---

## Final outcome summary

Cycle AQ compressed the committed test inventory from a **~5.2 MB monolithic diagnostic dump** into a **~13 KB governance artifact** while preserving all ownership, duplicate-name, marker, and registry-path enforcement. Governance-critical data stays committed; everything else is derived from a fresh full audit at `--check` time or available locally via `--full`.

The committed artifact is `tests/test_inventory_governance.json`. The legacy `tests/test_inventory.json` was removed in AQ3. Full diagnostic output lives at `artifacts/test_inventory_full.json` (gitignored, generated on demand).

**Final verification (closeout):**

| Command | Result |
| --- | --- |
| `py -3 tools/test_audit.py --check` | **Exit 0** — 4371 tests derived, 45 registry-owned files / 307 total |
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **67 passed** |

No failing checks. No additional compression implemented.

---

## Blocks completed (AQ1–AQ9)

| Block | Goal | Outcome |
| --- | --- | --- |
| **AQ1** | Inventory drift check mode | Added `--check` to `tools/test_audit.py` (in-memory regen vs committed JSON) |
| **AQ2** | CI drift gate + refresh | Wired `--check` into `convergence-checks.yml`; refreshed stale inventory |
| **AQ3** | Split governance vs full | Committed `test_inventory_governance.json`; removed `test_inventory.json`; added `--full` |
| **AQ4** | Derive registry index | Removed embedded `ownership_registry_index` from committed JSON |
| **AQ5** | Derive registry positions | Removed `files[].ownership_registry_positions` from committed JSON |
| **AQ6** | Derive per-test markers | Removed committed `tests[]`; marker coverage validated at `--check` |
| **AQ7** | Full-only triage aggregates | Removed `block_b_overlap_clusters` and `import_hub_modules` from committed JSON |
| **AQ8** | Registry-only file rows | Committed `files[]` reduced from 307 → 45 registry-owned paths |
| **AQ9** | Final payload minimization | Removed `cross_file_duplicate_test_names`; shrunk `summary` to stable metadata only |

Supporting recon artifacts (read-only, pre-implementation): `cycle_aq_test_inventory_compression_recon.md`, `cycle_aq_inventory_consumers.json`, `cycle_aq_inventory_duplication_map.json`.

Per-block details: `cycle_aq_block_aq1_implementation_summary.md` through `cycle_aq_block_aq9_implementation_summary.md`.

---

## Before / after inventory size

| Stage | Artifact | Size | Notes |
| --- | --- | ---: | --- |
| **Pre-AQ (recon)** | `tests/test_inventory.json` | ~5,461,291 bytes (~5.21 MB) | Monolithic; ~128k lines; full `tests[]` + diagnostic fields |
| **AQ3 split** | `tests/test_inventory_governance.json` | ~950,632 bytes (~0.91 MB) | First slim governance artifact |
| **AQ5** | governance JSON | ~914,308 bytes | After removing registry positions |
| **AQ6** | governance JSON | ~109,934 bytes | After removing `tests[]` |
| **AQ7** | governance JSON | ~81,563 bytes | After removing triage aggregates |
| **AQ8** | governance JSON | ~15,202 bytes | After registry-only `files[]` (45 rows) |
| **AQ9 (final)** | `tests/test_inventory_governance.json` | **13,237 bytes (~0.01 MB)** | Stable summary + 45 file rows |
| **Final reduction** | vs pre-AQ monolith | **~99.8%** smaller | |
| **Final reduction** | vs AQ3 governance | **~98.6%** smaller | |

Full diagnostic (local / `--full`, not committed): ~5.2 MB (`artifacts/test_inventory_full.json`, 307 files, 4371 tests).

---

## Final committed schema

**Top-level keys:** `summary`, `files` only.

```json
{
  "summary": {
    "inventory_schema_version": 2,
    "inventory_kind": "governance",
    "declared_pytest_markers": ["..."]
  },
  "files": [
    {
      "path": "tests/test_....py",
      "marker_set": ["..."],
      "collected_duplicate_base_names": [],
      "likely_architecture_layer": "gate|engine|planner|gpt|evaluator|smoke|transcript|gauntlet|general",
      "pytest_collected": 0
    }
  ]
}
```

**Committed `files[]` path set (45 rows):**

- 41 ownership-registry paths (direct owners + neighbor/compatibility suites)
- 4 additional cross-file duplicate file paths not already in the registry

**Explicitly absent from committed JSON:**

- `tests[]`
- `ownership_registry_index`
- `files[].ownership_registry_positions`
- `block_b_overlap_clusters`
- `import_hub_modules`
- `cross_file_duplicate_test_names`
- Derivables in `summary` (`pytest_collected_items`, `test_file_count`, `generated_utc`, shadowed-duplicate reports, bucket counts, etc.)

---

## Derived at `--check`

`py -3 tools/test_audit.py --check` regenerates a full inventory in memory, builds the governance payload, and validates:

| Derived concern | Validation |
| --- | --- |
| Governance JSON drift | Normalized compare (ignores removed timestamp field) |
| Per-test marker coverage | Every test has `marker_set`; file unions match per-test markers |
| Whole-suite file coverage | Full inventory file count vs live collect |
| Registry-owned `files[]` | All 45 required paths present; no non-governance paths committed |
| Cross-file duplicate allowlist | Derived `cross_file_duplicate_test_names` vs Python allowlist in `test_ownership_registry.py` |
| Triage aggregate structure | Full payload retains `block_b_overlap_clusters` and `import_hub_modules` |
| Summary shape | Committed summary contains only stable metadata fields |

Ownership pytest (`tests/test_ownership_registry.py`) reads committed governance JSON and additionally derives registry index, duplicate rows, and full-audit checks where needed.

---

## Remains in `--full` diagnostic output

`py -3 tools/test_audit.py --full` writes governance JSON **and** `artifacts/test_inventory_full.json` with the complete diagnostic payload:

| Category | Examples |
| --- | --- |
| All test files | 307 `files[]` rows with heuristics, imports, overlap hints, layer scores |
| Per-test rows | 4371 `tests[]` entries (markers, brittleness, feature areas, buckets) |
| Duplicate diagnostics | `cross_file_duplicate_test_names`, shadowed-name reports |
| Triage aggregates | `block_b_overlap_clusters`, `import_hub_modules`, feature-area spread |
| Full summary counts | `pytest_collected_items`, `test_file_count`, `generated_utc`, AST totals, bucket counts |
| Embedded registry snapshot | `ownership_registry_index` (diagnostic convenience) |

Use `--check-full` to verify an explicit full diagnostic file against a fresh regen (optional; not in CI).

---

## Commands for maintenance

| Task | Command |
| --- | --- |
| Regenerate committed governance JSON | `py -3 tools/test_audit.py` |
| Verify governance matches live suite (CI gate) | `py -3 tools/test_audit.py --check` |
| Generate local full diagnostic | `py -3 tools/test_audit.py --full` |
| Verify full diagnostic file | `py -3 tools/test_audit.py --check --check-full` |
| Run governance pytest | `py -3 -m pytest tests/test_ownership_registry.py -q` |
| Run audit-tool unit tests | `py -3 -m pytest tests/test_test_audit_tool.py -q` |
| Combined governance test suite | `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` |

**When to regenerate:** after adding/removing test modules, changing pytest markers, updating ownership registry paths, or adjusting direct-owner architecture heuristics in `tools/test_audit.py`.

---

## CI enforcement summary

| Workflow | Step | Command | Blocking |
| --- | --- | --- | --- |
| `convergence-checks.yml` | Pytest — test ownership registry | `python -m pytest tests/test_ownership_registry.py -q` | Yes |
| `convergence-checks.yml` | Test inventory drift check | `python tools/test_audit.py --check` | Yes |
| `content-lint.yml` | Test ownership registry (governance) | `python -m pytest tests/test_ownership_registry.py -q` | Yes |

Together these enforce: registry path presence, direct-owner layer alignment, cross-file duplicate allowlist, committed schema guards, and governance JSON drift detection with derived full-suite validation.

Runtime budget for `--check`: ~24–27 s (includes full `pytest --collect-only`).

---

## Non-blocking follow-ups

1. **Docs update** — `tests/TEST_AUDIT.md`, `tests/README_TESTS.md`, `cycle_aq_inventory_consumers.json`, and `docs/convergence_ci_inventory.md` still reference pre-AQ paths (`test_inventory.json`) and committed fields removed in AQ6–AQ9. Update to describe final governance schema and `--full` workflow.

2. **Optional schema v3 bump** — Consider bumping `INVENTORY_SCHEMA_VERSION` to signal registry-only `files[]` and minimal summary semantics to any external consumer. In-repo tests currently assert v2; bump is cosmetic unless external tooling exists.

3. **Optional nightly `--check-full`** — Add a scheduled job running `python tools/test_audit.py --check --check-full` against a CI-cached or artifact-stored full diagnostic file to catch diagnostic-only drift. Not required for PR gate; governance `--check` is sufficient for ownership enforcement.

---

## Closeout verdict

**Cycle AQ is complete.** Committed governance inventory is minimized to stable metadata and registry-owned file rows. All governance behavior is preserved through derived full audit validation at `--check` and ownership pytest. No further compression is planned unless new inventory fields are added to the generator.
