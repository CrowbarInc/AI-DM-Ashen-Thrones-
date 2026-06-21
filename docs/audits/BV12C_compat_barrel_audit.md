# BV12C — Compat Barrel Audit

**Date:** 2026-06-21  
**Phase:** BV12C governance closeout  

---

## Executive summary

Post-BV12B, compat barrel imports are **delegate verification only**. No consumer suites import `replay_smoke_assertions` or `gate_integration_smoke` directly.

| Compat module | BU FI | Static import sites (excl. allowlist) | Verdict |
| --- | --- | --- | --- |
| `replay_smoke_assertions` | 1 | 0 | Delegate-only ✓ |
| `gate_integration_smoke` | 1 | 0 | Delegate-only ✓ |

## Allowlisted residual consumers

| File | Imports | Classification |
| --- | --- | --- |
| `tests/test_bv12a_smoke_bridge_facade_delegates.py` | Both compat barrels (module import) | BV12A delegate verification — required |

## AST scan — non-allowlisted import sites

_No non-allowlisted compat barrel imports found._

## Barrel implementation (re-export only)

| Barrel | Delegates to |
| --- | --- |
| `replay_smoke_assertions` | `replay_fem_read_smoke` |
| `gate_integration_smoke` | `gate_orchestration_smoke` |

