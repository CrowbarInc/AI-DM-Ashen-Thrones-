# BV2 — `final_emission_meta` Access Patterns

**Date:** 2026-06-21  
**Scope:** Repeated read-side and packaging patterns across 61 direct importers + 34 smoke-facade indirect consumers.

## Pattern summary

| Pattern ID | Description | Importer count | Example symbols | Consolidation target |
|---|---|---:|---|---|
| **P1** | Sidecar / dict read | 23 | `read_final_emission_meta_dict`, `read_final_emission_meta_from_turn_payload`, `read_emission_debug_lane*` | FEM read-access facade |
| **P2** | Owner-bucket lookup | 22 | `opening_fallback_owner_bucket_from_meta`, `*_from_fields`, bucket constants | Ownership views (`ownership_schema` + bucket mappers) |
| **P3** | Observability normalize/project | 9 | `normalize_final_emission_meta_for_observability`, `build_fem_observability_events`, `normalized_observational_telemetry_bundle` | Observability read module |
| **P4** | Write-or-create FEM dict | 11 | `ensure_final_emission_meta_dict`, `patch_final_emission_meta` | **Stay on meta** (write owner) |
| **P5** | Producer repair kind stamp | 10 | `stamp_producer_repair_kind`, `PRODUCER_REPAIR_KIND_*`, `apply_sanitizer_producer_attribution_to_fem` | **Stay on meta** (write owner) |
| **P6** | Layer merge packaging | 19 | `merge_narrative_*`, `merge_response_type_meta`, `default_*_layer_meta` | **Stay on meta** (write owner) |
| **P7** | Accept-path source inference | 4 | `infer_accept_path_final_emitted_source`, `response_type_decision_payload` | Terminal-pipeline narrow export |
| **P8** | Opening fallback projection | 7 | `apply_opening_fallback_projection_fields`, `OPENING_FALLBACK_RESULT_META_FIELDS`, context mirrors | **Stay on meta** (fallback write) |
| **P9** | Mutation lineage refresh | 3 | `refresh_final_emission_mutation_lineage`, `build_final_emission_mutation_lineage` | **Stay on meta** |
| **P10** | Registry / key constants | 15 | `FINAL_EMISSION_META_KEY`, `NARRATIVE_AUTHENTICITY_FEM_KEYS`, `FEM_*` | Read-side surface / schema split |

---

## P1 — Sidecar read (highest fan-out pattern)

**Repeated sequence:**

1. Obtain `gm_output` or API turn payload
2. Call `read_final_emission_meta_dict(gm_output)` **or** `read_final_emission_meta_from_turn_payload(payload)`
3. Assert on nested keys (`final_route`, `response_type_*`, fallback traces)

**Consumers:** `emission_smoke_assertions` (→ 34 indirect), gate orchestration tests (5), `stage_diff_telemetry`, `post_emission_speaker_adoption`, `gm_retry`, spine validation tool.

**Duplication:** Same legacy top-level vs `internal_state.emission_debug_lane` resolution logic centralized in meta; consumers only need **immutable read view**, not packaging helpers.

---

## P2 — Owner-bucket lookup (highest cross-subsystem pattern)

**Repeated sequence:**

1. Read FEM dict (P1)
2. Call `opening_fallback_owner_bucket_from_meta(meta)` **or** field-variant mappers
3. Compare to `OPENING_FALLBACK_OWNER_*` / `SEALED_*` / `VISIBILITY_*` constants

**Identical field reads:**

- `opening_fallback_owner_bucket`
- `opening_fallback_authorship_source`
- `realization_fallback_family` (via replay precedence, not meta directly)
- Sealed/visibility bucket fields on replacement paths

**Consumers:** `golden_replay_projection`, `failure_classifier`, `replacement_attribution_inventory`, `final_emission_replay_projection`, 6 fallback test suites, `test_opening_fallback_owner_bucket.py`.

**Duplication:** Constants imported from meta re-export `ownership_schema`; mappers are **read-side policy** duplicated across replay + attribution + tests.

---

## P3 — Observability normalize/project

**Repeated sequence:**

1. Raw FEM dict from fixture or gate output
2. `normalize_final_emission_meta_for_observability(fem)` — fills nested defaults deterministically
3. Optional: `build_fem_observability_events(normalized)` or `assemble_unified_observational_telemetry_bundle`

**Identical helper chain:** `test_observational_telemetry_confidence.py` mirrors production `narrative_authenticity_eval` + `playability_eval` bundle assembly.

**Consumers:** 4 production diagnostics modules + 3 test modules.

---

## P4–P6 — Write packaging (legitimate meta ownership)

These patterns **should not migrate off meta** without explicit write-owner redesign:

| Pattern | Typical call chain | Primary owners |
|---|---|---|
| P4 ensure/patch | `ensure_final_emission_meta_dict` → mutate → `patch_final_emission_meta` | visibility, terminal, acceptance, NMO |
| P5 producer stamp | visibility/sealed/terminal `stamp_producer_repair_kind` | fallback routers, terminal pipeline |
| P6 layer merge | `default_*_layer_meta` → repair → `merge_*_into_final_emission_meta` | repairs, fem_assembly, preflight |

**Risk if migrated prematurely:** Splitting write paths creates dual-owner FEM shape drift (BK/BU governance regression).

---

## P7 — Accept-path projection

**Repeated reads:** Layer repair telemetry keys (`response_type_debug`, `*_layer_meta`) consumed by `infer_accept_path_final_emitted_source`.

**Consumers:** `strict_social_stack`, `generic_exit`, `test_final_emission_gate_selector_snapshots`.

**Note:** Same layer-key vocabulary read in P6 write path; inference is **read-side projection** over write-produced telemetry.

---

## P8 — Opening fallback projection

**Repeated sequence:**

1. `default_opening_fallback_fail_closed_result_meta()` or context mirrors
2. `apply_opening_fallback_projection_fields(meta, ...)`
3. `stamp_opening_fallback_owner_bucket(meta)`

**Consumers:** opening fallback chain (production) + opening fallback tests.

---

## P10 — Constants-only imports

Files importing **only** `FINAL_EMISSION_META_KEY` or bucket constants without calling functions:

- `test_final_emission_acceptance_quality.py`, `test_final_emission_narrative_mode_output.py`, `test_final_emission_opening_accept_debug.py`
- `output_sanitizer.py` (producer kind strings)

**Lowest-risk migration:** Re-point to `final_emission_ownership_schema` or `final_emission_meta_read_side_surface()` dict.

---

## Anti-patterns (consolidation opportunities)

| Anti-pattern | Evidence | Remedy |
|---|---|---|
| Test helpers import 12 meta symbols when replay projection owns lineage | `golden_replay_projection.py` | Replay acceptance adapter on `final_emission_replay_projection` |
| Bucket constants via meta instead of schema | 11 importers | Direct `ownership_schema` import |
| Gate tests bypass smoke facade but duplicate read_dict | 5 gate tests | Unified `fem_read` test helper |
| Meta re-exports `build_fem_runtime_lineage_events` | meta L1999 | Consumers use `replay_projection` only (already documented; meta import redundant) |

---

## Evidence

| Source | Path |
|---|---|
| Symbol frequency scan | BV2 analysis pass on 61 importers |
| AS4/AS5 migration notes | `docs/cycles/cycle_as_block_as4_implementation_summary.md` |
| AO5 replay boundary | `tests/helpers/golden_replay_projection.py` docstring |
