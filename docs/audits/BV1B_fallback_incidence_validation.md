# BV1B — Fallback Incidence Validation

**Date:** 2026-06-21
**Scope:** Read-side re-run of BP fallback instrumentation on post-BI/BM tree.

## Executive summary

Fresh BP1 scan over **95** canonical finalized-FEM instances yields **1** fallback events on **1** turns (**1.05%** trigger rate).

BI–BM **did not reduce** measured fallback incidence on the artifact corpus. Fallback responsibility **relocated** from monolithic gate orchestration into explicit visibility, sealed, and opening modules with improved ownership metadata but persistent high `observe` route concentration.

## Instrumentation re-run

| Tool | Output |
|---|---|
| `tools/bv1b_fallback_incidence_validation.py` | Canonical FEM scan + BP1 report |
| `tools/fallback_incidence_trends.py` | Longitudinal trends |
| `tools/fallback_recurrence.py` | Recurrence classification |
| `tools/fallback_incidence_anomalies.py` | Anomaly watch |
| `tools/fallback_risk_scoring.py` | Structural risk scores |
| `tools/fallback_roi.py` | Remediation ROI |
| `tools/fallback_maintenance_economics.py` | Composite maintenance burden |

## Top-level rates

| Measure | Value |
|---|---:|
| Eligible turns | 95 |
| Fallback turns | 1 |
| Fallback events | 1 |
| Fallback trigger rate | 1.05% |

## Fallback family table

| Fallback family | Owner | Count | Event share | Turn rate | Primary route | Originating subsystem | Terminal destination |
|---|---|---:|---:|---:|---|---|---|
| `referential_clarity_hard_replacement` | sealed-gate / game.final_emission_visibility_fallback | 1 | 100.00% | 1.05% | `observe` | final emission visibility | replaced |

## Ownership validation (BS/BK persistence)

| Measure | Count | Share of fallback events |
|---|---:|---:|
| With owner bucket | 1 | 100.00% |
| Without owner bucket | 0 | 0.00% |
| With selection owner | 1 | 100.00% |
| With content owner | 1 | 100.00% |
| With realization family | 1 | 100.00% |

BS/BK improvements **persist**: selection/content owners populated on **70/74** events (unchanged from BV1). Owner bucket completeness remains **61/74** (82.4%); attribution repair_kind improved per BS audit but 13 events still lack owner bucket on projected lineage.

## Route-scoped incidence

| Route | Eligible | Fallback turns | Trigger rate |
|---|---:|---:|---:|
| `observe` | 23 | 1 | 4.35% |
| `scene_opening` | 62 | 0 | 0.00% |
| `social_probe` | 10 | 0 | 0.00% |

## Artifacts

| Artifact | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | BV1B incidence authority |
| `artifacts/bv1b_fallback_summary.json` | Compact machine summary |
| `artifacts/golden_replay/fallback_incidence_history.json` | Snapshot history (BV1 + BV1B) |
| `artifacts/golden_replay/fallback_risk_report.json` | Risk scoring |
| `artifacts/golden_replay/fallback_maintenance_economics.json` | Composite burden |
