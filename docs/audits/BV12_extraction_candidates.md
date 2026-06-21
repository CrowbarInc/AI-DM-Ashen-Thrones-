# BV12 — Domain Extraction Candidates

**Date:** 2026-06-21  
**Constraint:** Behavior-preserving; no production changes in discovery phase  

---

## Executive answer

Decomposition is **feasible** via domain-named thin facades (1–2 symbols each) that delegate to existing implementations. Modules are already minimal; work is **consumer rerouting** and **governance**, not logic extraction.

## Candidate helper families

| Candidate module | Symbols | Est. consumers | Projected FI ↓ | Migration count | Replay risk |
| --- | --- | --- | --- | --- | --- |
| `replay_fem_read_smoke` | final_emission_meta_from_output | ~45 (acceptance + observability) | −45 from replay_smoke | ~45 import edits | low |
| `replay_projection_smoke` | final_emission_meta_from_output (alias stable) | ~8 (transcript/golden-adjacent) | −8 from replay_smoke | ~8 | low-medium |
| `pipeline_debug_notes_smoke` | read_turn_debug_notes | 3 | −3 from replay_smoke | 3 | low |
| `gate_orchestration_smoke` | apply_final_emission_gate_consumer | ~30 (orchestration/integration) | −30 from gate_integration | ~30 | low-medium |
| `gate_validation_smoke` | apply_final_emission_gate_consumer | ~9 (gate owner suites) | −9 from gate_integration | ~9 | medium |
| `gate_fixture_smoke` | gm_response_stub | 2 | −2 from gate_integration | 2 | low |
| `fallback_bridge_smoke` | gate consumer + FEM read (dual re-export) | 6 fallback dual-bridge suites | concentrates dual imports | 6 | low-medium |

## Phase-1 low-risk extractions (recommended first)

1. **`pipeline_debug_notes_smoke`** — 3 consumers, zero gate overlap.
2. **`gate_fixture_smoke`** — 2 consumers (`turn_pipeline_http_fixtures`, barrel re-export path).

These remove **5 FI** from combined cluster with minimal replay surface.

## Evidence anchors

| Metric | Value |
| --- | --- |
| final_emission_meta_from_output effective FI | 67 |
| read_turn_debug_notes FI | 3 |
| apply_final_emission_gate_consumer FI | 39 |
| gm_response_stub FI | 3 |
| Dual-bridge consumer files | 25 |

