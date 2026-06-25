# CF2 — Protected Field Source/Default Matrix

## Executive Summary

Every protected replay observation field (41 paths) now has an explicit **source/default/unavailable routing row** derived from the canonical extraction registry (`_PROTECTED_EXTRACTION_SPECS`) and schema defaults (`protected_observation_default_row`). A read-side contract builder (`tests/helpers/protected_field_routing_contract.py`) generates one row per field; **49 new unit tests** in `tests/test_cf2_protected_field_routing.py` lock defaults, unavailable routing, missing-source distinction, and synthetic-row risk.

**Protected Field Routing Clarity (primary metric):** Before CF2, routing policy was embedded in the 978-line extractor module and partially locked by three BL3 integration tests. After CF2, each field declares source path, normalized source (when tracked), default, unavailable rule, missing-source rule, drift bucket, classification, and first-line test owner in one contract matrix. Failures in defaults or unavailable routing now localize to `test_cf2_protected_field_routing.py` instead of broad golden replay suites.

**Runtime behavior unchanged.** No projection, default, or unavailable logic was modified.

---

## Protected Field Matrix

Legend:

- **Unavailable rule:** when the field path appears in `observed["unavailable"]`
- **Missing-source rule:** values in `observed["missing_source_by_field"]` (only fields with `raw_presence` tracking)
- **Default:** flat-path schema default from `protected_observation_default_row()`; dotted trace paths have no flat default

| Field | Source Path | Normalized Source | Default | Unavailable Rule | Missing-Source Rule | Drift Bucket | Owner Test |
|-------|-------------|-------------------|---------|------------------|---------------------|--------------|------------|
| `resolution_kind` | `payload.resolution.kind` | — | `None` | Never unavailable; `None` still represented | not tracked | structural_drift | `test_golden_replay_projection.py` |
| `route_kind` | trace `route_selected` → snap `resolution_compact.kind` → `resolution.kind` | — | `None` | Projected `None` → unavailable | raw absent → `runtime_missing_raw_absent`; raw present → `projection_missing_raw_present` | structural_drift | `test_cf1_route_and_trace_precedence.py` |
| `selected_speaker_id` | social-contract trace → transcript snapshot → `resolution.social.npc_id` | — | `None` | Projected `None` → unavailable | raw absent → `runtime_missing_raw_absent` | structural_drift | `test_cf1_speaker_projection_precedence.py` |
| `final_emitted_source` | FEM `_first_present(final_emitted_source, final_route, upstream_prepared_emission_source)` | `normalize_fem_for_replay_acceptance` | `None` | Projected `None` → unavailable | raw/normalized tracked; normalization gap → `normalized_view_missing_raw_present` | structural_drift | `test_final_emission_meta.py` |
| `final_emission_mutation_lineage` | FEM `final_emission_mutation_lineage` | `normalize_fem_for_replay_acceptance` | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `response_type_required` | FEM `response_type_required` | normalized FEM | `None` | Projected `None` → unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `response_type_candidate_ok` | FEM `response_type_candidate_ok` | normalized FEM | `None` | Projected `None` → unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `response_type_repair_used` | FEM `response_type_repair_used` | normalized FEM | `None` | Projected `None` → unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `response_type_repair_kind` | FEM `response_type_repair_kind` | — | `None` | Never unavailable | not tracked | structural_drift | `test_final_emission_meta.py` |
| `upstream_prepared_emission_used` | FEM `upstream_prepared_emission_used` | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `upstream_prepared_emission_valid` | FEM `upstream_prepared_emission_valid` | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `upstream_prepared_emission_source` | FEM `upstream_prepared_emission_source` | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `upstream_prepared_emission_reject_reason` | FEM `upstream_prepared_emission_reject_reason` | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_final_emission_meta.py` |
| `sanitizer_empty_fallback_used` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_empty_fallback_source` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_empty_fallback_owner` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_lineage_mode` | sanitizer_trace key → `sanitizer_mode` context | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_lineage_changed_count` | sanitizer_trace key → `sanitizer_changed_count` context | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_lineage_dropped_count` | sanitizer_trace key → `sanitizer_dropped_count` context | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_lineage_empty_fallback_used` | sanitizer_trace key → context fallback | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_lineage_legacy_rewrite_active` | sanitizer_trace / derived from mode | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_strict_social_fallback_used` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_strict_social_selection_owner` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_strict_social_prose_owner` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `sanitizer_strict_social_source` | payload `sanitizer_trace` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_sanitizer_projection.py` |
| `opening_recovered_via_fallback` | FEM flat | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_opening_projection.py` |
| `opening_fallback_authorship_source` | FEM flat | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_opening_projection.py` |
| `opening_fallback_owner_bucket` | `read_opening_fallback_owner_bucket_for_replay(FEM)` | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_fallback_opening_projection.py` |
| `sealed_fallback_owner_bucket` | FEM flat | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_golden_replay_fallback_sealed_projection.py` |
| `visibility_fallback_owner_bucket` | FEM flat | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_replacement_applied` | FEM flat | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_fallback_pool` | FEM flat | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_golden_replay_fallback_visibility_projection.py` |
| `visibility_fallback_kind` | FEM flat | normalized FEM | `None` | Never unavailable | raw/normalized tracked | structural_drift | `test_golden_replay_fallback_visibility_projection.py` |
| `fallback_family` | diegetic FEM → provenance FEM → lineage bridge | normalized FEM dual-family keys | `None` | Projected `None` → unavailable | raw/normalized tracked | structural_drift | `test_cf1_fallback_family_precedence.py` |
| `fallback_temporal_frame` | FEM flat | — | `None` | Never unavailable | not tracked | structural_drift | `test_golden_replay_projection.py` |
| `trace.canonical_entry.target_actor_id` | `trace.canonical_entry.target_actor_id` | — | nested trace | Parent container empty → `trace.canonical_entry` unavailable | not tracked (container raw presence only) | structural_drift | `test_golden_replay_projection.py` |
| `trace.canonical_entry.target_source` | `trace.canonical_entry.target_source` | — | nested trace | same | not tracked | structural_drift | `test_golden_replay_projection.py` |
| `trace.canonical_entry.reason` | `trace.canonical_entry.reason` | — | nested trace | same | not tracked | structural_drift | `test_golden_replay_projection.py` |
| `trace.social_contract_trace.route_selected` | `trace.social_contract_trace.route_selected` | — | nested trace | Parent empty → `trace.social_contract_trace` unavailable | not tracked | structural_drift | `test_golden_replay_projection.py` |
| `final_text` | `snap.gm_text` | — | `""` | Never unavailable | not tracked | semantic_drift | `test_golden_replay_projection.py` |
| `scaffold_leakage` | `final_text_has_scaffold_leakage(final_text)` | — | `False` | Never unavailable | not tracked | semantic_drift | `test_golden_replay_projection.py` |

Contract rows are programmatically generated by `build_protected_field_routing_matrix()` and must stay aligned with `_PROTECTED_EXTRACTION_SPECS` (locked by `test_cf2_routing_matrix_covers_every_protected_field`).

---

## Field Classification

| Field | Classification | Projection Owner | Test Owner | Notes |
|-------|----------------|------------------|------------|-------|
| `resolution_kind` | direct_runtime_fem | `_project_flat_protected_observed_fields` / resolution source | `test_golden_replay_projection.py` | Not FEM-backed despite resolution payload |
| `route_kind` | snapshot_transcript | `_resolve_route_kind` | `test_cf1_route_and_trace_precedence.py` | Combines trace + snap + resolution |
| `selected_speaker_id` | snapshot_transcript | `_resolve_selected_speaker_id` | `test_cf1_speaker_projection_precedence.py` | |
| `final_emitted_source` | direct_runtime_fem | FEM flat extractor + multi-key `_first_present` | `test_final_emission_meta.py` | Normalized presence tracked |
| `final_emission_mutation_lineage` | direct_runtime_fem | FEM flat; list-shaped on observed turn | `test_final_emission_meta.py` | |
| `response_type_*` (4 fields) | direct_runtime_fem | FEM flat | `test_final_emission_meta.py` | Three have unavailable_key |
| `upstream_prepared_emission_*` (4 fields) | direct_runtime_fem | FEM flat | `test_final_emission_meta.py` | No unavailable_key; `None` represented |
| `sanitizer_*` (12 fields) | direct_runtime_fem / derived | sanitizer_trace + lineage extractors | `test_golden_replay_fallback_sanitizer_projection.py` | Lineage fields use context fallbacks |
| `opening_*` (3 fields) | direct / derived | FEM flat + opening bucket read view | `test_golden_replay_fallback_opening_projection.py` | Bucket is derived, not raw FEM key |
| `sealed_*` / `visibility_*` (5 fields) | direct_runtime_fem | FEM flat | fallback family projection tests | Normalized presence tracked |
| `fallback_family` | derived_runtime_fem | `_resolve_fallback_family` | `test_cf1_fallback_family_precedence.py` | Collapses dual FEM + bridge |
| `fallback_temporal_frame` | direct_runtime_fem | FEM flat | `test_golden_replay_projection.py` | |
| `trace.*` (4 dotted paths) | trace_debug | trace nest under `observed["trace"]` | `test_golden_replay_projection.py` | Container-level unavailable |
| `final_text` | snapshot_transcript | `snap.gm_text` | `test_golden_replay_projection.py` | Default `""` not `None` |
| `scaffold_leakage` | derived_text | regex + payload-shape detector | `test_golden_replay_projection.py` | Default `False` |

Synthetic/default-only usage applies to **`observed_projection_schema_defaults()`** and **`synthetic_observed_replay_row()`** — not to live `project_turn_observation` output.

---

## Default Behavior Findings

| Field / Surface | Default | Risk | Recommendation |
|-----------------|---------|------|----------------|
| Most flat protected paths | `None` | Synthetic rows and sparse turns both show `None`; classifier cannot distinguish absent producer from intentional null without `unavailable` / presence metadata | Use `raw_signal_presence` + `unavailable` when diagnosing (CF2 tests lock distinction) |
| `final_text` | `""` | Empty prose is valid; distinguishes from missing key on synthetic rows | Keep; document that empty string ≠ unavailable |
| `scaffold_leakage` | `False` | Neutral default may hide “not evaluated” vs “evaluated clean” in synthetic-only rows | Classifier probes overlay explicit `False`; live projection always evaluates from text |
| `observed_projection_schema_defaults()` | All flat defaults + empty `trace` + `unavailable: []` | Baseline for synthetic rows; does not simulate sparse-turn unavailable | CF2 test locks empty unavailable on schema defaults |
| `synthetic_observed_replay_row(classifier_probe)` | Overlays route/speaker/FEM-like values | **High:** probe rows look “rich” while skipping canonical projection | CF2 test documents contrast vs sparse `project_turn_observation` |
| `protected_observation_default_row()` | 37× `None`, `final_text=""`, `scaffold_leakage=False` | Dashboard/classifier fixtures inherit neutral shape | Locked by 37 parametrized CF2 default tests + BL5 parity |

---

## Unavailable Behavior Findings

| Field / Container | Unavailable Trigger | Tested? | Risk |
|-------------------|---------------------|---------|------|
| `route_kind` | Projected value `None` | CF2 + BL3 | Low |
| `selected_speaker_id` | Projected value `None` | CF2 + BL3 | Low |
| `final_emitted_source` | Projected value `None` | CF2 + BL3 | Low |
| `response_type_required` | Projected value `None` | CF2 + BL3 | Low |
| `response_type_candidate_ok` | Projected value `None` | CF2 + BL3 | Low |
| `response_type_repair_used` | Projected value `None` | CF2 + BL3 | Low |
| `fallback_family` | Projected value `None` | CF2 + BL3 | Low |
| `trace.canonical_entry` | Empty trace container | CF2 + BL3 + AK5 | Low |
| `trace.turn_trace` | Empty trace container | CF2 + BL3 | Low |
| `trace.social_contract_trace` | Empty trace container | CF2 + BL3 | Low |
| All other protected fields | **Not** listed unavailable when `None` | CF2 sparse null test | Medium: `None` on observed turn ≠ unavailable for most FEM/sanitizer fields |
| Dotted trace leaves | Covered by parent prefix in `protected_path_covered_by_unavailable` | AK5 representation test | Low |

**Unavailable vs missing-source:** Unavailable is an explicit schema list (“field could not be represented”). Missing-source is a diagnostic map for classifier routing on fields with raw presence tracking only (7 flat keys + 3 trace containers + 5 supporting FEM delta keys).

---

## Raw vs Normalized Presence Findings

| Field group | Raw Signal | Normalized Signal | Projection Rule | Gap |
|-------------|------------|-------------------|-----------------|-----|
| FEM keys with `normalized_presence=True` (14 fields) | `_fem_has_any_key(fem, keys)` | `_fem_has_any_key(fem_normalized, keys)` | Both maps emitted on observed turn | Live `normalized_view_missing_raw_present` rare today; CF2 unit-tests routing function directly |
| `fallback_family` | dual-family key in raw FEM | dual-family key in normalized FEM | Same | Bridge inference uses raw FEM + lineage, not normalized |
| `route_kind`, `selected_speaker_id` | Custom raw predicates | not tracked | raw only | — |
| Trace containers | `bool(container)` | not tracked | Container keys in raw map | Leaf paths rely on container presence |
| Supporting delta keys | FEM key presence | normalized FEM key presence | Non-protected; classifier routing | — |
| Fields without `raw_presence` | not in map | not in map | No missing-source entry | Cannot distinguish raw absence via missing_source for sanitizer-only fields |

**Failure locality:** A failure in `missing_source_by_field` now localizes to `_missing_source_by_field_from_presence` (CF2 matrix test) or `_build_projection_status` (BL3 integration). Normalization gaps localize to `normalize_fem_for_replay_acceptance` / `test_final_emission_meta.py`.

---

## Tests Added

| File | Tests | What it locks |
|------|-------|---------------|
| `tests/helpers/protected_field_routing_contract.py` | (helper) | Programmatic 41-row routing matrix from registry + extraction specs |
| `tests/test_cf2_protected_field_routing.py` | 49 | Matrix coverage; per-path defaults; sparse unavailable set; null-vs-unavailable; missing-source routing; rich turn unavailable clearance; synthetic vs projected contrast |

Existing tests retained as integration owners: `test_ak5_*`, `test_bl2_*`, `test_bl3_*`, `test_bl5_*` in `test_golden_replay_projection.py`.

---

## Behavior Changes

**None.** All CF2 work is read-side contract documentation and tests. Sparse-turn unavailable list, defaults, and presence routing match pre-CF2 BL3 locks.

---

## Remaining Risks

1. **Synthetic classifier rows mask absence** — `_CLASSIFIER_PROBE_OVERLAY` supplies dialogue route, speaker, and FEM-like values without running projection; dashboard/classifier tests must not be treated as projection parity.

2. **`None` vs unavailable asymmetry** — Most FEM/sanitizer fields project `None` without entering `unavailable`; only seven flat fields + three trace containers use explicit unavailable marking. Readers must consult both the field value and `unavailable`.

3. **`normalized_view_missing_raw_present` under-exercised in integration** — Routing is locked at unit level; end-to-end normalization stripping scenarios remain thin.

4. **Contract helper vs extraction registry drift** — If `_PROTECTED_EXTRACTION_SPECS` changes without updating `_SOURCE_PATH_BY_EXTRACTION_SOURCE` in the contract helper, documentation strings may lag (registry parity tests catch path count; source descriptions are manual).

5. **Dotted trace paths have no flat defaults** — `observed_projection_schema_defaults()` supplies empty trace containers; leaves are absent until projection or overlay.

---

## Recommended Next Block

**Proceed with CF3 unchanged** (raw/normalized FEM field-family matrix per CF discovery), with these priorities:

1. Add one integration case that produces `normalized_view_missing_raw_present` through live FEM normalization if a realistic scenario exists in `normalize_final_emission_meta_for_observability`.
2. Extend the contract helper with `raw_presence` / `unavailable_key` / `normalized_presence` booleans exported from extraction specs (machine-readable) to eliminate manual doc duplication.
3. Do **not** collapse `None`-represented fields into unavailable without an explicit schema promotion — that would change drift semantics.

CF2 acceptance criteria met:

- [x] Every protected field has an explicit source/default/unavailable row
- [x] Every protected field has an identified owner test
- [x] Default vs unavailable vs missing-source behavior is distinguishable and tested
- [x] High-risk routing behavior has focused tests
- [x] Runtime behavior unchanged
- [x] CF3 can proceed without guessing routing policy
