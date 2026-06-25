# CF3 — Raw/Normalized FEM Field-Family Matrix

## Executive Summary

Golden replay projects **all 20 FEM-backed protected observation fields from raw FEM** (`read_fem_from_turn_for_replay`). Normalized FEM (`normalize_fem_for_replay_acceptance` → `normalize_final_emission_meta_for_observability`) is used for **presence diagnostics only** — not for overwriting projected flat field values.

**FEM Normalization Clarity (primary metric):** Before CF3, raw/normalized distinction was implicit in BL3 integration tests and scattered `test_final_emission_meta.py` cases. After CF3, every FEM-backed protected field has a contract row in `tests/helpers/fem_normalization_contract.py`, and **47 focused unit tests** in `tests/test_cf3_raw_normalized_fem_field_matrix.py` lock preservation, presence parity, adapter delegation, and projection extraction paths.

**Runtime behavior unchanged.** Normalization and projection logic were not modified.

---

## FEM Field Matrix

| Protected Field | Raw FEM Keys | Normalized Presence Tracked | Projection Owner | Test Owner |
|-----------------|--------------|----------------------------|------------------|------------|
| `final_emitted_source` | `final_emitted_source`, `final_route`, `upstream_prepared_emission_source` | Yes | `_first_present` on raw FEM | `test_final_emission_meta.py` |
| `final_emission_mutation_lineage` | `final_emission_mutation_lineage` | Yes | raw FEM flat extract | `test_final_emission_meta.py` |
| `response_type_required` | `response_type_required` | Yes | raw FEM flat extract | `test_final_emission_meta.py` |
| `response_type_candidate_ok` | `response_type_candidate_ok` | Yes | raw FEM flat extract | `test_final_emission_meta.py` |
| `response_type_repair_used` | `response_type_repair_used` | Yes | raw FEM flat extract | `test_final_emission_meta.py` |
| `response_type_repair_kind` | `response_type_repair_kind` | No | raw FEM flat extract | `test_final_emission_meta.py` |
| `upstream_prepared_emission_used` | `upstream_prepared_emission_used` | Yes | raw FEM flat extract | `test_golden_replay_fallback_upstream_projection.py` |
| `upstream_prepared_emission_valid` | `upstream_prepared_emission_valid` | Yes | raw FEM flat extract | `test_golden_replay_fallback_upstream_projection.py` |
| `upstream_prepared_emission_source` | `upstream_prepared_emission_source` | Yes | raw FEM flat extract | `test_golden_replay_fallback_upstream_projection.py` |
| `upstream_prepared_emission_reject_reason` | `upstream_prepared_emission_reject_reason` | Yes | raw FEM flat extract | `test_golden_replay_fallback_upstream_projection.py` |
| `opening_recovered_via_fallback` | `opening_recovered_via_fallback` | No | raw FEM flat extract | `test_golden_replay_fallback_opening_projection.py` |
| `opening_fallback_authorship_source` | `opening_fallback_authorship_source` | No | raw FEM flat extract | `test_golden_replay_fallback_opening_projection.py` |
| `opening_fallback_owner_bucket` | derived via `opening_fallback_owner_bucket_from_meta` | No | `read_opening_fallback_owner_bucket_for_replay` | `test_golden_replay_fallback_opening_projection.py` |
| `sealed_fallback_owner_bucket` | `sealed_fallback_owner_bucket` | Yes | raw FEM flat extract | `test_golden_replay_fallback_sealed_projection.py` |
| `visibility_fallback_owner_bucket` | `visibility_fallback_owner_bucket` | Yes | raw FEM flat extract | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_replacement_applied` | `visibility_replacement_applied` | Yes | raw FEM flat extract | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_fallback_pool` | `visibility_fallback_pool` | Yes | raw FEM flat extract | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_fallback_kind` | `visibility_fallback_kind` | Yes | raw FEM flat extract | `test_golden_replay_fallback_visibility_projection.py` |
| `fallback_family` | `fallback_family_used`, `realization_fallback_family` | Yes | `_resolve_fallback_family` (raw FEM + lineage) | `test_cf1_fallback_family_precedence.py` |
| `fallback_temporal_frame` | `fallback_temporal_frame` | No | raw FEM flat extract | `test_golden_replay_projection.py` |

**Classification summary:**

| Classification | Count | Meaning |
|----------------|-------|---------|
| raw_projected | 6 | Value from raw FEM; no normalized presence map entry |
| raw_and_normalized_presence | 13 | Value from raw FEM; both presence maps tracked |
| derived_from_raw_fem | 1 | `opening_fallback_owner_bucket` via owner-bucket read view |

---

## Normalization Ownership

| Layer | Canonical Owner | Duplicate Logic | Risk |
|-------|-----------------|-----------------|------|
| Replay acceptance adapter | `game.final_emission_replay_projection.normalize_fem_for_replay_acceptance` | Thin delegate only | Low |
| Observability normalization | `game.final_emission_meta.normalize_final_emission_meta_for_observability` | None for protected flat keys | Low |
| NA nested dict coercion | `normalize_merged_na_telemetry_for_eval` | Called from observability normalizer | Low — does not touch protected flat FEM |
| Dead-turn subtree defaults | `_DEAD_TURN_READ_DEFAULTS` merge inside observability normalizer | `read_dead_turn_from_gm_output` reads same defaults | Low |
| NA reason list coercion | Loop in observability normalizer on two list keys | Stage-diff projection merges separately | Low — non-protected lists |
| FEM flat extraction | `_extract_fem_flat_observed_fields(fem)` | Uses **raw** fem only | Low — intentional |
| Presence builder | `_build_projection_status(fem, fem_normalized, …)` | Separate raw vs normalized key checks | Low |

**Consumers intentionally using raw FEM:**

- `_extract_fem_flat_observed_fields`
- `_resolve_fallback_family`
- `read_opening_fallback_owner_bucket_for_replay`
- `_raw_presence_for_protected_spec` (key existence on raw dict)

**Consumers using normalized FEM:**

- `_normalized_presence_for_protected_spec` (key existence on normalized dict)
- `observed["fem_normalized_keys"]` (debug sorted key list)

---

## Presence Matrix

| Field | Raw Present (signal) | Normalized Present (signal) | Default (sparse) | Unavailable (sparse) | Notes |
|-------|----------------------|----------------------------|------------------|----------------------|-------|
| `final_emitted_source` | `_fem_has_any_key` on 3-key chain | same keys on normalized copy | `None` | Yes | Multi-key `_first_present` for value |
| `final_emission_mutation_lineage` | fem_key | fem_key | `None` | No | List-shaped on observed turn |
| `response_type_*` (4) | fem_key | fem_key | `None` | 3 of 4 (not `repair_kind`) | `repair_kind` has no unavailable_key |
| `upstream_prepared_*` (4) | fem_key | fem_key | `None` | No | Represented as `None`, not unavailable |
| `opening_*` (3) | fem_key / derived | N/A or fem_key | `None` | No | Bucket derived, not normalized |
| `sealed_*` / `visibility_*` (5) | fem_key | fem_key | `None` | No | |
| `fallback_family` | dual-family keys | dual-family keys | `None` | Yes | Bridge uses raw FEM + lineage |
| `fallback_temporal_frame` | not tracked | not tracked | `None` | No | |

**Sparse-turn lock (CF3):** When FEM keys absent, both `raw_signal_presence` and `normalized_signal_presence` are `False` for tracked fields. Fields with `unavailable_key` also appear in `observed["unavailable"]`.

**Rich-turn lock (CF3):** When FEM keys present, raw and normalized presence are both `True` — normalization does not strip top-level protected keys.

---

## Semantic Transformations

Normalization **does not alter protected flat FEM field values**. Documented transformations apply to non-protected or nested surfaces:

| Raw Input | Normalized Output | Owner | Reason |
|-----------|-------------------|-------|--------|
| `dead_turn: null` / non-mapping | `_DEAD_TURN_READ_DEFAULTS` merged dict | `normalize_final_emission_meta_for_observability` | Stable dead-turn read defaults |
| `dead_turn: {partial}` | defaults merged with partial | same | Preserve known keys, fill gaps |
| `narrative_authenticity_*` nested dicts `null` | `{}` | `normalize_merged_na_telemetry_for_eval` | NA telemetry stable empty maps |
| `narrative_authenticity_failure_reasons: "not-a-list"` | `[]` | observability normalizer | Malformed list guard |
| `narrative_authenticity_reason_codes` list | string-stripped list | observability normalizer | Whitespace filter |
| Dual fallback family keys | **unchanged values** | pass-through | CF1/CF3 lock no collapse |
| Protected flat FEM keys (all 20) | **same values** | pass-through shallow copy | CF3 parametrized preservation |

**Stage-diff NA projection** (`stage_diff_narrative_authenticity_projection`) merges reason code aliases — separate bounded surface, not used for protected field values.

---

## Tests Added

| File | Count | Field families protected |
|------|-------|--------------------------|
| `tests/helpers/fem_normalization_contract.py` | (helper) | 20-row FEM-backed field inventory |
| `tests/test_cf3_raw_normalized_fem_field_matrix.py` | 47 | All FEM-backed fields; dual-family; dead-turn; sparse/rich presence; multi-key `final_emitted_source`; opening bucket derivation |

**Existing tests retained as owners:**

- `test_final_emission_meta.py::test_normalize_final_emission_meta_for_observability_fills_nested_defaults_deterministically`
- `test_final_emission_meta.py::test_normalize_fem_preserves_dual_fallback_family_fields_without_collapse`
- `test_final_emission_meta.py::test_golden_replay_dual_family_precedence_matches_fem_normalization`
- `test_golden_replay_projection.py::test_bl3_*_presence_pipeline_locked`

---

## Behavior Changes

**None.** CF3 adds contract documentation and tests only. Confirmed invariants:

1. Protected flat FEM values are projected from **raw** FEM.
2. Normalization adds nested defaults (dead-turn, NA dicts) without rewriting flat protected stamps.
3. Raw and normalized presence agree when top-level FEM keys are present or uniformly absent.

---

## Remaining Risks

1. **`normalized_view_missing_raw_present` under-exercised end-to-end** — routing exists in `_missing_source_by_field_from_presence`, but observability normalization currently does not strip protected flat keys, so this path is rare in live projection.

2. **`missing_source_by_field` naming** — `projection_missing_raw_present` is emitted for all raw-present tracked fields on rich turns, not only projection failures; classifier consumers must interpret via paired presence maps.

3. **Opening owner bucket** — derived from raw FEM via attribution read views; not re-validated through normalized FEM (by design).

4. **Non-protected FEM keys** — response-delta and strict-social auxiliary keys on observed turn use raw `_first_present` but are outside the 41-path protected registry.

5. **Future normalization expansion** — if `normalize_final_emission_meta_for_observability` begins rewriting flat protected keys, CF3 preservation tests will fail first (intentional guard).

---

## Recommended Next Block

**Proceed with CF4 unchanged** (trace nest / dotted protected path contract), with these CF3 carry-forwards:

1. Add one live integration case for `normalized_view_missing_raw_present` only if a realistic normalization strip scenario is promoted — today none exists for flat protected keys.
2. Consider exporting `fem_backed_protected_field_paths()` from the public replay facade if tooling needs programmatic FEM inventory.
3. Do **not** switch protected value projection to normalized FEM without an explicit schema migration — raw projection is the current acceptance authority.

CF3 acceptance criteria met:

- [x] Every FEM-backed protected field has a raw→normalized contract row
- [x] Normalization ownership is explicit (adapter + meta owner)
- [x] Semantic transformations documented (nested-only; flat pass-through)
- [x] Raw vs normalized presence independently testable
- [x] 47 focused normalization tests added
- [x] Runtime behavior unchanged
- [x] CF4 can proceed without guessing FEM normalization policy
