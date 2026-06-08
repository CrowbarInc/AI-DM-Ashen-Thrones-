# Cycle AQ / Block AQ9 — Final Governance Payload Minimization

**Date:** 2026-06-06  
**Status:** Complete

---

## Summary

Removed the last duplicated governance fields from committed `tests/test_inventory_governance.json`. `cross_file_duplicate_test_names` and derivable summary counts are now derived from fresh full audit output during `--check`. Committed governance retains only stable metadata plus registry-owned `files[]` rows.

---

## Files changed

| File | Change |
| --- | --- |
| `tools/test_audit.py` | `build_governance_summary()`, slim `build_governance_payload()`; `collect_cross_file_duplicate_governance_errors()`; `--check` validates summary shape, full-suite counts, and derived duplicate allowlist |
| `tests/test_inventory_governance.json` | Regenerated with minimal top-level schema |
| `tests/test_ownership_registry.py` | Rejects stored duplicate rows; allowlist checks use derived full audit; stable-summary tests |
| `tests/test_test_audit_tool.py` | Updated fixtures and validation tests for AQ9 schema |

---

## Governance size before / after

| Metric | Before (AQ8) | After (AQ9) | Delta |
| --- | ---: | ---: | ---: |
| File size | 15,202 bytes | 13,237 bytes | **−1,965 bytes (~12.9%)** |
| Top-level keys | 3 (`summary`, `files`, `cross_file_duplicate_test_names`) | **2** (`summary`, `files`) | −1 |
| `summary` fields | 5+ (included counts, timestamps) | **3** (stable only) | −2+ |

**Cumulative from AQ5 baseline:** 914,308 → 13,237 bytes (**~98.6%** smaller).

---

## Final committed top-level schema

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
      "likely_architecture_layer": "gate|engine|...",
      "pytest_collected": 0
    }
  ]
}
```

**Derived at `--check` (not committed):**

- `cross_file_duplicate_test_names` + allowlist enforcement
- `pytest_collected_items`, `test_file_count`, and other full diagnostic summary counts
- Per-test marker coverage (`tests[]`)
- Triage aggregates (`block_b_overlap_clusters`, `import_hub_modules`)
- Whole-suite non-registry file rows (262 paths)

**Retained in full diagnostic (`--full`):** all counts, duplicates, triage aggregates, complete `files[]` (307 rows), and `tests[]`.

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
| `py -3 -m pytest tests/test_test_audit_tool.py tests/test_ownership_registry.py -q` | **67 passed** |
| `py -3 tools/test_audit.py --check` | **Exit 0** (4371 tests derived, 45 registry-owned / 307 total files) |
| `py -3 tools/test_audit.py --full` | **Exit 0** (full diagnostic retains duplicates + counts) |

### New / updated tests

- `test_governance_summary_contains_stable_metadata_only`
- `test_governance_omits_cross_file_duplicate_test_names`
- `test_governance_rejects_stored_cross_file_duplicate_test_names`
- `test_cross_file_duplicate_allowlist_from_derived_full_audit`
- `test_validate_governance_summary_shape_rejects_derivable_fields`
- `test_validate_derived_cross_file_duplicate_governance_uses_allowlist`
- `test_ownership_registry_governance` — passes derived duplicate rows from full audit

---

## AQ closeout recommendation

**Yes — Cycle AQ is ready for closeout** from a governance-compression standpoint.

All planned compression blocks (AQ3–AQ9) are complete:

| Block | Outcome |
| --- | --- |
| AQ3 | Split governance vs full diagnostic |
| AQ4 | Derive ownership registry index |
| AQ5 | Derive registry positions |
| AQ6 | Derive per-test markers |
| AQ7 | Full-only triage aggregates |
| AQ8 | Registry-only `files[]` rows |
| AQ9 | Derived duplicates + stable summary |

CI gate (`tools/test_audit.py --check`) and ownership pytest enforce the full governance contract using derived full audit output. Committed JSON is ~13 KB — down ~98.6% from the pre-AQ5 ~914 KB artifact.

**Non-blocking follow-ups (post-closeout):**

1. Doc pointer updates (`tests/TEST_AUDIT.md`, `cycle_aq_inventory_consumers.json`, `tests/README_TESTS.md`) to describe final AQ9 schema.
2. Optional schema version bump to v3 if external consumers need an explicit signal (in-repo tests remain on v2).
3. Optional nightly `--check-full` job for diagnostic drift (not required for PR gate).
