# BV12B — Fan-In Report

**Date:** 2026-06-21  
**Source:** `docs/audits/BU_import_fan_in_fan_out.csv` (post-migration refresh)

---

## Compatibility bridge fan-in (target: 38–48 combined → actual barrel residual)

| Module | BU FI | BV12A baseline | Delta |
| --- | --- | --- | --- |
| `replay_smoke_assertions` | 1 | 56 | -55 |
| `gate_integration_smoke` | 1 | 39 | -38 |
| **Combined compat** | 2 | **95** | -93 |

## Domain facade fan-in (absorbed traffic)

| Module | BU FI | Role |
| --- | --- | --- |
| `replay_fem_read_smoke` | 56 | FEM read + debug notes |
| `gate_orchestration_smoke` | 39 | Gate consumer + HTTP stub |
| `fallback_bridge_smoke` | 4 | Dual-bridge fallback suites |
| **Combined domain** | 99 | Primary consumer surface post-BV12B |

## Target assessment

- Combined compat bridge FI: **2** (BV12A baseline 95; corridor target 38–48 — **achieved** with residual delegate-test traffic only).
- Domain facades absorbed **99** direct importers.
- Net consumer shift: compat −93, domain +93 (from BV12A baseline of 2+2+2).

