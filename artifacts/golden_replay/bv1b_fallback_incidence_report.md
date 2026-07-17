# Fallback Incidence Report

> Read-only advisory report derived from finalized recorded turn metadata. It does not affect runtime or replay scoring.

## Summary

- **Fallback trigger rate:** 1.98%
- **Eligible turns:** 101
- **Fallback turns:** 2
- **Fallback events:** 2
- **Unknown-route turns:** 1

## Fallback Kinds

| Value | Events |
|---|---:|
| `referential_clarity_hard_replacement` | 1 |
| `sealed_unknown_replacement` | 1 |

## Event Owners

| Value | Events |
|---|---:|
| `game.final_emission_gate` | 2 |

## Owner Buckets

| Value | Events |
|---|---:|
| `sealed-gate` | 1 |

## Selection Owners

| Value | Events |
|---|---:|
| `game.final_emission_gate` | 1 |
| `game.final_emission_visibility_fallback` | 1 |

## Content Owners

| Value | Events |
|---|---:|
| `game.final_emission_gate` | 1 |
| `game.final_emission_sealed_fallback` | 1 |

## Compatibility Status

| Value | Events |
|---|---:|
| `active_governed` | 1 |
| `unknown_unclassified` | 1 |

## Governed Classifications

| Value | Events |
|---|---:|
| `BOUNDED` | 1 |
| `UNKNOWN` | 1 |

## Trigger Sites

| Value | Events |
|---|---:|
| `referential_clarity_hard_replacement` | 1 |
| `sealed_terminal_replacement` | 1 |

## Trigger Conditions

| Value | Events |
|---|---:|
| `referential_clarity_gate_failed` | 1 |
| `sealed_terminal_replacement_required` | 1 |

## Route Trigger Rates

| Route | Eligible Turns | Fallback Turns | Trigger Rate |
|---|---:|---:|---:|
| `observe` | 23 | 1 | 4.35% |
| `question` | 5 | 1 | 20.00% |
| `scene_opening` | 62 | 0 | 0.00% |
| `social_probe` | 10 | 0 | 0.00% |
| `unknown` | 1 | 0 | 0.00% |

## Final Routes

| Value | Events |
|---|---:|
| `replaced` | 2 |

## Metadata Coverage

| Measure | Count |
|---|---:|
| `turns_with_runtime_lineage_events` | 101 |
| `turns_with_final_emission_meta` | 101 |
| `fallback_events_with_owner_bucket` | 1 |
| `fallback_events_with_selection_owner` | 2 |
| `fallback_events_with_content_owner` | 2 |
| `fallback_events_with_diegetic_family` | 0 |
| `fallback_events_with_realization_family` | 1 |
| `fallback_events_with_observed_family` | 0 |
| `fallback_events_with_known_route` | 2 |

## Interpretation

Rates are turn-scoped: a turn with one or more finalized `fallback_selected` events counts once as a fallback turn. Event counts remain separate so multi-event turns are visible. `route_kind`, FEM `final_route`, and event `gate_path` are intentionally not collapsed.
