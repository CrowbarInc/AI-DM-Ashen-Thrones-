# BV7A — Replay & Gate Bridge Extraction

**Date:** 2026-06-21  
**Scope:** Extract highest-fan-in bridge families from `emission_smoke_assertions`; migrate consumers; measure fan-in.  
**Constraint:** No runtime, replay, or test semantic changes.

---

## Executive summary

BV7A split the two dominant bridge families into dedicated helper modules, kept `emission_smoke_assertions` as a **compatibility barrel** (re-exports via `__all__`), and migrated **64 consumers** to direct bridge imports.

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| **`emission_smoke_assertions` FI** | **73** | **30** | **−43 (−59%)** |
| **`replay_smoke_assertions` FI** | 0 (n/a) | **46** | +46 (new hub) |
| **`gate_integration_smoke` FI** | 0 (n/a) | **39** | +39 (new hub) |
| Phase target (≤55 on monolith) | — | **30** | **Met** |

Bridge symbol caller fan-in moved with extraction:

| Symbol | Before (via monolith) | After (owner module) |
|---|---:|---:|
| `final_emission_meta_from_output` | 42 | **43** (`replay_smoke_assertions`) |
| `apply_final_emission_gate_consumer` | 37 | **37** (`gate_integration_smoke`) |

Monolith is **no longer #1** ecosystem fan-in hub. Largest test helper FI nodes are now the extracted bridges (expected redistribution).

---

## Modules created

| Module | Symbols owned | Production fan-out |
|---|---|---|
| `tests/helpers/replay_smoke_assertions.py` | `final_emission_meta_from_output`, `read_turn_debug_notes` | `game.final_emission_meta_read` |
| `tests/helpers/gate_integration_smoke.py` | `apply_final_emission_gate_consumer`, `gm_response_stub` | `game.final_emission_runtime` (+ replay bridge for FEM) |

`tests/helpers/emission_smoke_assertions.py` retains phrase/route smoke, AC/RD consumer seams, and **re-exports** all extracted symbols for backward compatibility.

---

## Consumer migration (Phase 1)

**Method:** `scripts/bv7a_migrate_bridge_imports.py` — AST import split by bridge symbol class.

| Category | Files migrated |
|---|---:|
| Replay bridge only | 18 |
| Gate bridge only | 11 |
| Both bridges (+ optional smoke symbols) | 35 |
| **Total** | **64** |

**Remaining monolith importers (30):** suites that import smoke-only symbols (`assert_*`, `response_type_contract`, AC/RD layers) without bridge-only imports, plus `opening_fallback_evidence.py` and the contract test module.

Examples still on monolith:

- `tests/test_turn_pipeline_shared.py` — phrase/route smoke bundle
- `tests/test_emission_smoke_assertions_contract.py` — facade contract owner
- `tests/test_final_emission_boundary_convergence.py` — AC/RD + gate + smoke mix (gate/replay split; smoke stays)

---

## Governance updates

| Area | Change |
|---|---|
| BN1 downstream test seam | `gate_integration_smoke.apply_final_emission_gate_consumer` |
| BD6 compression guard replacement strings | Gate → `gate_integration_smoke`; FEM read → `replay_smoke_assertions` |
| BJ-4 registry lock | Validates BV7A bridge modules + monolith `__all__` re-exports |
| `game/final_emission_runtime.py` doc | Points to gate bridge (with monolith re-export note) |

---

## Regression validation

```text
pytest tests/test_emission_smoke_assertions_contract.py
pytest tests/test_turn_pipeline_shared.py
pytest tests/test_golden_replay_direct_seam.py
pytest tests/test_final_emission_gate_orchestration_order.py
pytest tests/test_final_emission_boundary_convergence.py
pytest tests/test_narration_transcript_regressions.py
pytest tests/test_bv4b_concrete_beat_upstream_satisfier.py
pytest tests/test_ownership_registry.py::test_bj4_emission_smoke_facade_stays_weak_consumer_bridge
```

**Result:** All targeted suites green. Replay parity, gate behavior, and smoke expectations unchanged (import-path-only migration + delegate move without logic edits).

---

## Remaining work (BV7B+)

| Item | FI impact estimate |
|---|---:|
| Migrate mixed smoke+bridge suites off monolith re-export | −10 to −15 monolith FI |
| Extract `consumer_layer_smoke` (AC/RD/RT seams) | −18 monolith FI |
| Extract pure route/phrase/speaker smoke families | −12 monolith FI |
| Retire or thin barrel when monolith FI ≤5 | governance |

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Post-BV7A module FI |
| `docs/audits/BU_caller_fan_in.csv` | Per-symbol caller FI |
| [BV7_verification_projection.md](BV7_verification_projection.md) | Updated Phase 2 projection |
| [BV7_concentration_report.md](BV7_concentration_report.md) | Pre-BV7A baseline |
