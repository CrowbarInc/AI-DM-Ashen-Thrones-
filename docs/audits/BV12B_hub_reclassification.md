# BV12B — Hub Reclassification

**Date:** 2026-06-21  
**Phase:** BV12B post-migration hub status

---

## Compat barrels — hub status

| Module | FI | Still a hub? | Rationale |
| --- | --- | --- | --- |
| `replay_smoke_assertions` | 1 | Yes — residual | Re-export-only barrel; FI should decay to registry/docs/delegate-test residual |
| `gate_integration_smoke` | 1 | Yes — residual | Re-export-only barrel; same decay pattern |

## Domain facades — intentional hubs

| Module | FI | Intentional hub? | Notes |
| --- | --- | --- | --- |
| `replay_fem_read_smoke` | 56 | Yes | Primary FEM read surface for replay acceptance, projection, observability |
| `gate_orchestration_smoke` | 39 | Yes | Primary gate consumer surface for orchestration/integration suites |
| `fallback_bridge_smoke` | 4 | Yes — narrow | Combined import surface for fallback dual-bridge suites only |

## Remaining migration candidates

| Category | Files | Action |
| --- | --- | --- |
| Direct compat replay imports | — | Migrate to `replay_fem_read_smoke` in BV12C if any regrow |
| Direct compat gate imports | — | Migrate to `gate_orchestration_smoke` in BV12C if any regrow |
| Registry docstrings | `tests/test_ownership_registry.py`, facade module docstrings | Update routing guidance to domain facades (BV12C governance) |
| BV10C read-cluster guard | Still references `replay_smoke_assertions` path | Extend allowlist to `replay_fem_read_smoke` in BV12C |

## BV12C readiness

- Compat barrels remain available as thin re-export shims.
- Domain facades now own consumer fan-in; governance caps can target facade FI ceilings.
- Delegate verification (`test_bv12a_smoke_bridge_facade_delegates.py`) unchanged.

