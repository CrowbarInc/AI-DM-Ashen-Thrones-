# BV2 — `final_emission_meta` Dependency Inventory

**Date:** 2026-06-21  
**Scope:** Analysis only. Maps every direct importer of `game.final_emission_meta`.  
**Method:** Fresh BU AST scan (`scripts/bu_final_emission_coupling_discovery.py`) + per-file symbol extraction (`artifacts/bv2_meta_dependency_inventory.json`).

## Hub baseline (current)

| Metric | Value | Source |
|---|---:|---|
| Fan-in (total) | **61** | `docs/audits/BU_import_fan_in_fan_out.csv` |
| Fan-in (production) | **27** | same |
| Fan-in (tests) | **28** | same |
| Fan-in (helpers) | **6** | same |
| Fan-out | **6** | `ownership_schema`, `replay_projection`, `validators`, `realization_provenance`, `state_channels`, `telemetry_vocab` |
| Ownership refs (lexical) | **134–175** | BV1 / BU ownership map |
| Module LOC | **~2,264** | `game/final_emission_meta.py` |
| Indirect read consumers | **34+** | via `tests.helpers.emission_smoke_assertions.final_emission_meta_from_output` (no direct meta import) |

**BV1C rank:** #2 ecosystem fan-in hub (after `emission_smoke_assertions` 70 FI); #1 **production** read-side schema hub.

---

## Importer summary by subsystem

| Subsystem | Direct importers | Primary access mode |
|---|---:|---|
| Fallback | 14 | Owner-bucket stamps, projection fields, producer repair kinds |
| Tests (owner + gate suites) | 14 | Constants, read helpers, bucket parity |
| Final emission (write/merge) | 10 | `ensure_*`, layer merges, defaults |
| Diagnostics | 9 | Observability bundles, dead-turn classification |
| Terminal pipeline | 9 | Packaging, producer stamps, accept-path projection |
| Replay | 2 | Owner-bucket from meta, normalize for acceptance |
| Attribution | 2 | Bucket mappers for classifier/inventory |
| Speaker finalize | 1 | `read_final_emission_meta_dict` |

---

## Production importers (27)

| File | Subsystem | Imported symbols (summary) | Read frequency | Ownership bucket |
|---|---|---|---|---|
| `game/dead_turn_report_visibility.py` | diagnostics | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` | Low (bundle assembly) | observability-projection |
| `game/fallback_provenance_debug.py` | fallback | Fast-fallback provenance keys, `patch_final_emission_meta` | Write-on-debug | write-packaging |
| `game/final_emission_acceptance_quality.py` | final emission | `ensure_final_emission_meta_dict` | Per accept-path write | write-packaging |
| `game/final_emission_fem_assembly.py` | final emission | `merge_narrative_authenticity_into_final_emission_meta`, `merge_response_type_meta` | Per assembly write | layer-merge-packaging |
| `game/final_emission_finalize.py` | terminal pipeline | `ensure_*`, `package_*`, `patch_*`, `refresh_*`, `apply_sanitizer_producer_attribution_to_fem` | Every finalize | producer-attribution |
| `game/final_emission_gate_preflight_defaults.py` | final emission | `default_narrative_authenticity_layer_meta`, `default_response_type_debug` | Preflight init | layer-merge-packaging |
| `game/final_emission_generic_exit.py` | terminal pipeline | `FINAL_EMISSION_META_KEY`, opening projection, `infer_accept_path_final_emitted_source`, `response_type_decision_payload` | Every generic exit | write-packaging |
| `game/final_emission_narration_constraint_debug.py` | final emission | `build_narration_constraint_debug`, `merge_narration_constraint_debug_meta` | Debug path write | layer-merge-packaging |
| `game/final_emission_narrative_mode_output.py` | final emission | `ensure_*`, `merge_narrative_mode_output_into_final_emission_meta` | NMO merge write | write-packaging |
| `game/final_emission_opening_fallback.py` | fallback | `OPENING_FALLBACK_RESULT_META_FIELDS`, fail-closed defaults, `stamp_opening_fallback_owner_bucket` | Fallback write | opening-fallback-owner |
| `game/final_emission_repairs.py` | final emission | NA trace build/merge, `stamp_producer_repair_kind` | Repair write | producer-attribution |
| `game/final_emission_replay_projection.py` | replay | `opening_fallback_owner_bucket_from_meta` (lazy) | Lineage projection read | opening-fallback-owner |
| `game/final_emission_response_type.py` | final emission | `_default_response_type_debug`, `stamp_opening_fallback_owner_bucket` | RT write | opening-fallback-owner |
| `game/final_emission_sealed_fallback.py` | fallback | `refresh_final_emission_mutation_lineage`, `sealed_fallback_owner_bucket_from_fields` | Sealed path | sealed-fallback-owner |
| `game/final_emission_strict_social_stack.py` | terminal pipeline | `FINAL_EMISSION_META_KEY`, `infer_accept_path_final_emitted_source`, `stamp_producer_repair_kind` | Strict accept write | producer-attribution |
| `game/final_emission_terminal_pipeline.py` | terminal pipeline | `ensure_*`, `stamp_producer_repair_kind`, strict-social producer kind | Terminal enforcement | producer-attribution |
| `game/final_emission_visibility_fallback.py` | fallback | Visibility producer kinds (×4), `stamp_*`, `visibility_fallback_owner_bucket_from_fields` | Visibility repair write | visibility-fallback-owner |
| `game/gm_retry.py` | fallback | `read_final_emission_meta_dict`, `stamp_retry_terminal_fallback_producer_metadata` | Read + retry stamp | read-side + producer |
| `game/interaction_continuity.py` | final emission | `ensure_final_emission_meta_dict` (lazy) | Continuity write | write-packaging |
| `game/narrative_authenticity.py` | final emission | `build_narrative_authenticity_emission_trace` | NA packaging | layer-merge-packaging |
| `game/narrative_authenticity_eval.py` | diagnostics | `NARRATIVE_AUTHENTICITY_FEM_KEYS`, normalize bundle, `read_final_emission_meta_from_turn_payload` | Evaluator read | observability-projection |
| `game/opening_deterministic_fallback.py` | fallback | `default_opening_fallback_context_mirror_values` | Opening mirror defaults | opening-fallback-owner |
| `game/output_sanitizer.py` | final emission | `PRODUCER_REPAIR_KIND_*` sanitizer tokens | Sanitizer stamp | producer-attribution |
| `game/playability_eval.py` | diagnostics | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` | Playability read | observability-projection |
| `game/post_emission_speaker_adoption.py` | speaker finalize | `read_final_emission_meta_dict` | Post-speaker read | read-side-access |
| `game/stage_diff_telemetry.py` | diagnostics | `read_final_emission_meta_dict`, `stage_diff_narrative_authenticity_projection` | Stage-diff read | read-side-access |
| `game/upstream_response_repairs.py` | fallback | `stamp_upstream_prepared_opening_producer_metadata` (lazy) | Upstream opening stamp | opening-fallback-owner |

---

## Test and helper importers (34)

| File | Subsystem | Symbol count | Ownership bucket |
|---|---|---:|---|
| `tests/helpers/behavioral_gauntlet_eval.py` | diagnostics | 3 | read-side-access |
| `tests/helpers/emission_smoke_assertions.py` | tests | 2 | read-side-access |
| `tests/helpers/failure_classifier.py` | attribution | 1 | opening-fallback-owner |
| `tests/helpers/golden_replay_projection.py` | replay | 12 | opening + sealed + visibility buckets, normalize, read_from_turn_payload |
| `tests/helpers/opening_fallback_evidence.py` | fallback | 6 | opening-fallback-owner |
| `tests/helpers/replacement_attribution_inventory.py` | attribution | 3 | all three bucket mappers |
| `tests/test_dead_turn_detection.py` | diagnostics | 2 | observability-projection |
| `tests/test_dead_turn_evaluation_threading.py` | diagnostics | 2 | read-side-access |
| `tests/test_final_emission_acceptance_quality.py` | tests | 1 | write-packaging |
| `tests/test_final_emission_boundary_convergence.py` | tests | 1 | layer-merge |
| `tests/test_final_emission_channel_separation.py` | terminal pipeline | 4 | read-side-access |
| `tests/test_final_emission_gate_diagnostics.py` | terminal pipeline | 1 | read-side-access |
| `tests/test_final_emission_gate_n4.py` | terminal pipeline | 1 | read-side-access |
| `tests/test_final_emission_gate_orchestration_order.py` | terminal pipeline | 1 | read-side-access |
| `tests/test_final_emission_gate_selector_snapshots.py` | terminal pipeline | 4 | layer-merge + read |
| `tests/test_final_emission_meta.py` | tests | 65+ | **owner suite** — full surface |
| `tests/test_final_emission_narration_constraint_debug.py` | tests | 2 | layer-merge |
| `tests/test_final_emission_narrative_mode_output.py` | tests | 1 | write-packaging |
| `tests/test_final_emission_opening_accept_debug.py` | tests | 1 | write-packaging |
| `tests/test_final_emission_opening_fallback.py` | fallback | 3 | opening-fallback-owner |
| `tests/test_final_emission_sealed_fallback.py` | fallback | 5 | sealed-fallback-owner |
| `tests/test_final_emission_visibility.py` | fallback | 2 | read + sealed constant |
| `tests/test_final_emission_visibility_fallback.py` | fallback | 7 | visibility-fallback-owner |
| `tests/test_gm_retry.py` | fallback | 1 | opening-fallback-owner |
| `tests/test_golden_replay_direct_seam.py` | replay | 1 | read-side-access |
| `tests/test_narrative_mode_output_validator.py` | tests | 3 | layer-merge |
| `tests/test_observational_telemetry_confidence.py` | diagnostics | 4 | observability-projection |
| `tests/test_opening_fallback_owner_bucket.py` | attribution | 16 | **bucket parity owner suite** |
| `tests/test_ownership_registry.py` | tests | module | governance static scan |
| `tests/test_run_scenario_spine_validation.py` | diagnostics | 1 | read-side-access |
| `tests/test_tone_escalation_rules.py` | tests | 2 | layer-merge + read |
| `tests/test_transcript_gauntlet_actor_addressing.py` | tests | 1 | read-side-access |
| `tests/test_upstream_response_repairs.py` | fallback | 1 | opening-fallback-owner |
| `tests/test_validation_layer_separation_runtime.py` | tests | 1 | layer-merge |

**Tools note:** `tools/run_scenario_spine_validation.py` imports `read_final_emission_meta_dict` but is outside the BU 216-module ecosystem count; documented as tooling read-side consumer.

---

## Indirect dependency (smoke facade)

34 test files call `final_emission_meta_from_output()` in `tests/helpers/emission_smoke_assertions.py`, which delegates to `read_final_emission_meta_dict`. These **do not** increment meta fan-in but **do** concentrate read-side behavior behind a single helper (70 FI on the facade vs 2 FI direct meta import from smoke module).

---

## Fan-out detail (meta imports)

| Imported module | Role |
|---|---|
| `game.final_emission_ownership_schema` | Canonical owner-bucket string constants (re-exported through meta today) |
| `game.final_emission_replay_projection` | `build_fem_runtime_lineage_events` compatibility re-export |
| `game.final_emission_validators` | Response-type debug merge delegates |
| `game.realization_provenance` | Provenance field vocabulary (via validators/lineage path) |
| `game.state_channels` | Debug payload projection |
| `game.telemetry_vocab` | Observability event envelope |

---

## Evidence

| Artifact | Path |
|---|---|
| Machine inventory | `artifacts/bv2_meta_dependency_inventory.json` |
| BU fan-in/fan-out | `docs/audits/BU_import_fan_in_fan_out.csv` |
| BV1C hub rank | `docs/audits/BV1C_hub_migration_analysis.md` |
| Module owner docstring | `game/final_emission_meta.py` L1–28 |
