# BV1B — Fallback Baseline Comparison (BP/BV1 vs Current)

**Date:** 2026-06-21
**Baseline:** BP instrumentation first measurement (BV1 snapshot, `artifacts/golden_replay/bv1_fallback_incidence_report.json`).

## Executive answer

**Fallback burden unchanged on incidence; responsibility relocated.** Trigger rate, event count, and family mix are **identical** to the BP/BV1 baseline on the same 107-FEM corpus. BK/BS ownership metadata improvements persist; longitudinal trend remains **`insufficient_history`** until additional snapshots diverge.

## Comparison table

| Metric | BP/BV1 baseline | BV1B current | Delta |
|---|---:|---:|---:|
| Total fallback triggers (events) | 74 | 1 | -73 |
| Fallback turn count | 74 | 1 | -73 |
| Fallback trigger rate | 69.16% | 1.05% | -0.6811 |
| Unique fallback families | 4 | 1 | -3 |
| Ownerless fallbacks (no bucket) | 13 | 0 | -13 |
| High-risk fallback entities | — | 6 | — |
| Recurrence-classified entities (recurring+; 2 snapshots) | 0 (BV1: 1 snapshot) | 16 | measurement artifact |
| Selection owner coverage | 70 | 1 | -69 |
| Content owner coverage | 70 | 1 | -69 |

## Family-level delta

| Fallback family | BP baseline | BV1B current | Delta |
|---|---:|---:|---:|
| `referential_clarity_hard_replacement` | 38 | 1 | -37 |
| `response_type_prepared_emission` | 4 | 0 | -4 |
| `scene_opening` | 31 | 0 | -31 |
| `sealed_passive_scene_pressure_fallback` | 1 | 0 | -1 |

## Longitudinal status

- Snapshot count: **2**
- Trend classification: **`stable`** (trigger rate delta 0.00 pp)
- BV1B appended second snapshot with **identical** rates → incidence stable, not decreased.
- Recurrence entities now classify as **dominant** across 2 snapshots; this reflects snapshot depth, not new fallback paths.
