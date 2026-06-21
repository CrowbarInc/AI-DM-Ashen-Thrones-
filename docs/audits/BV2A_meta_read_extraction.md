# BV2A — Meta Read Facade Extraction

**Date:** 2026-06-21  
**Phase:** BV2 Phase 1 execution (read facade + owner-bucket views)  
**Constraint:** No runtime behavior, schema, ownership authority, or write-path changes.

## Executive summary

BV2A introduced two read-side modules and migrated **15 consumers** off direct `game.final_emission_meta` imports. Measured fan-in on the canonical meta owner dropped from **61 → 47** (−14, **23%**), meeting the phase target (≈47).

Read traffic now flows through `game.final_emission_meta_read` (FI **15**). Owner-bucket mapper implementations moved to `game.final_emission_owner_bucket_views` with meta re-exports preserved for backward compatibility.

---

## Fan-in measurement

| Module | Pre-BV2A | Post-BV2A | Δ |
|---|---:|---:|---:|
| `game.final_emission_meta` | **61** | **47** | **−14** |
| `game.final_emission_meta_read` | — | **15** | +15 |
| `game.final_emission_owner_bucket_views` | — | **1** | +1 (meta re-import only) |

### Meta fan-in breakdown (post)

| Slice | Count |
|---|---:|
| Production | 24 |
| Tests | 19 |
| Helpers | 4 |

### Meta fan-out (post)

**7** — added `final_emission_owner_bucket_views`; other deps unchanged (`ownership_schema`, `replay_projection`, `validators`, `realization_provenance`, `state_channels`, `telemetry_vocab`).

**Method:** `scripts/bu_final_emission_coupling_discovery.py` (218-module ecosystem, 2026-06-21 post-migration scan).

---

## New modules

### `game/final_emission_meta_read.py`

Stable read-side facade delegating to canonical meta:

- Sidecar reads: `read_final_emission_meta_dict`, `read_final_emission_meta_from_turn_payload`, `read_emission_debug_lane*`, `read_debug_notes_from_turn_payload`
- Observability: `normalize_final_emission_meta_for_observability`, `build_fem_observability_events`, `assemble_unified_observational_telemetry_bundle`, `normalized_observational_telemetry_bundle`, `stage_diff_narrative_authenticity_projection`, `normalize_merged_na_telemetry_for_eval`
- Dead-turn read: `classify_dead_turn`, `read_dead_turn_from_gm_output`, `summarize_gameplay_validation_for_turn`
- Key registry: `NARRATIVE_AUTHENTICITY_FEM_KEYS`

### `game/final_emission_owner_bucket_views.py`

Read-only bucket mappers (implementations moved from meta):

- `opening_fallback_owner_bucket_from_fields`
- `opening_fallback_owner_bucket_from_meta`
- `visibility_fallback_owner_bucket_from_fields`
- `sealed_fallback_owner_bucket_from_fields`

Canonical bucket **definitions** remain on `game.final_emission_ownership_schema`. Meta **re-exports** all four mappers for existing import paths.

---

## Migrated consumers (15)

| File | Category | Symbols via `meta_read` |
|---|---|---|
| `game/dead_turn_report_visibility.py` | diagnostics | bundle + gameplay validation summary |
| `game/narrative_authenticity_eval.py` | diagnostics | NA keys, normalize, bundle, read_from_turn_payload |
| `game/playability_eval.py` | diagnostics | bundle + validation summary |
| `game/stage_diff_telemetry.py` | diagnostics | read_dict + stage-diff NA projection |
| `tests/helpers/emission_smoke_assertions.py` | helper | read_dict + debug_notes |
| `tests/helpers/behavioral_gauntlet_eval.py` | helper | read_dict + dead-turn read/summary |
| `tests/test_observational_telemetry_confidence.py` | observability | normalize, observability events, unified bundle |
| `tests/test_dead_turn_detection.py` | observability | classify + read dead-turn |
| `tests/test_dead_turn_evaluation_threading.py` | observability | unified bundle + read_dict |
| `tests/test_transcript_gauntlet_actor_addressing.py` | helper | read_dict |
| `tests/test_run_scenario_spine_validation.py` | diagnostics | read_dict (lazy) |
| `tools/run_scenario_spine_validation.py` | tooling | read_dict |
| `tests/test_final_emission_gate_diagnostics.py` | gate read smoke | read_dict |
| `tests/test_final_emission_gate_n4.py` | gate read smoke | read_dict |
| `tests/test_final_emission_gate_orchestration_order.py` | gate read smoke | read_dict |
| `tests/test_validation_layer_separation_runtime.py` | observability | `NARRATIVE_AUTHENTICITY_FEM_KEYS` (lazy) |

*Note: 16 rows — `test_run_scenario_spine_validation` lazy import counted; tools path outside BU ecosystem but migrated for consistency.*

---

## Intentionally not migrated (BV2A scope)

Per BV2A requirements — replay, fallback, and attribution paths deferred:

| Remaining direct meta importers (sample) | Reason deferred |
|---|---|
| `tests/helpers/golden_replay_projection.py` | Replay (BV2 Phase 2 C4) |
| `game/final_emission_replay_projection.py` | Replay |
| `tests/helpers/failure_classifier.py` | Attribution |
| `tests/helpers/replacement_attribution_inventory.py` | Attribution |
| `game/final_emission_visibility_fallback.py` | Fallback write owner |
| `game/final_emission_sealed_fallback.py` | Fallback write owner |
| `tests/test_opening_fallback_owner_bucket.py` | Fallback bucket owner suite |
| `tests/test_final_emission_meta.py` | Canonical FEM owner suite |
| `game/final_emission_finalize.py` | Write packaging |
| `tests/test_final_emission_channel_separation.py` | Mixed read + write (`package_emission_channel_sidecar`) |

**Remaining direct meta importers:** **47** (BU scan post-BV2A; pre-BV2A inventory in `artifacts/bv2_meta_dependency_inventory.json`).

---

## Test verification

| Suite | Result |
|---|---|
| `tests/test_final_emission_meta.py` | Pass |
| `tests/test_opening_fallback_owner_bucket.py` | Pass |
| `tests/test_observational_telemetry_confidence.py` | Pass |
| `tests/test_dead_turn_detection.py` | Pass |
| `tests/test_dead_turn_evaluation_threading.py` | Pass |
| `tests/test_transcript_gauntlet_actor_addressing.py` | Pass |
| `tests/test_final_emission_gate_diagnostics.py` | Pass |
| `tests/test_final_emission_gate_n4.py` | Pass |
| `tests/test_final_emission_gate_orchestration_order.py` | Pass |
| `tests/test_validation_layer_separation_runtime.py` | Pass |

No behavioral, output, replay, or ownership contract changes observed in affected suites.

---

## Projected next reduction (BV2A+ / Phase 2)

| Target | Est. FI reduction | Consumers |
|---|---:|---|
| Replay acceptance adapter (C4) | −3 | `golden_replay_projection`, `final_emission_replay_projection` |
| Attribution → bucket views (C1 remainder) | −4 | `failure_classifier`, `replacement_attribution_inventory`, `test_opening_fallback_owner_bucket` mappers |
| Fallback test bucket constants → schema/views | −6 | sealed/visibility/opening fallback test suites |
| Mixed gate tests (channel separation) | −1 | split read vs write imports |
| Speaker finalize read | −1 | `post_emission_speaker_adoption` |

**Projected meta FI after Phase 2:** **~29–32** (per [BV2_meta_consolidation_verification.md](BV2_meta_consolidation_verification.md)).

---

## Artifacts

| Path | Role |
|---|---|
| `game/final_emission_meta_read.py` | Read facade |
| `game/final_emission_owner_bucket_views.py` | Bucket view mappers |
| `artifacts/bv2_meta_fan_in_baseline.json` | Pre-BV2A baseline (FI=61) |
| [BV2_meta_consolidation_plan.md](BV2_meta_consolidation_plan.md) | Full phased plan |

---

## Command log

```bash
python scripts/bu_final_emission_coupling_discovery.py
python -m pytest tests/test_final_emission_meta.py tests/test_opening_fallback_owner_bucket.py \
  tests/test_observational_telemetry_confidence.py tests/test_dead_turn_detection.py \
  tests/test_dead_turn_evaluation_threading.py tests/test_final_emission_gate_orchestration_order.py -q
git checkout -- docs/audits/BU_*.csv  # restore CSV side effects after scan
```
