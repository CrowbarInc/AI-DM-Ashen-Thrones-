# Cycle AO3 — Dashboard Evidence Manifest from Classifier Contract (Closeout)

**Date:** 2026-06-03  
**Status:** Completed

---

## Objective

Move dashboard Evidence-column key ownership into the classifier contract; dashboard module retains formatting and markdown rendering only.

---

## Files changed

| File | Change |
|---|---|
| `tests/failure_classification_contract.py` | Added contract-owned `FAILURE_DASHBOARD_EVIDENCE_MANIFEST`, derived row keys/labels, `failure_dashboard_evidence_manifest()`, import-time validation (29 keys, ⊆ classifier evidence) |
| `tests/helpers/failure_dashboard_report.py` | Removed hand-curated manifest; re-imports contract exports; kept `_format_dashboard_evidence_value` and `_evidence_cell` rendering |
| `tests/helpers/failure_classification_sync.py` | Removed duplicate `_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_LABELS`; strengthened `dashboard_evidence_manifest_misalignments()` to assert contract ↔ dashboard re-export parity |
| `tests/test_failure_classification_contract.py` | Added `test_ao3_dashboard_evidence_manifest_owned_by_classifier_contract`; dashboard subset test now calls sync misalignments |
| `tests/test_failure_dashboard_controlled_failures.py` | Imports manifest from contract; label lock test uses sync helper |

**Not changed:** `failure_classifier.py`, projection, golden fixtures, protected replay manifest, runtime, table columns, markdown formatters.

---

## Evidence manifest before / after

| Surface | Before | After |
|---|---|---|
| Authority location | `failure_dashboard_report.py` (hand-curated tuple) | `failure_classification_contract.py` |
| Dashboard evidence keys | 29 | 29 (unchanged) |
| Dashboard evidence labels | 29 | 29 (unchanged, same order) |
| Table columns | 17 | 17 (unchanged) |
| Duplicate label lock in sync | `_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_LABELS` (29 strings) | Removed — contract is sole source |
| Classifier optional fields | 47 | 47 (unchanged) |

**Dashboard module role after AO3:** import manifest → format values → render markdown. No independent evidence key list.

---

## Alignment locks added

- Contract import-time: 29 keys, no duplicates, ⊆ `CLASSIFIER_EVIDENCE_FIELDS`, labels match manifest order
- Sync: dashboard re-exports must equal contract manifest/keys/labels exactly
- Tests: `test_ao3_*`, existing controlled-failure evidence cell probes unchanged

---

## Tests executed

```powershell
python -m pytest tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
# 85 passed

python -m pytest tests/test_failure_classifier.py -q
# 66 passed

python -m pytest -m golden_replay -q
# 68 passed
```

---

## Follow-up recommendation for AO4

**AO4 — Unified synthetic observed-row fixture builder**

- Consolidate `failure_classification_sync.observed_failure_row()` and `failure_dashboard_fixtures._observed()` into one shared builder module
- Update `CONTROLLED_FAILURE_CASES` and classifier probe tests to import the unified factory
- Expected tests: `test_failure_classifier.py`, `test_failure_classification_contract.py`, `test_failure_dashboard_controlled_failures.py`
- Parallel with AO5/AO6; no dependency on AO3 beyond stable contract imports

**Optional later:** Derive `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` as `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` to eliminate the duplicate 47-field frozenset (set equality already enforced at import).

---

## Risks

- Adding a dashboard Evidence key now requires editing `failure_classification_contract.py` only — sync fails if dashboard module drifts
- Circular import avoided: contract → projection (AO2); dashboard → contract; sync → contract + dashboard (lazy import in misalignment helper only)
