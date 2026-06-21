# BV12A — Facade Extraction Baseline

**Date:** 2026-06-21  
**Phase:** BV12A complete — no consumer migrations yet  

---

## Current fan-in (unchanged — compat barrels retained)

| Module | BU FI | Status |
| --- | --- | --- |
| `replay_smoke_assertions` | 56 | Compatibility barrel |
| `gate_integration_smoke` | 39 | Compatibility barrel |
| **Combined** | 95 | Baseline for Phase 2 |

## New domain facades (Phase 1 extraction)

| Module | Exports | Phase 2 migration target FI |
| --- | --- | --- |
| `replay_fem_read_smoke` | 2 | ~53 (FEM read consumers) |
| `gate_orchestration_smoke` | 2 | ~37 (gate consumer consumers) |
| `fallback_bridge_smoke` | 2 (re-export) | ~3 fallback dual-bridge suites |

## Migration-ready consumers (Phase 2)

| Target facade | Ready consumers | Notes |
| --- | --- | --- |
| replay_fem_read_smoke | 57 | Direct importers of compat barrel today |
| gate_orchestration_smoke | 40 | Direct importers of compat barrel today |
| fallback_bridge_smoke | 3 | `tests/test_fallback_overwrite_containment.py`, `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_strict_social_emergency_fallback_dialogue.py` |

## Projected Phase 2 reduction

| Metric | Current | Post Phase 2 (est.) |
| --- | --- | --- |
| Combined compat bridge FI | 95 | 38–48 |
| replay_smoke_assertions FI | 56 | 8–12 (barrel only) |
| gate_integration_smoke FI | 39 | 6–10 (barrel only) |
| Domain facade FI (distributed) | 0 | 70–80 |

## Validation

| Suite batch | Result |
| --- | --- |
| BV12A delegate verification | 8/8 pass |
| Registry (BJ4 + BV10C guards) | pass |
| Replay (golden_replay_direct_seam, projection) | pass |
| Gate (orchestration_order, selector_snapshots, n4) | pass |
| Fallback (behavior_gate, overwrite_containment, diegetic) | pass |
| Smoke (anti_railroading, turn_pipeline_shared, emission contract) | pass |
| Note | `test_final_emission_opening_fallback::test_adapter_selects_usable_upstream_prepared_payload_unchanged` fails on owner-bucket projection (orthogonal to BV12A import routing) |

