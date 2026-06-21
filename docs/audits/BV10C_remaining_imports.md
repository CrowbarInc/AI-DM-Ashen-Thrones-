# BV10C — Remaining Read-Cluster Authority Imports

**Date:** 2026-06-21
**Phase:** BV10C (replay adapter completion + governance lock)
**Constraint:** Import retargeting only — no runtime, replay, or ownership-authority changes.

## Summary

| Authority cluster FI (BU CSV) | **19** |
| BV10B baseline | **39** (24 + 7 + 8) |
| BV10C target | **31–35** |
| Met | **✓** |

## `final_emission_meta_read` — FI **4** (5 AST importers incl. tools)

| File | Classification | Symbols |
|---|---|---|
| `game/observability_attribution_read.py` | migration candidate | FINAL_EMISSION_META_KEY, NARRATIVE_AUTHENTICITY_FEM_KEYS, assemble_unified_observational_telemetry_bundle, build_fem_observability_events, classify_dead_turn, default_response_type_debug, … |
| `tests/helpers/replay_smoke_assertions.py` | compatibility (smoke facade) | read_debug_notes_from_turn_payload, read_final_emission_meta_dict |
| `tests/test_opening_fallback_owner_bucket.py` | owner suite | final_emission_meta_read_side_surface |
| `tools/refresh_protected_replay_manifest.py` | compatibility (tooling) | opening_fallback_metadata_field_registry_parity_errors |
| `tools/run_scenario_spine_validation.py` | compatibility (tooling) | read_final_emission_meta_dict |

## `final_emission_owner_bucket_views` — FI **7** (6 AST importers incl. tools)

| File | Classification | Symbols |
|---|---|---|
| `game/attribution_read_views.py` | migration candidate | OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES, OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES, OPENING_FALLBACK_OWNER_BUCKETS, OPENING_FALLBACK_OWNER_RETRY, OPENING_FALLBACK_OWNER_SEALED_GATE, OPENING_FALLBACK_OWNER_STRICT_SOCIAL, … |
| `game/final_emission_meta.py` | authority owner | opening_fallback_owner_bucket_from_fields, opening_fallback_owner_bucket_from_meta, visibility_fallback_owner_bucket_from_fields |
| `game/final_emission_sealed_fallback.py` | migration candidate | sealed_fallback_owner_bucket_from_fields |
| `game/final_emission_visibility_fallback.py` | migration candidate | visibility_fallback_owner_bucket_from_fields |
| `tests/test_final_emission_meta.py` | owner suite | opening_fallback_owner_bucket_from_meta |
| `tests/test_opening_fallback_owner_bucket.py` | owner suite | OPENING_FALLBACK_OWNER_BUCKETS, OPENING_FALLBACK_OWNER_RETRY, OPENING_FALLBACK_OWNER_SEALED_GATE, OPENING_FALLBACK_OWNER_STRICT_SOCIAL, OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, … |

## `final_emission_ownership_schema` — FI **8** (6 AST importers incl. tools)

| File | Classification | Symbols |
|---|---|---|
| `game/attribution_read_views.py` | migration candidate | ALLOWED_FALLBACK_CONTENT_OWNERS, ALLOWED_FALLBACK_SELECTION_OWNERS, OPENING_FAIL_CLOSED_CONTENT_OWNER, OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED, OPENING_FALLBACK_CONTENT_OWNER, OPENING_FALLBACK_SELECTION_OWNER, … |
| `game/final_emission_meta.py` | authority owner | OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES, OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES, OPENING_FALLBACK_OWNER_BUCKETS, OPENING_FALLBACK_OWNER_RETRY, OPENING_FALLBACK_OWNER_SEALED_GATE, OPENING_FALLBACK_OWNER_STRICT_SOCIAL, … |
| `game/final_emission_sealed_fallback.py` | migration candidate | SEALED_FALLBACK_OWNER_BUCKETS, SEALED_FALLBACK_OWNER_SEALED_GATE, SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED, SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS, SEALED_FALLBACK_OWNER_UNKNOWN_NONE |
| `game/final_emission_visibility_fallback.py` | migration candidate | VISIBILITY_FALLBACK_OWNER_BUCKETS, VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY, VISIBILITY_FALLBACK_OWNER_SEALED_GATE, VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY, VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS, VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE |
| `game/ownership_projection_views.py` | migration candidate | OPENING_FAIL_CLOSED_CONTENT_OWNER, OPENING_FALLBACK_CONTENT_OWNER, OPENING_FALLBACK_SELECTION_OWNER, OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS, SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD, SANITIZER_FALLBACK_SELECTION_OWNER, … |
| `tests/test_final_emission_meta.py` | owner suite | OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED, OPENING_FALLBACK_CONTENT_OWNER, OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES, OPENING_FALLBACK_OWNER_BUCKETS, OPENING_FALLBACK_OWNER_RETRY, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, … |

## Intentionally retained direct authority imports

| Surface | Reason |
|---|---|
| `game/final_emission_meta.py` | FEM write owner re-exports bucket mappers |
| Fallback write modules | Write-time bucket stamp authority |
| `game/attribution_read_views` / projection / observability facades | Delegate-only; sole meta_read consumer in production |
| `tests/test_final_emission_meta.py` | FEM owner suite |
| `tests/test_opening_fallback_owner_bucket.py` | Bucket mapping owner suite |
| `tests/helpers/replay_smoke_assertions.py` | Downstream FEM read bridge (BV7A) |
| `tools/*` | Tooling parity / spine validation (excluded from governance scan) |
