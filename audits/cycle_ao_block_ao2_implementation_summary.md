# Cycle AO2 — Classifier Evidence Derived from Protected Registry (Closeout)

**Date:** 2026-06-03  
**Status:** Completed

---

## Objective

Replace the hand-maintained `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` frozenset with a derivative of the AO1 protected observation extraction registry, preserving classifier output shape and all existing tests.

---

## Files changed

| File | Change |
|---|---|
| `tests/helpers/golden_replay_projection.py` | Added `_PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS`, `protected_classifier_evidence_field_paths()`, `protected_classifier_evidence_excluded_paths()`, import-time validation |
| `tests/failure_classification_contract.py` | `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS = protected_classifier_evidence_field_paths()`; removed 32-entry manual frozenset; added subset/disjoint import-time asserts |
| `tests/helpers/failure_classification_sync.py` | Stronger AO2 alignment checks; registry summary includes overlap/exclusion counts |
| `tests/test_failure_classification_contract.py` | Added `test_ao2_protected_classifier_evidence_derived_from_observation_registry` |

**Not changed:** `failure_classifier.py` behavior, dashboard module, manifest, runtime, golden fixtures.

---

## Evidence overlap before / after

| Set | Before | After |
|---|---:|---:|
| Required classifier fields | 15 | 15 (unchanged) |
| Optional evidence fields | 47 | 47 (unchanged) |
| Protected overlap (`PROTECTED_CLASSIFIER_EVIDENCE_FIELDS`) | 32 manual | 32 derived |
| Classifier extension-only fields | 15 manual | 15 manual |
| `CLASSIFIER_EVIDENCE_FIELDS` | 47 | 47 (unchanged) |

**Derivation rule (AO2):**

```
protected_classifier_evidence_field_paths()
  = { flat protected observation paths }
    − _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS
```

**Excluded flat protected paths (5 — classifier-ineligible):**

| Path | Reason |
|---|---|
| `resolution_kind` | Protected route-shape lock; not classifier optional evidence |
| `response_type_candidate_ok` | Protected structural; classifier uses required/repair fields |
| `opening_recovered_via_fallback` | Protected opening signal; not copied to classifier row |
| `final_text` | Semantic protected; classifier uses `final_text_hash` extension |
| `scaffold_leakage` | Semantic protected; routed via replay tags |

**Dotted protected paths (4)** excluded automatically by flat-path filter: `trace.canonical_entry.*`, `trace.social_contract_trace.route_selected`.

---

## Remaining manual classifier-only surfaces

| Surface | Count | Notes |
|---|---:|---|
| `REQUIRED_CLASSIFICATION_FIELDS` | 15 | Row identity/routing — intentionally manual |
| `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` | 47 | Full optional allowlist — manual (AO3 may derive dashboard subset) |
| `CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` | 15 | Classifier-only diagnostics — manual |
| Taxonomies (`ALLOWED_*`) | — | Unchanged |

**Classifier extension-only fields (15):**

`canonical_target_actor_id`, `emission_sublayer`, `fallback_content_owner`, `fallback_selection_owner`, `final_text_hash`, `missing_source_kind`, `mutation_source`, `post_gate_mutation_detected`, `prepared_emission_owner`, `repair_kind`, `sanitizer_changed_count`, `sanitizer_event_count`, `sanitizer_mode`, `sanitizer_rewrite_used`, `secondary_owner`

---

## Tests executed

```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q
# 99 passed

python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
# 51 passed

python -m pytest -m golden_replay -q
# 68 passed
```

---

## Alignment locks added

- Import-time: derived overlap ⊆ optional evidence; overlap ∩ extension = ∅
- Import-time (projection): 32-path count, flat-only, registry subset, exclusions parity
- Sync: `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS == protected_classifier_evidence_field_paths()`
- Sync: exclusions == flat protected − overlap (clear message when registry adds a path)

---

## Follow-up recommendation for AO3

**AO3 — Dashboard evidence manifest from classifier contract**

- Derive `FAILURE_DASHBOARD_EVIDENCE_MANIFEST` row keys from `CLASSIFIER_EVIDENCE_FIELDS` (or a labeled manifest exported from `failure_classification_contract.py`) instead of the hand-curated 29-key tuple in `failure_dashboard_report.py`
- Presentation formatting (`_format_dashboard_evidence_value`) stays in dashboard module
- Expected tests: contract tests, `test_failure_dashboard_controlled_failures.py`, classifier alignment

**Optional later:** Derive `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` as `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` to eliminate duplicate 47-field frozenset (requires careful review of field ordering/docs only — set equality already enforced).

---

## Risks

- Adding a flat protected observation path now requires updating `_PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS` (if ineligible) **or** `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` (if eligible) — import-time validation fails loudly either way
- Circular import risk mitigated: contract imports projection only; projection does not import contract
