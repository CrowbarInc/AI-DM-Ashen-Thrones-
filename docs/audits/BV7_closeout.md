# BV7 — Smoke Decomposition Closeout

**Date:** 2026-06-21  
**Status:** **CLOSED** (BV7A + BV7B + BV7C)  
**Primary metric:** Smoke Helper Concentration (`emission_smoke_assertions` fan-in)

---

## Executive summary

BV7 decomposed the accidental bridge hub inside `tests/helpers/emission_smoke_assertions.py` into named family modules while preserving BE6 triple-layer smoke boundaries and zero runtime/replay semantic changes. The monolith FI fell from **73 → 15 (−79%)** and is now a **smoke-core compatibility barrel** only. BV7C locked import governance to prevent monolith regrowth.

---

## Phase summary

### BV7A — Replay & gate bridge extraction

| Item | Detail |
|---|---|
| **Scope** | Extract FEM read + gate orchestration bridges |
| **Modules created** | `replay_smoke_assertions`, `gate_integration_smoke` |
| **Consumers migrated** | 64 suites |
| **Monolith FI** | 73 → 30 (−59%) |
| **Evidence** | [BV7A_bridge_extraction.md](BV7A_bridge_extraction.md) |

### BV7B — Consumer-layer (RT/AC/RD) extraction

| Item | Detail |
|---|---|
| **Scope** | Extract response-type, actor-consistency, route-determinism consumer seams |
| **Modules created** | `response_type_smoke`, `actor_consistency_smoke`, `route_determinism_smoke` |
| **Consumers migrated** | 16 suites (+ split imports on 4) |
| **Monolith FI** | 30 → 15 (−50%) |
| **Evidence** | [BV7B_consumer_extraction.md](BV7B_consumer_extraction.md) |

### BV7C — Closeout & governance lock

| Item | Detail |
|---|---|
| **Scope** | Final import audit, hub re-measurement, governance enforcement |
| **Governance added** | `test_bv7c_smoke_monolith_*` import guard + FI cap (18) |
| **Monolith FI** | **15** (unchanged — verification only) |
| **Evidence** | [BV7C_import_audit.md](BV7C_import_audit.md), [BV7C_import_classification.md](BV7C_import_classification.md), [BV7C_hub_rankings.md](BV7C_hub_rankings.md) |

---

## Primary metrics

| Metric | Start (pre-BV7) | End (BV7C) | Delta |
|---|---:|---:|---:|
| **`emission_smoke_assertions` FI** | **73** | **15** | **−58 (−79%)** |
| **`replay_smoke_assertions` FI** | 0 (n/a) | **46** | +46 (intentional bridge hub) |
| **`gate_integration_smoke` FI** | 0 (n/a) | **39** | +39 (intentional bridge hub) |

### Supporting family metrics (BV7B)

| Metric | Start | End | Delta |
|---|---:|---:|---:|
| `response_type_smoke` FI | 0 | 17 | +17 |
| `actor_consistency_smoke` FI | 0 | 5 | +5 |
| `route_determinism_smoke` FI | 0 | 5 | +5 |

---

## Constraints verified

| Constraint | Status |
|---|---|
| No runtime behavior changes | ✓ |
| No replay behavior changes | ✓ |
| No assertion semantic changes | ✓ |
| BE6 triple-layer phrase split preserved | ✓ |
| Monolith target band 12–18 FI | ✓ (15) |

---

## Governance locks (post-BV7C)

| Guard | Enforces |
|---|---|
| `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge` | Bridge modules exist; monolith `__all__` re-exports |
| `test_be6_scaffold_phrase_triple_layer_split_locked` | Phrase matrix separation |
| `test_bv7c_smoke_monolith_import_guard_*` | No RT/AC/RD/gate/replay bridge imports from monolith |
| `test_bv7c_emission_smoke_assertions_concentration_locked` | Static importer allowlist + FI cap |

Required facades for new imports:

- `response_type_smoke` — RT consumer seams
- `actor_consistency_smoke` — AC consumer seams
- `route_determinism_smoke` — RD consumer seams
- `replay_smoke_assertions` — FEM read bridge
- `gate_integration_smoke` — gate orchestration bridge

---

## Residual monolith role

After BV7C, `emission_smoke_assertions` owns **only**:

1. Phrase / hygiene smoke (BE6 layer 2)
2. Route wiring smoke (AL3 downstream sentinels)
3. Speaker / open-call smoke
4. Compatibility barrel re-exports for extracted symbols

It is **not** a maintenance hub for bridge or consumer-layer policy edits.

---

## Next target

See [BV8_candidate_analysis.md](BV8_candidate_analysis.md). **Recommended:** BV8 — speaker projection recurrence retirement (maintenance drag not addressed by BV7 bridge split).

---

## Evidence index

| Document | Phase |
|---|---|
| [BV7_concentration_report.md](BV7_concentration_report.md) | Recon |
| [BV7_decomposition_plan.md](BV7_decomposition_plan.md) | Plan |
| [BV7A_bridge_extraction.md](BV7A_bridge_extraction.md) | BV7A |
| [BV7B_consumer_extraction.md](BV7B_consumer_extraction.md) | BV7B |
| [BV7B_remaining_importers.md](BV7B_remaining_importers.md) | BV7B |
| [BV7C_import_audit.md](BV7C_import_audit.md) | BV7C |
| [BV7C_import_classification.md](BV7C_import_classification.md) | BV7C |
| [BV7C_hub_rankings.md](BV7C_hub_rankings.md) | BV7C |
| `tests/test_ownership_registry.py` | Governance |
