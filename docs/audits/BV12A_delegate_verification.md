# BV12A — Delegate Verification

**Date:** 2026-06-21  
**Phase:** BV12A domain facade extraction  
**Constraint:** No runtime, replay, or assertion semantic changes.

---

## Executive summary

Three domain facades were added; compatibility bridges are re-export-only barrels.

| Facade | Role | Implementation owner |
| --- | --- | --- |
| `replay_fem_read_smoke` | FEM read + debug notes | Delegates to `game.final_emission_meta_read` |
| `gate_orchestration_smoke` | Gate consumer + HTTP stub | Delegates to `game.final_emission_runtime` + replay FEM facade |
| `fallback_bridge_smoke` | Dual-bridge import surface | Re-exports domain facades only |
| `replay_smoke_assertions` | Compatibility barrel | Re-exports `replay_fem_read_smoke` |
| `gate_integration_smoke` | Compatibility barrel | Re-exports `gate_orchestration_smoke` |

## Verification method

| Check | Mechanism | Result |
| --- | --- | --- |
| Function identity delegation (compat → domain) | `tests/test_bv12a_smoke_bridge_facade_delegates.py` | Automated |
| Fallback bridge re-exports | Same test module | Automated |
| Compat barrels have no local FunctionDef | AST scan in test module | Automated |
| Gate domain uses replay FEM facade (not compat barrel) | Source import audit | Automated |
| No replay projection duplication | Forbidden fragment scan | Automated |
| Registry bridge ownership | `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge` | Automated |

## Domain separation

- **Replay responsibility:** `replay_fem_read_smoke` owns FEM extraction only.
- **Gate responsibility:** `gate_orchestration_smoke` owns runtime orchestration + fixture stub.
- **Fallback responsibility:** `fallback_bridge_smoke` combines import surface without merged logic.
- **Cross-domain coupling removed:** `gate_orchestration_smoke` imports `replay_fem_read_smoke`, not `replay_smoke_assertions`.

