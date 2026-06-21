# BV10 — Read-Side Attribution Cluster Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only. Direct importers of the three-module read-side attribution cluster.
**Method:** AST scan (`tools/bv10_read_cluster_discovery.py`) + BU ecosystem fan-in (`docs/audits/BU_import_fan_in_fan_out.csv`).

## Cluster baseline (current)

| Module | BU fan-in | FO | Ownership concentration | BV9 rank |
|---|---:|---:|---:|---:|
| `game.final_emission_meta_read` | **29** | 1 | 0.0024 | #6 |
| `game.final_emission_owner_bucket_views` | **22** | 1 | 0.2206 | #14 |
| `game.final_emission_ownership_schema` | **19** | 1 | 0.4173 | #15 |
| **Combined (sum of module FI)** | **70** | 3 | — | largest unaddressed read cluster |

**Unique importers (deduped across cluster):** 54 files import at least one target.
**Multi-import overlap:** 16 files import two or three targets (see hub analysis).

**BV2 context:** Write-side `final_emission_meta` reduced 61 → 22; read facades absorbed deferred BV2 consumers (+11 meta_read, +17 bucket_views FI post-BV2B).

---

## `final_emission_meta_read` — 29 BU fan-in (31 AST importers)

| File | Subsystem | Imported symbols | Ownership bucket | Read frequency |
|---|---|---|---|---|
| `game/dead_turn_report_visibility.py` | diagnostics | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` | observability-projection | Medium |
| `game/final_emission_replay_projection.py` | replay | `normalize_final_emission_meta_for_observability`, `read_emission_debug_lane_from_turn_payload`, `read_final_emission_meta_from_turn_payload` | observability-projection | Low |
| `game/narrative_authenticity_eval.py` | diagnostics | `NARRATIVE_AUTHENTICITY_FEM_KEYS`, `normalize_merged_na_telemetry_for_eval`, `normalized_observational_telemetry_bundle`, `read_final_emission_meta_from_turn_payload`, +1 more | read-side-access | High |
| `game/playability_eval.py` | diagnostics | `normalized_observational_telemetry_bundle`, `summarize_gameplay_validation_for_turn` | observability-projection | Medium |
| `game/post_emission_speaker_adoption.py` | speaker | `read_final_emission_meta_dict` | read-side-access | Low |
| `game/stage_diff_telemetry.py` | diagnostics | `read_final_emission_meta_dict`, `stage_diff_narrative_authenticity_projection` | read-side-access | Medium |
| `tests/helpers/behavioral_gauntlet_eval.py` | other | `read_dead_turn_from_gm_output`, `read_final_emission_meta_dict`, `summarize_gameplay_validation_for_turn` | observability-projection | Medium |
| `tests/helpers/emission_smoke_assertions.py` | tests | `read_debug_notes_from_turn_payload` | read-side-access | Import-only |
| `tests/helpers/replay_smoke_assertions.py` | replay | `read_debug_notes_from_turn_payload`, `read_final_emission_meta_dict` | read-side-access | Medium |
| `tests/test_dead_turn_detection.py` | diagnostics | `classify_dead_turn`, `read_dead_turn_from_gm_output` | observability-projection | Medium |
| `tests/test_dead_turn_evaluation_threading.py` | diagnostics | `assemble_unified_observational_telemetry_bundle`, `read_final_emission_meta_dict` | observability-projection | Low |
| `tests/test_final_emission_acceptance_quality.py` | tests | `FINAL_EMISSION_META_KEY` | read-side-access | Import-only |
| `tests/test_final_emission_boundary_convergence.py` | tests | `default_response_type_debug` | layer-projection | Low |
| `tests/test_final_emission_channel_separation.py` | tests | `read_debug_notes_from_turn_payload`, `read_emission_debug_lane`, `read_final_emission_meta_dict` | read-side-access | Medium |
| `tests/test_final_emission_gate_diagnostics.py` | tests | `read_final_emission_meta_dict` | read-side-access | Medium |
| `tests/test_final_emission_gate_n4.py` | tests | `read_final_emission_meta_dict` | read-side-access | Medium |
| `tests/test_final_emission_gate_orchestration_order.py` | tests | `read_final_emission_meta_dict` | read-side-access | High |
| `tests/test_final_emission_gate_selector_snapshots.py` | tests | `infer_accept_path_final_emitted_source`, `read_final_emission_meta_dict` | read-side-access | Import-only |
| `tests/test_final_emission_narrative_mode_output.py` | tests | `FINAL_EMISSION_META_KEY` | read-side-access | Import-only |
| `tests/test_final_emission_opening_accept_debug.py` | tests | `FINAL_EMISSION_META_KEY` | read-side-access | Import-only |
| `tests/test_final_emission_opening_fallback.py` | fallback | `read_final_emission_meta_dict` | read-side-access | High |
| `tests/test_final_emission_visibility.py` | tests | `read_final_emission_meta_dict` | read-side-access | High |
| `tests/test_golden_replay_direct_seam.py` | replay | `read_final_emission_meta_dict` | read-side-access | Low |
| `tests/test_observational_telemetry_confidence.py` | diagnostics | `assemble_unified_observational_telemetry_bundle`, `build_fem_observability_events`, `normalize_final_emission_meta_for_observability`, `stage_diff_narrative_authenticity_projection` | observability-projection | High |
| `tests/test_opening_fallback_owner_bucket.py` | fallback | `final_emission_meta_read_side_surface` | read-side-access | Medium |
| `tests/test_run_scenario_spine_validation.py` | diagnostics | `read_final_emission_meta_dict` | read-side-access | Medium |
| `tests/test_tone_escalation_rules.py` | tests | `default_response_type_debug`, `read_final_emission_meta_dict` | layer-projection | Medium |
| `tests/test_transcript_gauntlet_actor_addressing.py` | tests | `read_final_emission_meta_dict` | read-side-access | Low |
| `tests/test_validation_layer_separation_runtime.py` | tests | `NARRATIVE_AUTHENTICITY_FEM_KEYS` | layer-projection | Import-only |
| `tools/refresh_protected_replay_manifest.py` | replay | `opening_fallback_metadata_field_registry_parity_errors` | read-side-access | Low |
| `tools/run_scenario_spine_validation.py` | diagnostics | `read_final_emission_meta_dict` | read-side-access | Low |

---

## `owner_bucket_views` — 22 BU fan-in (22 AST importers)

| File | Subsystem | Imported symbols | Ownership bucket | Read frequency |
|---|---|---|---|---|
| `game/final_emission_meta.py` | other | `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta`, `visibility_fallback_owner_bucket_from_fields` | owner-bucket-projection | Medium |
| `game/final_emission_replay_projection.py` | replay | `opening_fallback_owner_bucket_from_meta` | owner-bucket-projection | Medium |
| `game/final_emission_sealed_fallback.py` | fallback | `sealed_fallback_owner_bucket_from_fields` | owner-bucket-projection | Medium |
| `game/final_emission_visibility_fallback.py` | fallback | `visibility_fallback_owner_bucket_from_fields` | owner-bucket-projection | Medium |
| `tests/failure_classification_contract.py` | attribution | `OPENING_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_BUCKETS` | schema-vocabulary | Import-only |
| `tests/helpers/failure_classification_sync.py` | attribution | `SEALED_FALLBACK_OWNER_SEALED_GATE` | schema-vocabulary | Import-only |
| `tests/helpers/failure_classifier.py` | attribution | `opening_fallback_owner_bucket_from_meta` | owner-bucket-projection | Low |
| `tests/helpers/failure_dashboard_fixtures.py` | other | `SEALED_FALLBACK_OWNER_SEALED_GATE` | schema-vocabulary | Import-only |
| `tests/helpers/opening_fallback_evidence.py` | fallback | `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, +2 more | owner-bucket-projection | Medium |
| `tests/helpers/replacement_attribution_inventory.py` | attribution | `opening_fallback_owner_bucket_from_meta`, `sealed_fallback_owner_bucket_from_fields`, `visibility_fallback_owner_bucket_from_fields` | owner-bucket-projection | Medium |
| `tests/test_failure_classification_contract.py` | attribution | `OPENING_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_BUCKETS` | schema-vocabulary | Import-only |
| `tests/test_failure_classifier.py` | attribution | `SEALED_FALLBACK_OWNER_SEALED_GATE` | schema-vocabulary | Import-only |
| `tests/test_final_emission_gate_selector_snapshots.py` | tests | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED` | schema-vocabulary | Import-only |
| `tests/test_final_emission_meta.py` | tests | `opening_fallback_owner_bucket_from_meta` | owner-bucket-projection | Medium |
| `tests/test_final_emission_opening_fallback.py` | fallback | `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED` | schema-vocabulary | Import-only |
| `tests/test_final_emission_sealed_fallback.py` | fallback | `SEALED_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, +1 more | schema-vocabulary | Import-only |
| `tests/test_final_emission_visibility.py` | tests | `SEALED_FALLBACK_OWNER_SEALED_GATE` | schema-vocabulary | Import-only |
| `tests/test_final_emission_visibility_fallback.py` | fallback | `VISIBILITY_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, `VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY`, +3 more | owner-bucket-projection | Low |
| `tests/test_gm_retry.py` | fallback | `OPENING_FALLBACK_OWNER_RETRY` | schema-vocabulary | Import-only |
| `tests/test_golden_replay_fallback_projection.py` | replay | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, +1 more | schema-vocabulary | Import-only |
| `tests/test_opening_fallback_owner_bucket.py` | fallback | `OPENING_FALLBACK_OWNER_BUCKETS`, `OPENING_FALLBACK_OWNER_RETRY`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_STRICT_SOCIAL`, +11 more | owner-bucket-projection | Medium |
| `tests/test_runtime_lineage_telemetry.py` | tests | `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED` | schema-vocabulary | Import-only |

---

## `ownership_schema` — 19 BU fan-in (18 AST importers)

| File | Subsystem | Imported symbols | Ownership bucket | Read frequency |
|---|---|---|---|---|
| `game/final_emission_meta.py` | other | `OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES`, `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_BUCKETS`, `OPENING_FALLBACK_OWNER_RETRY`, +19 more | owner-bucket-projection | Low |
| `game/final_emission_replay_projection.py` | replay | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_FALLBACK_SELECTION_OWNER`, +18 more | schema-vocabulary | Low |
| `game/final_emission_sealed_fallback.py` | fallback | `SEALED_FALLBACK_OWNER_BUCKETS`, `SEALED_FALLBACK_OWNER_SEALED_GATE`, `SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED`, `SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS`, +1 more | schema-vocabulary | Import-only |
| `game/final_emission_visibility_fallback.py` | fallback | `VISIBILITY_FALLBACK_OWNER_BUCKETS`, `VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY`, `VISIBILITY_FALLBACK_OWNER_SEALED_GATE`, `VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY`, +2 more | schema-vocabulary | Import-only |
| `game/output_sanitizer.py` | other | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD`, +6 more | schema-vocabulary | Medium |
| `game/runtime_lineage_telemetry.py` | observability | `OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS`, `SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS` | attribution-vocabulary | Import-only |
| `game/upstream_response_repairs.py` | other | `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED` | attribution-vocabulary | Import-only |
| `tests/failure_classification_contract.py` | attribution | `ALLOWED_FALLBACK_CONTENT_OWNERS`, `ALLOWED_FALLBACK_SELECTION_OWNERS` | schema-vocabulary | Import-only |
| `tests/helpers/failure_classification_sync.py` | attribution | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_OWNER_SEALED_GATE`, `OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED`, +19 more | schema-vocabulary | Import-only |
| `tests/helpers/failure_dashboard_fixtures.py` | other | `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, +10 more | attribution-vocabulary | Import-only |
| `tests/test_failure_classification_contract.py` | attribution | `ALLOWED_FALLBACK_CONTENT_OWNERS`, `ALLOWED_FALLBACK_SELECTION_OWNERS`, `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, +6 more | schema-vocabulary | Import-only |
| `tests/test_failure_classifier.py` | attribution | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_FALLBACK_SELECTION_OWNER`, +8 more | attribution-vocabulary | Import-only |
| `tests/test_final_emission_meta.py` | tests | `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`, `OPENING_FALLBACK_OWNER_BUCKETS`, +27 more | schema-vocabulary | Import-only |
| `tests/test_golden_replay_fallback_projection.py` | replay | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, +13 more | attribution-vocabulary | Import-only |
| `tests/test_golden_replay_projection.py` | replay | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_TRACE_SELECTION_OWNER_SHORT` | attribution-vocabulary | Import-only |
| `tests/test_output_sanitizer.py` | tests | `SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD`, `SANITIZER_FALLBACK_SELECTION_OWNER`, `SANITIZER_STRICT_SOCIAL_CONTENT_OWNER`, `SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD`, +3 more | attribution-vocabulary | Import-only |
| `tests/test_replacement_attribution_inventory.py` | attribution | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, +1 more | schema-vocabulary | Import-only |
| `tests/test_runtime_lineage_telemetry.py` | tests | `OPENING_FAIL_CLOSED_CONTENT_OWNER`, `OPENING_FALLBACK_CONTENT_OWNER`, `OPENING_FALLBACK_SELECTION_OWNER`, `SEALED_FALLBACK_MODULE_CONTENT_OWNER`, +3 more | schema-vocabulary | Import-only |

---

## Evidence

| Artifact | Path |
|---|---|
| Machine inventory | `artifacts/bv10_dependency_inventory.json` |
| Discovery script | `tools/bv10_read_cluster_discovery.py` |
| BU fan-in/fan-out | `docs/audits/BU_import_fan_in_fan_out.csv` |
| BV9 concentration | `docs/audits/BV9_concentration_rankings.md` |
