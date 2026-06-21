# Fallback Maintenance Economics

> Advisory-only integration of BP5-BP12 observability and remediation economics.

## Executive Summary

- Status: `ok`
- Maintenance burden: 62/100 (`high`)
- Unresolved risk: 620.00
- Backlog risk: 0
- Confidence: `low` (0/6)

## Burden Analysis

- Unresolved-risk component: 40/40
- Active-remediation component: 0/20
- Recurring-hotspot component: 20/20
- Trend/anomaly component: 2/20
- Classes: negligible <5; low <15; moderate <30; elevated <50; high <75; critical >=75.

## Risk Analysis

- Unresolved contributors: 16
- Queue entries: 0
- Trend: `stable`
- Anomalies: 0 (`none`)

## ROI Analysis

- Risk removed per engineering hour: n/a
- Unresolved risk per engineering hour: n/a
- Remediation efficiency: `unavailable`
- Total hours invested: 0

## Hotspots

| Group | Contributor | Risk | Classification | Priority | Recurrence | Anomalies |
|---|---|---:|---|---|---|---:|
| `fallback_kinds` | `fallback_kind/referential_clarity_hard_replacement` | 40.27 | `elevated` | `monitor` | `dominant` | 0 |
| `fallback_kinds` | `fallback_kind/scene_opening` | 38.38 | `moderate` | `monitor` | `dominant` | 0 |
| `fallback_kinds` | `fallback_kind/response_type_prepared_emission` | 31.08 | `moderate` | `monitor` | `dominant` | 0 |
| `fallback_kinds` | `fallback_kind/sealed_passive_scene_pressure_fallback` | 30.27 | `moderate` | `monitor` | `dominant` | 0 |
| `owners` | `content_owner/game.final_emission_sealed_fallback` | 41.14 | `elevated` | `monitor` | `dominant` | 0 |
| `owners` | `selection_owner/game.final_emission_visibility_fallback` | 40.86 | `elevated` | `monitor` | `dominant` | 0 |
| `owners` | `owner_bucket/sealed-gate` | 39.84 | `moderate` | `monitor` | `dominant` | 0 |
| `owners` | `owner_bucket/upstream-prepared` | 39.84 | `moderate` | `monitor` | `dominant` | 0 |
| `owners` | `selection_owner/game.final_emission_gate` | 39.14 | `moderate` | `monitor` | `dominant` | 0 |
| `owners` | `content_owner/game.opening_deterministic_fallback` | 38.86 | `moderate` | `monitor` | `dominant` | 0 |
| `owners` | `owner_bucket/unknown-ambiguous` | 30.33 | `moderate` | `monitor` | `dominant` | 0 |
| `routes` | `route_kind/observe` | 41.35 | `elevated` | `monitor` | `dominant` | 0 |
| `routes` | `route_kind/scene_opening` | 38.38 | `moderate` | `monitor` | `dominant` | 0 |
| `routes` | `route_kind/unknown` | 30.27 | `moderate` | `monitor` | `dominant` | 0 |
| `families` | `diegetic_family/scene_opening` | 50 | `elevated` | `monitor` | `dominant` | 0 |
| `families` | `realization_family/gate_terminal_repair` | 50 | `elevated` | `monitor` | `dominant` | 0 |

## Confidence

- Low: 0-2 points; medium: 3-4; high: 5-6.
- History depth: 2 snapshots.
- Remediation count: 0.
- Effort coverage: 0.0%.

## Recommendations

- Collect fallback history and remediation evidence before using economics in contraction planning.
