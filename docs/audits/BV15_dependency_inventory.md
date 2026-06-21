# BV15 — Final Emission Gate Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only — every direct importer of `game.final_emission_gate`
**Method:** `python tools/bv15_final_emission_gate_discovery.py` + BU CSV reconciliation

---

## Hub baseline (current)

| Module | BU fan-in | AST direct importers | Defined exports | Re-exports | LOC | Fan-out |
| --- | --- | --- | --- | --- | --- | --- |
| `game.final_emission_gate` | **30** | 31 | 1 | 13 | 338 | 11 |

**BV14 context:** `social_exchange_emission` compat FI **52 → 12**; gate owner is now the highest remaining **production-core orchestration** concentration at FI **30**.

**Post-BN decomposition:** Module body is **338 LOC** with a single defined orchestration entrypoint (`apply_final_emission_gate`); 13 stack/preflight symbols remain as **namespace re-exports** from extracted owners (BN1–BN11).

## Importer split

| Layer | Count | Share |
| --- | --- | --- |
| Production (`game/`) | 1 | 3% |
| Tests (`tests/`) | 30 | 96% |

## Summary by subsystem

| Subsystem | Importers | Primary symbols |
| --- | --- | --- |
| final emission gate | 14 | `apply_final_emission_gate` |
| integration/regression | 13 | `feg (module)` |
| final emission pipeline | 1 | `apply_final_emission_gate` |
| gate helpers | 1 | `feg (module)` |
| ownership governance | 1 | `feg (module)` |
| diagnostics | 1 | `feg (module)` |

## Full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
| --- | --- | --- | --- |
| `game/final_emission_runtime.py` | final emission pipeline | `apply_final_emission_gate` | gate-orchestration |
| `tests/helpers/gate_equivalence_monkeypatch.py` | gate helpers | `feg (module)` | module-introspection |
| `tests/test_answer_shape_primacy.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_block_u_finalize_stack_divergence.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_bv3a_observe_referential_clarity_repair.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_bv3e_eligibility_expansion.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_c4_narrative_mode_live_pipeline.py` | integration/regression | `feg_module (module)` | module-introspection |
| `tests/test_dialogue_social_plan.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_diegetic_fallback_narration.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_fallback_behavior_gate.py` | final emission gate | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_final_emission_acceptance_quality.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | final emission gate | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_final_emission_fast_fallback_composition.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_final_emission_gate_diagnostics.py` | final emission gate | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_final_emission_gate_n4.py` | final emission gate | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_final_emission_gate_orchestration_order.py` | final emission gate | `apply_final_emission_gate`, `get_speaker_selection_contract` | gate-orchestration |
| `tests/test_final_emission_gate_selector_snapshots.py` | final emission gate | `apply_final_emission_gate`, `feg (module)` | module-introspection |
| `tests/test_final_emission_opening_fallback.py` | final emission gate | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_final_emission_response_type.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_final_emission_scene_state_anchor.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_final_emission_sealed_fallback.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_final_emission_visibility.py` | final emission gate | `apply_final_emission_gate`, `feg (module)` | module-introspection |
| `tests/test_final_emission_visibility_fallback.py` | final emission gate | `feg (module)` | module-introspection |
| `tests/test_ownership_registry.py` | ownership governance | `feg (module)` | ownership-governance |
| `tests/test_social_exchange_emission.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_speaker_contract_enforcement_extraction.py` | integration/regression | `feg (module)` | module-introspection |
| `tests/test_speaker_contract_risk.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_tone_escalation_rules.py` | integration/regression | `apply_final_emission_gate` | gate-orchestration |
| `tests/test_validation_layer_separation_runtime.py` | diagnostics | `feg (module)` | module-introspection |
