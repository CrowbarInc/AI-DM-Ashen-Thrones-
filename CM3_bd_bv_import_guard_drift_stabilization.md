# CM3 — BD/BV Import-Guard Drift Triage and Stabilization

Date: 2026-06-26  
Scope: import routing and read-facade re-exports only. No production behavior changes. No guard allowlist broadening.

## Summary

Resolved all three pre-existing ownership-registry guard failures (BD6, BV2C, BV10C) by routing stale direct imports through existing facades and extending read-side facade re-exports where symbols were missing. **No BD/BV guard logic was relaxed** and **no allowlist entries were added**.

`tests/test_ownership_registry.py` now passes in full (**84/84**).

## Failures Reproduced

Command: `python -m pytest tests/test_ownership_registry.py -q -k "bd6 or bv2c or bv10"`

| Test | Violation count (before) |
|---|---:|
| `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` | 1 |
| `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` | 9 |
| `test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades` | 4 |

## Violation Classification and Fixes

### BD6 — 1 violation

| File | Import | Classification | Fix |
|---|---|---|---|
| `tests/helpers/golden_replay_projection_engine.py` | `game.final_emission_replay_projection.read_opening_fallback_owner_bucket_for_replay` | Stale direct replay-projection import; should use BD-6 golden replay facade | Import from `tests.helpers.golden_replay_projection` (already re-exports symbol) |

### BV2C — 9 violations

| File | Imports | Classification | Fix |
|---|---|---|---|
| `tests/test_final_emission_opening_fallback.py` | `OPENING_FALLBACK_EMITTED_METADATA_FIELDS`, `OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS`, `opening_fallback_metadata_classification_parity_errors`, `OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS`, `merge_response_type_meta`, `read_final_emission_meta_dict` | Stale direct `final_emission_meta` imports | Route through `game.observability_attribution_read`; `read_final_emission_meta_dict` uses existing module-level `replay_fem_read_smoke` alias |
| `tests/test_golden_replay_fallback_opening_projection.py` | `OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS`, `OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS` | Stale direct meta import in inline test | Route through `game.observability_attribution_read` |
| `tests/test_opening_fallback_owner_bucket.py` | `OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS` | Stale direct meta import at module level | Route through `game.observability_attribution_read` |

### BV10C — 4 violations (after BV2C facade pass)

| File | Imports | Classification | Fix |
|---|---|---|---|
| `tests/test_final_emission_opening_fallback.py` | `game.final_emission_ownership_schema.OPENING_FALLBACK_LEGACY_*`, `OPENING_FALLBACK_RETIRED_*` | Stale direct ownership-schema import | Route through `game.attribution_read_views` |
| `tests/test_golden_replay_fallback_opening_projection.py` | `OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP` | Stale direct ownership-schema import | Route through `game.attribution_read_views` |
| `tests/test_failure_classifier.py` | `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES` in static-lock test | Stale direct ownership-schema import | Route through `game.attribution_read_views` |
| `tests/test_opening_fallback_owner_bucket.py` | inline `ownership_schema` imports | Stale direct ownership-schema import | Route through `game.attribution_read_views` |

After BV2C routing moved imports to `final_emission_meta_read`, BV10C flagged those as read-cluster authority imports. Resolved by extending `game.observability_attribution_read` to re-export opening-fallback read symbols and routing consumer tests there (BV10 outer facade).

## Facade Extensions (narrow re-exports only)

| File | Symbols added |
|---|---|
| `game/final_emission_meta_read.py` | `OPENING_FALLBACK_*` field registries, `opening_fallback_metadata_classification_parity_errors`, `merge_response_type_meta`, `final_emission_meta_read_side_surface` (already partial) |
| `game/attribution_read_views.py` | `OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP` |
| `game/observability_attribution_read.py` | Opening-fallback read symbols delegated from `final_emission_meta_read` |

## Guard Modules — No Allowlist Changes

`tests/ownership_guard_bd_dependency_compression.py` and `tests/ownership_guard_bv_compatibility.py` were **not modified**. No wildcard exclusions added.

## Validation Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_ownership_registry.py -q -k "bd6 or bv2c or bv10"` | **9 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **84 passed** |
| `python -m pytest tests/test_gate_context_ownership_guards.py -q` | **33 passed** |
| `python -m pytest tests/test_gate_delegate_closeout_locks.py -q` | **100 passed** |
| `python -m pytest tests/test_final_emission_opening_fallback.py tests/test_golden_replay_fallback_opening_projection.py tests/test_opening_fallback_owner_bucket.py tests/test_failure_classifier.py -q` | **All passed** |
| `python tools/test_audit.py --check` | **Failed — pre-existing unrelated drift** (+4 `tests/test_failure_dashboard_*.py` files missing from committed inventory; not introduced by CM3) |

## CM4 Readiness

**BD/BV entrypoint extraction is now safe to proceed.**

- All three blocking guard families pass.
- Full registry suite passes (84/84).
- Fixes are routing/facade-only; no structural guard weakening.
- Remaining `test_audit.py --check` failure is unrelated failure-dashboard inventory drift and should not block CM4.
