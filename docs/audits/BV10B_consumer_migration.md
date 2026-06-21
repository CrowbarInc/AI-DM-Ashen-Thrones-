# BV10B — Consumer Migration Inventory

**Date:** 2026-06-21
**Phase:** BV10 Phase 2 (attribution + observability consumer migration)
**Constraint:** Import retargeting only — no behavior, replay, or authority changes.

**Migrated files:** 32

| File | Old dependency | New dependency | Subsystem |
|---|---|---|---|
| `tests/failure_classification_contract.py` | ownership_schema + owner_bucket_views | attribution_read_views | attribution |
| `tests/helpers/failure_classification_sync.py` | ownership_schema + owner_bucket_views | attribution_read_views | attribution |
| `tests/helpers/failure_classifier.py` | owner_bucket_views | attribution_read_views | attribution |
| `tests/helpers/failure_dashboard_fixtures.py` | ownership_schema + owner_bucket_views | attribution_read_views | attribution |
| `tests/helpers/replacement_attribution_inventory.py` | owner_bucket_views | attribution_read_views | attribution |
| `tests/test_failure_classification_contract.py` | ownership_schema + owner_bucket_views | attribution_read_views | attribution |
| `tests/test_failure_classifier.py` | ownership_schema + owner_bucket_views | attribution_read_views | attribution |
| `tests/test_replacement_attribution_inventory.py` | ownership_schema | attribution_read_views | attribution |
| `tests/helpers/opening_fallback_evidence.py` | owner_bucket_views | attribution_read_views | fallback |
| `tests/test_gm_retry.py` | owner_bucket_views | attribution_read_views | fallback |
| `tests/test_final_emission_visibility.py` | owner_bucket_views | attribution_read_views | tests |
| `tests/test_final_emission_gate_selector_snapshots.py` | owner_bucket_views | attribution_read_views | tests |
| `tests/test_final_emission_opening_fallback.py` | owner_bucket_views | attribution_read_views | fallback |
| `tests/test_final_emission_visibility_fallback.py` | owner_bucket_views | attribution_read_views | fallback |
| `tests/test_final_emission_sealed_fallback.py` | owner_bucket_views | attribution_read_views | fallback |
| `tests/test_golden_replay_fallback_projection.py` | ownership_schema + owner_bucket_views | ownership_projection_views + attribution_read_views | replay |
| `tests/test_runtime_lineage_telemetry.py` | ownership_schema + owner_bucket_views | ownership_projection_views + attribution_read_views | replay |
| `tests/test_golden_replay_projection.py` | ownership_schema | ownership_projection_views | replay |
| `tests/test_output_sanitizer.py` | ownership_schema | ownership_projection_views | tests |
| `game/runtime_lineage_telemetry.py` | ownership_schema | ownership_projection_views | observability |
| `game/output_sanitizer.py` | ownership_schema | ownership_projection_views + attribution_read_views (bucket tokens) | final emission |
| `game/final_emission_replay_projection.py` | ownership_schema + owner_bucket_views + meta_read (lazy adapters) | ownership_projection_views + attribution_read_views + observability_attribution_read | replay |
| `game/upstream_response_repairs.py` | ownership_schema | attribution_read_views | final emission |
| `game/dead_turn_report_visibility.py` | final_emission_meta_read | observability_attribution_read | diagnostics |
| `game/playability_eval.py` | final_emission_meta_read | observability_attribution_read | diagnostics |
| `game/narrative_authenticity_eval.py` | final_emission_meta_read | observability_attribution_read | diagnostics |
| `game/stage_diff_telemetry.py` | meta_read (stage_diff half) | observability_attribution_read (+ meta_read for read_dict) | diagnostics |
| `tests/test_observational_telemetry_confidence.py` | final_emission_meta_read | observability_attribution_read | observability |
| `tests/test_dead_turn_detection.py` | final_emission_meta_read | observability_attribution_read | diagnostics |
| `tests/test_dead_turn_evaluation_threading.py` | meta_read (partial) | observability_attribution_read (+ meta_read for read_dict) | diagnostics |
| `tests/helpers/behavioral_gauntlet_eval.py` | meta_read (partial) | observability_attribution_read (+ meta_read for read_dict) | diagnostics |
| `tests/test_validation_layer_separation_runtime.py` | meta_read (lazy NA keys) | observability_attribution_read | observability |

## Intentionally not migrated

| File | Reason |
|---|---|
| `game/final_emission_meta.py` | FEM write owner |
| `game/final_emission_visibility_fallback.py` | Fallback write owner |
| `game/final_emission_sealed_fallback.py` | Fallback write owner |
| `tests/test_final_emission_meta.py` | FEM / schema owner suite |
| `tests/test_opening_fallback_owner_bucket.py` | Bucket owner suite |
| Gate/smoke `read_final_emission_meta_dict` consumers | Deferred to BV10C (C5) |
| `tools/*`, `tests/test_bv10a_read_facade_delegates.py` | Tooling / delegate verification |
