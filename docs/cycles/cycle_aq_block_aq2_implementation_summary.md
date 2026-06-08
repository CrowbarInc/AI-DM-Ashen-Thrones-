# Cycle AQ / Block AQ2 — Inventory Refresh and CI Drift Gate

**Date:** 2026-06-05  
**Status:** Complete

---

## Summary

Refreshed committed `tests/test_inventory.json` to match live pytest collection, wired `python tools/test_audit.py --check` into `convergence-checks.yml`, and confirmed drift check + governance tests pass. Minor heuristic tweaks in `tools/test_audit.py` were required so two direct-owner modules classify correctly after refresh (no schema or registry changes).

---

## Files changed

| File | Change |
| --- | --- |
| `tests/test_inventory.json` | Regenerated via `py -3 tools/test_audit.py` |
| `.github/workflows/convergence-checks.yml` | Added blocking **Test inventory drift check** step |
| `tools/test_audit.py` | Raised `gauntlet_regressions` gauntlet score; added `narrative_mode_contract` gpt signal (governance layer alignment after refresh) |
| `tests/test_test_audit_tool.py` | Added 2 heuristic regression tests for direct-owner layer scoring |

**Not changed:** inventory schema (v2), field set, `tests/test_ownership_registry.py`.

---

## Inventory count before / after

| Metric | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `summary.test_file_count` | 306 | 307 | +1 |
| `summary.pytest_collected_items` | 4,247 | 4,343 | +96 |
| `summary.generated_utc` | 2026-05-30T19:07:18Z | 2026-06-05T00:57:44Z | refreshed |
| `summary.inventory_schema_version` | 2 | 2 | unchanged |

Notable new module in inventory: `tests/test_final_emission_sealed_fallback.py`.

---

## CI workflow change

**File:** `.github/workflows/convergence-checks.yml`

**Location:** Immediately after **Pytest — test ownership registry**, before **Protected replay manifest registry parity**.

```yaml
- name: Test inventory drift check
  run: python tools/test_audit.py --check
```

This is a **hard-fail (blocking)** step in the existing convergence-checks job.

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **41 passed** |
| `py -3 tools/test_audit.py --check` (after refresh) | **Exit 0** — inventory matches fresh regen (4343 tests, 307 files) |

---

## `--check` confirmation

**Passes** after refresh. Repeated `--check` runs are stable aside from `summary.generated_utc` (ignored during comparison).

---

## Ancillary fix (refresh fallout)

First regen exposed two pre-existing governance layer mismatches that only surface when inventory heuristics are current:

| Group | Direct owner | Issue | Fix |
| --- | --- | --- | --- |
| `gpt_expression_surface_smoke` | `test_narrative_mode_output_validator.py` | Scored `general` | Boost gpt when `narrative_mode_contract` / validator filename present |
| `gauntlet_playability_validation` | `test_gauntlet_regressions.py` | Scored `gpt` (call_gpt patches) over `gauntlet` | Raise gauntlet filename score above gpt patch signal |

Second regen + tests confirmed green.

---

## Next block note

Schema compression (slim governance JSON, drop `tests[]` from commit) remains deferred per AQ plan — not started in AQ2.
