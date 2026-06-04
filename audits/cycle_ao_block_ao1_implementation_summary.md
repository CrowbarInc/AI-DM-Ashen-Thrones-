# Cycle AO1 — Registry-Driven Projection Extraction (Closeout)

**Date:** 2026-06-03  
**Status:** Completed

---

## Objective

Reduce replay ownership fanout by making `PROTECTED_OBSERVATION_FIELDS` the primary authority for acceptance-side projection extraction, presence tracking, and unavailable-path computation.

---

## Files changed

| File | Change |
|---|---|
| `tests/helpers/golden_replay_projection.py` | Added `_ProtectedExtractionSpec` registry (41 paths), derived FEM/sanitizer extractors, registry-driven raw/normalized presence, unavailable computation, resolver helpers |
| `tests/test_golden_replay.py` | Added `test_ao1_protected_extraction_registry_matches_observation_registry` parity lock |

---

## Ownership touchpoints removed

| Before (manual / duplicated) | After (registry-driven) |
|---|---|
| Hardcoded `_FEM_FLAT_OBSERVED_EXTRACTORS` tuple (16 entries) | Derived from `_PROTECTED_EXTRACTION_SPECS` where `source=fem_flat` |
| Hardcoded `_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS` (7 entries) | Derived from registry where `source=sanitizer_trace` |
| Hardcoded `_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS` (4 entries) | Derived from registry where `source=sanitizer_lineage` |
| Manual `opening_recovered_via_fallback` / `opening_fallback_authorship_source` FEM reads in `project_turn_observation()` | Included in derived FEM flat extractors |
| 27-line inline `raw_signal_presence` dict | `_build_raw_signal_presence()` driven by spec `raw_presence` + trace containers + supporting specs |
| 21-line inline `normalized_signal_presence` dict | `_build_normalized_signal_presence()` driven by spec `normalized_presence` |
| 20-line inline `unavailable` list comprehension | `_compute_unavailable_paths()` driven by spec `unavailable_key` + trace containers |
| Inline `missing_source_by_field` loop | `_build_missing_source_by_field()` helper |
| Inline route/speaker/fallback resolution blocks | `_resolve_route_kind()`, `_resolve_selected_speaker_id()`, `_resolve_fallback_family()` |

**Net effect:** Adding or retargeting a protected FEM-flat or sanitizer field now requires updating `_PROTECTED_EXTRACTION_SPECS` (co-located with registry paths) rather than three separate manual lists.

---

## New public surface

- `protected_observation_extraction_registry()` — returns the 41-path extraction spec map for AO2+ consumers

---

## Behavior preserved (verified)

- Dual fallback-family precedence unchanged (`project_replay_fallback_family_from_fem` + `_project_replay_fallback_family`)
- Unavailable parent-prefix semantics unchanged
- Drift buckets unchanged
- 41 protected paths unchanged
- Observed turn shape unchanged (all golden_replay tests pass)

---

## Tests executed

```powershell
python -m pytest -m golden_replay -q --tb=short
# 67 passed

python -m pytest tests/test_golden_replay.py -k "ak5 or dual_family or project_turn" -q --tb=short
# 12 passed (includes new AO1 parity test)
```

---

## Risks / follow-up for AO2

| Item | Notes |
|---|---|
| `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` in contract | Still hand-maintained; AO2 should derive overlap from `protected_observation_extraction_registry()` + classifier extension set |
| `golden_replay.py` protected expectation DSL | Route/speaker/scaffold fragments still live in runner helper — AO1 follow-on or separate block |
| `_SUPPORTING_RAW_PRESENCE_SPECS` | Response-delta keys remain a small manual tuple (non-protected, classifier-only) |
| Trace leaf paths | Represented via nested `trace` dict; extraction specs document `source=trace_leaf` but projection logic remains in trace assembly |
| `sanitizer_lineage_legacy_rewrite_active` | Special-case logic retained in `_extract_sanitizer_lineage_observed_fields`; registered with `source=sanitizer_lineage_legacy` |

---

## Intentionally not changed

- Classifier, dashboard, manifest, runtime modules
- `PROTECTED_OBSERVATION_FIELDS` membership or drift buckets
- Compatibility wrappers (`protected_field_paths`, etc.)
