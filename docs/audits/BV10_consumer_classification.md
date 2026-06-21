# BV10 — Read-Side Attribution Cluster Consumer Classification

**Date:** 2026-06-21
**Scope:** Group direct importers by maintenance subsystem.
**Source:** `artifacts/bv10_dependency_inventory.json` (71 import edges; 54 unique files).

## Classification overview

| Subsystem | Import edges | Primary modules touched | Migration eligible |
|---|---:|---|---|
| **Replay** | 9 | meta_read, bucket_views, schema | **High** (via replay adapter) |
| **Attribution** | 11 | bucket_views, schema | **High** (attribution read views) |
| **Fallback** | 12 | bucket_views, schema | Partial (write owners stay; tests migrate) |
| **Diagnostics** | 9 | meta_read | **High** (observability read facade) |
| **Observability** | 4 | meta_read, schema | **High** |
| **Tests** | 19 | meta_read, bucket_views | **High** (smoke / gate helpers) |
| **Speaker** | 1 | meta_read | Medium |
| **Other / authority** | 6 | all three | Low (meta write owner, owner suites) |

*Import-edge totals exceed unique files where one file imports multiple cluster modules.*

---

## Replay

**Import edges:** 9

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/final_emission_replay_projection.py` | `final_emission_meta_read` | `normalize_final_emission_meta_for_observability`, `read_emission_debug_lane_from_turn_payload`, `read_final_emission_meta_from_turn_payload` |
| `game/final_emission_replay_projection.py` | `owner_bucket_views` | `opening_fallback_owner_bucket_from_meta` |
| `game/final_emission_replay_projection.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER`, +16 more |
| `tests/helpers/replay_smoke_assertions.py` | `final_emission_meta_read` | `read_debug_notes_from_turn_payload`, `read_final_emission_meta_dict` |
| `tests/test_golden_replay_direct_seam.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_golden_replay_fallback_projection.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, `VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY` |
| `tests/test_golden_replay_fallback_projection.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, +11 more |
| `tests/test_golden_replay_projection.py` | `ownership_schema` | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_TRACE_SELECTION_OWNER_SHORT` |
| `tools/refresh_protected_replay_manifest.py` | `final_emission_meta_read` | `opening_fallback_metadata_field_registry_parity_errors` |

---

## Attribution

**Import edges:** 11

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `tests/failure_classification_contract.py` | `owner_bucket_views` | `OPENING_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_BUCKETS` |
| `tests/failure_classification_contract.py` | `ownership_schema` | `ALLOWED_FALLBACK_CONTENT_OWNERS`, `ALLOWED_FALLBACK_SELECTION_OWNERS` |
| `tests/helpers/failure_classification_sync.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE` |
| `tests/helpers/failure_classification_sync.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, +17 more |
| `tests/helpers/failure_classifier.py` | `owner_bucket_views` | `opening_fallback_owner_bucket_from_meta` |
| `tests/helpers/replacement_attribution_inventory.py` | `owner_bucket_views` | `opening_fallback_owner_bucket_from_meta`, `sealed_fallback_owner_bucket_from_fields`, `visibility_fallback_owner_bucket_from_fields` |
| `tests/test_failure_classification_contract.py` | `owner_bucket_views` | `OPENING_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_BUCKETS` |
| `tests/test_failure_classification_contract.py` | `ownership_schema` | `ALLOWED_FALLBACK_CONTENT_OWNERS`, `ALLOWED_FALLBACK_SELECTION_OWNERS`, `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, +4 more |
| `tests/test_failure_classifier.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE` |
| `tests/test_failure_classifier.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, +6 more |
| `tests/test_replacement_attribution_inventory.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, `VISIBILITY_FALLBACK_SELECTION_OWNER` |

---

## Fallback

**Import edges:** 12

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/final_emission_sealed_fallback.py` | `owner_bucket_views` | `sealed_fallback_owner_bucket_from_fields` |
| `game/final_emission_sealed_fallback.py` | `ownership_schema` | `SEALED_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `SEALED_FALLBACK_OWNER_UNKNOWN_NONE` |
| `game/final_emission_visibility_fallback.py` | `owner_bucket_views` | `visibility_fallback_owner_bucket_from_fields` |
| `game/final_emission_visibility_fallback.py` | `ownership_schema` | `VISIBILITY_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, `VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE` |
| `tests/helpers/opening_fallback_evidence.py` | `owner_bucket_views` | `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta` |
| `tests/test_final_emission_opening_fallback.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_final_emission_opening_fallback.py` | `owner_bucket_views` | `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED` |
| `tests/test_final_emission_sealed_fallback.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `SEALED_FALLBACK_OWNER_UNKNOWN_NONE` |
| `tests/test_final_emission_visibility_fallback.py` | `owner_bucket_views` | `VISIBILITY_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, `VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE`, +1 more |
| `tests/test_gm_retry.py` | `owner_bucket_views` | `OPENING_FALLBACK_OWNER_RETRY` |
| `tests/test_opening_fallback_owner_bucket.py` | `final_emission_meta_read` | `final_emission_meta_read_side_surface` |
| `tests/test_opening_fallback_owner_bucket.py` | `owner_bucket_views` | `OPENING_FALLBACK_OWNER_BUCKETS`, `OPENING_FALLBACK_OWNER_RETRY`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_STRICT_SOCIAL`, `OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, +9 more |

---

## Diagnostics

**Import edges:** 9

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/dead_turn_report_visibility.py` | `final_emission_meta_read` | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` |
| `game/narrative_authenticity_eval.py` | `final_emission_meta_read` | `NARRATIVE_AUTHENTICITY_FEM_KEYS`, `normalize_merged_na_telemetry_for_eval`, `normalized_observational_telemetry_bundle`, `read_final_emission_meta_from_turn_payload`, `summarize_gameplay_validation_for_turn` |
| `game/playability_eval.py` | `final_emission_meta_read` | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` |
| `game/stage_diff_telemetry.py` | `final_emission_meta_read` | `read_final_emission_meta_dict`, `stage_diff_narrative_authenticity_projection` |
| `tests/test_dead_turn_detection.py` | `final_emission_meta_read` | `classify_dead_turn`, `read_dead_turn_from_gm_output` |
| `tests/test_dead_turn_evaluation_threading.py` | `final_emission_meta_read` | `assemble_unified_observational_telemetry_bundle`, `read_final_emission_meta_dict` |
| `tests/test_observational_telemetry_confidence.py` | `final_emission_meta_read` | `assemble_unified_observational_telemetry_bundle`, `build_fem_observability_events`, `normalize_final_emission_meta_for_observability`, `stage_diff_narrative_authenticity_projection` |
| `tests/test_run_scenario_spine_validation.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tools/run_scenario_spine_validation.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |

---

## Observability

**Import edges:** 4

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/runtime_lineage_telemetry.py` | `ownership_schema` | `OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS`, `SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS` |
| `tests/helpers/behavioral_gauntlet_eval.py` | `final_emission_meta_read` | `read_dead_turn_from_gm_output`, `read_final_emission_meta_dict`, `summarize_gameplay_validation_for_turn` |
| `tests/test_runtime_lineage_telemetry.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED` |
| `tests/test_runtime_lineage_telemetry.py` | `ownership_schema` | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, `SEALED_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER`, +1 more |

---

## Speaker finalize

**Import edges:** 1

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/post_emission_speaker_adoption.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |

---

## Tests

**Import edges:** 19

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `tests/helpers/emission_smoke_assertions.py` | `final_emission_meta_read` | `read_debug_notes_from_turn_payload` |
| `tests/test_final_emission_acceptance_quality.py` | `final_emission_meta_read` | `FINAL_EMISSION_META_KEY` |
| `tests/test_final_emission_boundary_convergence.py` | `final_emission_meta_read` | `default_response_type_debug` |
| `tests/test_final_emission_channel_separation.py` | `final_emission_meta_read` | `read_debug_notes_from_turn_payload`, `read_emission_debug_lane`, `read_final_emission_meta_dict` |
| `tests/test_final_emission_gate_diagnostics.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_final_emission_gate_n4.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_final_emission_gate_orchestration_order.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_final_emission_gate_selector_snapshots.py` | `final_emission_meta_read` | `infer_accept_path_final_emitted_source`, `read_final_emission_meta_dict` |
| `tests/test_final_emission_gate_selector_snapshots.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED` |
| `tests/test_final_emission_meta.py` | `owner_bucket_views` | `opening_fallback_owner_bucket_from_meta` |
| `tests/test_final_emission_meta.py` | `ownership_schema` | `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_BUCKETS`, `OPENING_FALLBACK_OWNER_RETRY`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, +25 more |
| `tests/test_final_emission_narrative_mode_output.py` | `final_emission_meta_read` | `FINAL_EMISSION_META_KEY` |
| `tests/test_final_emission_opening_accept_debug.py` | `final_emission_meta_read` | `FINAL_EMISSION_META_KEY` |
| `tests/test_final_emission_visibility.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_final_emission_visibility.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE` |
| `tests/test_output_sanitizer.py` | `ownership_schema` | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_TRACE_SELECTION_OWNER_SHORT`, +1 more |
| `tests/test_tone_escalation_rules.py` | `final_emission_meta_read` | `default_response_type_debug`, `read_final_emission_meta_dict` |
| `tests/test_transcript_gauntlet_actor_addressing.py` | `final_emission_meta_read` | `read_final_emission_meta_dict` |
| `tests/test_validation_layer_separation_runtime.py` | `final_emission_meta_read` | `NARRATIVE_AUTHENTICITY_FEM_KEYS` |

---

## Authority / other

**Import edges:** 6

| Consumer | Module | Symbols / pattern |
|---|---|---|
| `game/final_emission_meta.py` | `owner_bucket_views` | `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta`, `visibility_fallback_owner_bucket_from_fields` |
| `game/final_emission_meta.py` | `ownership_schema` | `OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES`, `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_BUCKETS`, `OPENING_FALLBACK_OWNER_RETRY`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_STRICT_SOCIAL`, +17 more |
| `game/output_sanitizer.py` | `ownership_schema` | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_TRACE_SELECTION_OWNER_SHORT`, +4 more |
| `game/upstream_response_repairs.py` | `ownership_schema` | `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED` |
| `tests/helpers/failure_dashboard_fixtures.py` | `owner_bucket_views` | `SEALED_FALLBACK_OWNER_SEALED_GATE` |
| `tests/helpers/failure_dashboard_fixtures.py` | `ownership_schema` | `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD`, +8 more |

---

