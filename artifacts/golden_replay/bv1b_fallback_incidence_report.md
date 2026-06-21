# Fallback Incidence Report

> Read-only advisory report derived from finalized recorded turn metadata. It does not affect runtime or replay scoring.

## Summary

- **Fallback trigger rate:** 1.05%
- **Eligible turns:** 95
- **Fallback turns:** 1
- **Fallback events:** 1
- **Unknown-route turns:** 0

## Fallback Kinds

| Value | Events |
|---|---:|
| `referential_clarity_hard_replacement` | 1 |

## Event Owners

| Value | Events |
|---|---:|
| `game.final_emission_gate` | 1 |

## Owner Buckets

| Value | Events |
|---|---:|
| `sealed-gate` | 1 |

## Selection Owners

| Value | Events |
|---|---:|
| `game.final_emission_visibility_fallback` | 1 |

## Content Owners

| Value | Events |
|---|---:|
| `game.final_emission_sealed_fallback` | 1 |

## Route Trigger Rates

| Route | Eligible Turns | Fallback Turns | Trigger Rate |
|---|---:|---:|---:|
| `observe` | 23 | 1 | 4.35% |
| `scene_opening` | 62 | 0 | 0.00% |
| `social_probe` | 10 | 0 | 0.00% |

## Final Routes

| Value | Events |
|---|---:|
| `replaced` | 1 |

## Metadata Coverage

| Measure | Count |
|---|---:|
| `turns_with_runtime_lineage_events` | 95 |
| `turns_with_final_emission_meta` | 95 |
| `fallback_events_with_owner_bucket` | 1 |
| `fallback_events_with_selection_owner` | 1 |
| `fallback_events_with_content_owner` | 1 |
| `fallback_events_with_diegetic_family` | 0 |
| `fallback_events_with_realization_family` | 1 |
| `fallback_events_with_observed_family` | 0 |
| `fallback_events_with_known_route` | 1 |

## Interpretation

Rates are turn-scoped: a turn with one or more finalized `fallback_selected` events counts once as a fallback turn. Event counts remain separate so multi-event turns are visible. `route_kind`, FEM `final_route`, and event `gate_path` are intentionally not collapsed.
