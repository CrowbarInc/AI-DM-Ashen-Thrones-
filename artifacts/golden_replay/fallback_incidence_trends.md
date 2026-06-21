# Fallback Incidence Trends

> Read-only longitudinal reporting derived from BP1 snapshots.

## Executive Summary

- **Trend classification:** `stable`
- **Snapshot count:** 2
- **Thresholds:** improving below -1.00 percentage point, stable within +/-1.00 percentage point, worsening above +1.00 percentage point.
- **Rolling baseline:** up to 5 prior snapshots.

## Current Snapshot

- Timestamp: `2026-06-21T11:37:14.736308Z`
- Artifact source: `BV1B:artifact_scan_107_fem`
- Eligible turns: 107
- Fallback turns: 74
- Fallback events: 74
- Fallback trigger rate: 69.16%

## Change Since Previous Snapshot

- Trigger-rate delta: +0.00 pp
- Fallback-event delta: +0
- Fallback-turn delta: +0

## Top Fallback Kinds

| Name | Current | Previous | Delta | Direction |
|---|---:|---:|---:|---|
| `referential_clarity_hard_replacement` | 38 | 38 | +0 | `stable` |
| `scene_opening` | 31 | 31 | +0 | `stable` |
| `response_type_prepared_emission` | 4 | 4 | +0 | `stable` |
| `sealed_passive_scene_pressure_fallback` | 1 | 1 | +0 | `stable` |

## Top Owners

| Name | Current | Previous | Delta | Direction |
|---|---:|---:|---:|---|
| `sealed-gate` | 30 | 30 | +0 | `stable` |
| `upstream-prepared` | 30 | 30 | +0 | `stable` |
| `unknown-ambiguous` | 1 | 1 | +0 | `stable` |
| `game.final_emission_visibility_fallback` | 38 | 38 | +0 | `stable` |
| `game.final_emission_gate` | 32 | 32 | +0 | `stable` |
| `game.final_emission_sealed_fallback` | 39 | 39 | +0 | `stable` |
| `game.opening_deterministic_fallback` | 31 | 31 | +0 | `stable` |

## Top Routes

| Route | Eligible | Fallback Turns | Rate | Delta | Direction |
|---|---:|---:|---:|---:|---|
| `scene_opening` | 62 | 31 | 50.00% | +0.00 pp | `stable` |
| `observe` | 44 | 42 | 95.45% | +0.00 pp | `stable` |
| `unknown` | 1 | 1 | 100.00% | +0.00 pp | `stable` |

## Trend Direction

`stable`

## Notable Changes

- `fallback_event_count`: +0
- `fallback_trigger_rate`: +0
- `fallback_turn_count`: +0
