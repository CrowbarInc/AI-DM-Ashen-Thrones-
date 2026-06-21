# BV12C — Hub Reclassification

**Date:** 2026-06-21  

---

## Did BV12 reduce maintenance concentration?

**Yes — on the compat bridge layer.** Combined compat FI fell from 95 → 2. Edit churn for FEM read and gate orchestration changes now localizes to domain-specific facade importers instead of a single undifferentiated bridge.

## Was redistribution intentional?

**Yes.** BV12A extracted domain facades; BV12B migrated ~72 consumer files; BV12C locks regrowth. Domain facade FI (~99 combined) reflects **deliberate domain ownership**, not monolith regrowth (4 exports per facade, pure delegates).

| Module | FI | Hub type | Verdict |
| --- | --- | --- | --- |
| `replay_smoke_assertions` | 1 | Compat shim | Not a hub — capped residual |
| `gate_integration_smoke` | 1 | Compat shim | Not a hub — capped residual |
| `replay_fem_read_smoke` | 56 | Domain hub | Intentional — FEM read surface |
| `gate_orchestration_smoke` | 39 | Domain hub | Intentional — gate consumer surface |
| `fallback_bridge_smoke` | 4 | Narrow dual-bridge | Intentional — 3 fallback suites |

## Accidental new hub creation?

**No.** Pre-BV12, a single replay bridge (FI 56) and gate bridge (FI 39) absorbed heterogeneous domains. Post-BV12, the same traffic splits across three **named domain surfaces** with governance caps on compat shims only. Net test-module fan-in is conserved, not concentrated.

