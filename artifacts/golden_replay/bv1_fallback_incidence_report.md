# Fallback Incidence Report

> Read-only advisory report derived from finalized recorded turn metadata. It does not affect runtime or replay scoring.

## Summary

- **Fallback trigger rate:** 69.16%
- **Eligible turns:** 107
- **Fallback turns:** 74
- **Fallback events:** 74
- **Unknown-route turns:** 1

## Fallback Kinds

| Value | Events |
|---|---:|
| `referential_clarity_hard_replacement` | 38 |
| `scene_opening` | 31 |
| `response_type_prepared_emission` | 4 |
| `sealed_passive_scene_pressure_fallback` | 1 |

## Event Owners

| Value | Events |
|---|---:|
| `game.final_emission_gate` | 74 |

## Owner Buckets

| Value | Events |
|---|---:|
| `sealed-gate` | 30 |
| `upstream-prepared` | 30 |
| `unknown-ambiguous` | 1 |

## Selection Owners

| Value | Events |
|---|---:|
| `game.final_emission_visibility_fallback` | 38 |
| `game.final_emission_gate` | 32 |

## Content Owners

| Value | Events |
|---|---:|
| `game.final_emission_sealed_fallback` | 39 |
| `game.opening_deterministic_fallback` | 31 |

## Route Trigger Rates

| Route | Eligible Turns | Fallback Turns | Trigger Rate |
|---|---:|---:|---:|
| `observe` | 44 | 42 | 95.45% |
| `scene_opening` | 62 | 31 | 50.00% |
| `unknown` | 1 | 1 | 100.00% |

## Final Routes

| Value | Events |
|---|---:|
| `replaced` | 72 |
| `accept_candidate` | 2 |

## Metadata Coverage

| Measure | Count |
|---|---:|
| `turns_with_runtime_lineage_events` | 107 |
| `turns_with_final_emission_meta` | 107 |
| `fallback_events_with_owner_bucket` | 61 |
| `fallback_events_with_selection_owner` | 70 |
| `fallback_events_with_content_owner` | 70 |
| `fallback_events_with_diegetic_family` | 1 |
| `fallback_events_with_realization_family` | 60 |
| `fallback_events_with_observed_family` | 0 |
| `fallback_events_with_known_route` | 73 |

## Interpretation

Rates are turn-scoped: a turn with one or more finalized `fallback_selected` events counts once as a fallback turn. Event counts remain separate so multi-event turns are visible. `route_kind`, FEM `final_route`, and event `gate_path` are intentionally not collapsed.
