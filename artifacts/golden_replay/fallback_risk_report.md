# Structural Fallback Risk Report

> Advisory-only maintenance risk scoring. Scores do not affect runtime or replay acceptance.

## Executive Summary

- Status: `ok`
- Snapshots analyzed: 2
- Highest-risk contributor: `realization_family/gate_terminal_repair` at 50.0 (`elevated`)
- Source signals: BP5 `stable`, BP6 `insufficient_history`, BP7 `ok`.

## Risk Model

Score = frequency contribution (20) + recurrence strength (25) + anomaly participation (15) + anomaly severity (20) + trend direction (20).

- Frequency: within-dimension cumulative incidence share, scaled to 20 points.
- Recurrence: transient 0, recurring 8, persistent 16, dominant 25.
- Anomaly participation: 5 points per matching named anomaly, capped at 15.
- Anomaly severity: none 0, info 4, watch 8, warning 14, critical 20.
- Trend: insufficient/improving 0, stable 5, worsening 20.
- Classes: negligible <10; low <25; moderate <40; elevated <60; high <80; critical >=80.
- Maximum score: 100.0.

## Ranked Hotspots

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| 1 | `elevated` | 50.0 | `realization_family` | `gate_terminal_repair` | 100.0% | `dominant` | 0 | `none` | `stable` |
| 2 | `elevated` | 50.0 | `diegetic_family` | `scene_opening` | 100.0% | `dominant` | 0 | `none` | `stable` |
| 3 | `elevated` | 41.3514 | `route_kind` | `observe` | 56.8% | `dominant` | 0 | `none` | `stable` |
| 4 | `elevated` | 41.1429 | `content_owner` | `game.final_emission_sealed_fallback` | 55.7% | `dominant` | 0 | `none` | `stable` |
| 5 | `elevated` | 40.8571 | `selection_owner` | `game.final_emission_visibility_fallback` | 54.3% | `dominant` | 0 | `none` | `stable` |
| 6 | `elevated` | 40.2703 | `fallback_kind` | `referential_clarity_hard_replacement` | 51.4% | `dominant` | 0 | `none` | `stable` |
| 7 | `moderate` | 39.8361 | `owner_bucket` | `sealed-gate` | 49.2% | `dominant` | 0 | `none` | `stable` |
| 8 | `moderate` | 39.8361 | `owner_bucket` | `upstream-prepared` | 49.2% | `dominant` | 0 | `none` | `stable` |
| 9 | `moderate` | 39.1429 | `selection_owner` | `game.final_emission_gate` | 45.7% | `dominant` | 0 | `none` | `stable` |
| 10 | `moderate` | 38.8571 | `content_owner` | `game.opening_deterministic_fallback` | 44.3% | `dominant` | 0 | `none` | `stable` |
| 11 | `moderate` | 38.3784 | `fallback_kind` | `scene_opening` | 41.9% | `dominant` | 0 | `none` | `stable` |
| 12 | `moderate` | 38.3784 | `route_kind` | `scene_opening` | 41.9% | `dominant` | 0 | `none` | `stable` |
| 13 | `moderate` | 31.0811 | `fallback_kind` | `response_type_prepared_emission` | 5.4% | `dominant` | 0 | `none` | `stable` |
| 14 | `moderate` | 30.3279 | `owner_bucket` | `unknown-ambiguous` | 1.6% | `dominant` | 0 | `none` | `stable` |
| 15 | `moderate` | 30.2703 | `fallback_kind` | `sealed_passive_scene_pressure_fallback` | 1.4% | `dominant` | 0 | `none` | `stable` |
| 16 | `moderate` | 30.2703 | `route_kind` | `unknown` | 1.4% | `dominant` | 0 | `none` | `stable` |

## Highest-Risk Kinds

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| 1 | `elevated` | 40.2703 | `fallback_kind` | `referential_clarity_hard_replacement` | 51.4% | `dominant` | 0 | `none` | `stable` |
| 2 | `moderate` | 38.3784 | `fallback_kind` | `scene_opening` | 41.9% | `dominant` | 0 | `none` | `stable` |
| 3 | `moderate` | 31.0811 | `fallback_kind` | `response_type_prepared_emission` | 5.4% | `dominant` | 0 | `none` | `stable` |
| 4 | `moderate` | 30.2703 | `fallback_kind` | `sealed_passive_scene_pressure_fallback` | 1.4% | `dominant` | 0 | `none` | `stable` |

## Highest-Risk Owners

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| 1 | `elevated` | 41.1429 | `content_owner` | `game.final_emission_sealed_fallback` | 55.7% | `dominant` | 0 | `none` | `stable` |
| 2 | `elevated` | 40.8571 | `selection_owner` | `game.final_emission_visibility_fallback` | 54.3% | `dominant` | 0 | `none` | `stable` |
| 3 | `moderate` | 39.8361 | `owner_bucket` | `sealed-gate` | 49.2% | `dominant` | 0 | `none` | `stable` |
| 4 | `moderate` | 39.8361 | `owner_bucket` | `upstream-prepared` | 49.2% | `dominant` | 0 | `none` | `stable` |
| 5 | `moderate` | 39.1429 | `selection_owner` | `game.final_emission_gate` | 45.7% | `dominant` | 0 | `none` | `stable` |
| 6 | `moderate` | 38.8571 | `content_owner` | `game.opening_deterministic_fallback` | 44.3% | `dominant` | 0 | `none` | `stable` |
| 7 | `moderate` | 30.3279 | `owner_bucket` | `unknown-ambiguous` | 1.6% | `dominant` | 0 | `none` | `stable` |

## Highest-Risk Routes

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| 1 | `elevated` | 41.3514 | `route_kind` | `observe` | 56.8% | `dominant` | 0 | `none` | `stable` |
| 2 | `moderate` | 38.3784 | `route_kind` | `scene_opening` | 41.9% | `dominant` | 0 | `none` | `stable` |
| 3 | `moderate` | 30.2703 | `route_kind` | `unknown` | 1.4% | `dominant` | 0 | `none` | `stable` |

## Highest-Risk Families

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| 1 | `elevated` | 50.0 | `realization_family` | `gate_terminal_repair` | 100.0% | `dominant` | 0 | `none` | `stable` |
| 2 | `elevated` | 50.0 | `diegetic_family` | `scene_opening` | 100.0% | `dominant` | 0 | `none` | `stable` |

## Recommendations

- Review elevated, high, and critical contributors using their factor-level evidence.
- Treat scores as maintenance prioritization signals, not runtime or replay acceptance gates.
