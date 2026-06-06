# Cycle AQ / Block AQ1 — Inventory Drift Check Mode

**Date:** 2026-06-04  
**Status:** Complete

---

## Summary

Added non-mutating `--check` mode to `tools/test_audit.py`. The tool now regenerates inventory in memory and compares it to committed `tests/test_inventory.json`, ignoring `summary.generated_utc`. Normal write mode is unchanged.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | Refactored `build_inventory_payload()` / `write_inventory()`; added `--check`, normalization, drift report, and exit codes |
| `tests/test_test_audit_tool.py` | Added 7 unit tests for comparison helpers and check dispatch |

**Not changed:** `tests/test_ownership_registry.py`, inventory schema, field set, or committed `tests/test_inventory.json`.

---

## Commands run

```powershell
py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q
py -3 tools/test_audit.py --check
```

---

## Test results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **39 passed** (32 ownership + 7 audit-tool) |
| `py -3 tools/test_audit.py --check` | **Exit code 1** (expected — committed inventory is stale) |

### New unit tests

- `test_normalize_inventory_ignores_generated_utc`
- `test_inventories_match_when_only_timestamp_differs`
- `test_inventories_do_not_match_when_nodeids_differ`
- `test_format_inventory_drift_report_lists_nodeid_and_file_deltas`
- `test_run_inventory_check_passes_when_committed_matches_fresh`
- `test_run_inventory_check_fails_when_committed_stale`
- `test_main_check_dispatches_without_writing`

---

## `--check` against committed inventory

**Fails** (as expected from AQ recon).

| Metric | Committed | Fresh regen | Delta |
| --- | ---: | ---: | ---: |
| Test files | 306 | 307 | +1 (`tests/test_final_emission_sealed_fallback.py`) |
| Collected items | 4,247 | 4,343 | +96 net nodeid churn (+175 added, −79 removed) |

Failure output includes added/removed files, sampled nodeids, and count summary. Timestamp-only differences would pass (covered by unit tests).

---

## Recommended CI command for Block AQ2

Add to `.github/workflows/convergence-checks.yml` (after ownership registry pytest, before or alongside other strict audits):

```yaml
- name: Test inventory drift check
  run: python tools/test_audit.py --check
```

**Note:** This step will **fail on current `main`** until someone runs `py -3 tools/test_audit.py` and commits the refreshed inventory in a separate maintenance commit. AQ2 options:

1. **Wire CI first + refresh commit** — land `--check` in CI together with inventory regen PR.
2. **Refresh first, then CI** — regen/commit inventory, then enable the CI step.

Runtime budget: ~26–39 s for full collect + compare on this machine.

Local parity:

```powershell
py -3 tools/test_audit.py --check
```

Refresh when stale:

```powershell
py -3 tools/test_audit.py
```
