# BV13C — Final Compat Import Audit

**Date:** 2026-06-21  
**Phase:** BV13C governance closeout  
**Target:** `game.final_emission_text` compatibility barrel

---

## Executive summary

Post-BV13B, compat barrel AST fan-in is **4** (cap ≤8; BV13B regex scan reported 5 including
`gate_thin_boundary_locks` governance string markers). Residual imports are fallback wrapper
users and delegate verification only. Formatting and policy traffic routes through canonical
authority modules.

| Module | AST FI | Classification | Verdict |
| --- | --- | --- | --- |
| `game.final_emission_text` | 4 | Compat shim | Locked — capped residual ✓ |
| `game.final_emission_text_formatting` | 51 | Formatting authority | Intentional domain hub |
| `game.final_emission_text_policy` | 8 | Policy authority | Controlled policy surface |

## Residual compat importers (allowlisted)

| File | Symbol / import | Classification | Status |
| --- | --- | --- | --- |
| `game/final_emission_fast_fallback_composition.py` | `_global_narrative_fallback_stock_line` | fallback wrapper | Allowlisted ✓ |
| `game/final_emission_scene_emit_integrity.py` | `_global_narrative_fallback_stock_line` | fallback wrapper | Allowlisted ✓ |
| `tests/test_bv13a_final_emission_text_facade_delegates.py` | `module import` | delegate verification | Allowlisted ✓ |
| `tests/test_diegetic_fallback_block4.py` | `_global_narrative_fallback_stock_line` | fallback wrapper | Allowlisted ✓ |

## Governance marker scans (string references, not imports)

| File | Role | Classification |
| --- | --- | --- |
| `tests/helpers/gate_thin_boundary_locks.py` | BN9/BV13C forbidden import markers | governance marker |

## AST scan — non-allowlisted import sites

_No non-allowlisted compat barrel imports found._

