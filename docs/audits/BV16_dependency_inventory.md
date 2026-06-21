# BV16 — Final Emission Terminal Pipeline Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only — every direct importer of `game.final_emission_terminal_pipeline`
**Method:** `python tools/bv16_final_emission_terminal_pipeline_discovery.py` + BU CSV reconciliation

---

## Hub baseline (current)

| Module | BU fan-in | AST direct importers | Defined exports | Namespace imports | LOC | Fan-out |
| --- | --- | --- | --- | --- | --- | --- |
| `game.final_emission_terminal_pipeline` | **26** | 26 | 5 | 24 | 350 | 18 |

**BV15 context:** `final_emission_gate` classified as **legitimate orchestration authority** (FI **30**, governance-inflated). Terminal pipeline is the paired **finalize-tail** target at FI **26**.

**Module shape:** **350 LOC** with **5 defined symbols** (`run_gate_terminal_enforcement_pipeline`, `apply_strict_social_emergency_fallback_patch`, profile type, 2 private helpers) and **24 imported symbols** bound at module scope (visibility, N4, IC, opening, repairs, meta).

## Importer split

| Layer | Count | Share |
| --- | --- | --- |
| Production (`game/`) | 2 | 7% |
| Tests (`tests/`) | 24 | 92% |

## Summary by subsystem

| Subsystem | Importers | Primary symbols / attrs |
| --- | --- | --- |
| final emission terminal | 11 | `terminal_pipeline (module)` |
| integration/regression | 9 | `terminal_pipeline (module)` |
| final emission pipeline | 2 | `terminal_pipeline (module)` |
| replay | 2 | `terminal_pipeline (module)` |
| gate helpers | 1 | `terminal_pipeline (module)` |
| ownership governance | 1 | `terminal_pipeline (module)` |

## Full importer table

| File | Subsystem | Imported symbols | Attribute uses | Ownership bucket |
| --- | --- | --- | --- | --- |
| `game/final_emission_generic_exit.py` | final emission pipeline | `terminal_pipeline (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `game/final_emission_strict_social_stack.py` | final emission pipeline | `terminal_pipeline (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `tests/helpers/post_speaker_finalize_probe.py` | gate helpers | `terminal_pipeline (module)` | `_apply_fallback_behavior_layer`, `_apply_referent_clarity_pre_finalize`, `apply_acceptance_quality_n4_floor_seam`, `apply_interaction_continuity_emission_step`, `apply_visibility_enforcement`, `attach_interaction_continuity_validation` | visibility-monkeypatch |
| `tests/test_anti_railroading.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_anti_railroading_transcript_regressions.py` | replay | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_context_separation.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_fallback_behavior_gate.py` | final emission terminal | `terminal_pipeline (module)` | `_apply_fallback_behavior_layer`, `apply_interaction_continuity_emission_step` | terminal-tail-monkeypatch |
| `tests/test_final_emission_acceptance_quality.py` | final emission terminal | `terminal_pipeline (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `tests/test_final_emission_boundary_convergence.py` | final emission terminal | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | final emission terminal | `terminal_pipeline (module)` | `_apply_referent_clarity_pre_finalize`, `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_final_emission_gate_n4.py` | final emission terminal | `terminal_pipeline (module)` | `attach_interaction_continuity_validation` | terminal-tail-monkeypatch |
| `tests/test_final_emission_gate_orchestration_order.py` | final emission terminal | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_final_emission_gate_selector_snapshots.py` | final emission terminal | `terminal_pipeline (module)` | `apply_acceptance_quality_n4_floor_seam`, `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_final_emission_narration_constraint_debug.py` | final emission terminal | `terminal_pipeline (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `tests/test_final_emission_opening_accept_debug.py` | final emission terminal | `terminal_pipeline (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `tests/test_final_emission_sealed_fallback.py` | final emission terminal | `apply_strict_social_emergency_fallback_patch` | — | finalize-realization |
| `tests/test_final_emission_visibility_fallback.py` | final emission terminal | `tp (module)` | `run_gate_terminal_enforcement_pipeline` | terminal-orchestration |
| `tests/test_narration_transcript_regressions.py` | replay | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_ownership_registry.py` | ownership governance | `terminal_pipeline (module)`, `tp (module)` | `apply_visibility_enforcement`, `run_gate_terminal_enforcement_pipeline` | ownership-governance |
| `tests/test_player_facing_narration_purity.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_prompt_context.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_referential_clarity_player_coref.py` | integration/regression | `terminal_pipeline (module)` | `_apply_referent_clarity_pre_finalize`, `run_gate_terminal_enforcement_pipeline` | module-introspection |
| `tests/test_social_exchange_emission.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_speaker_contract_enforcement.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_speaker_contract_risk.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
| `tests/test_tone_escalation_rules.py` | integration/regression | `terminal_pipeline (module)` | `apply_visibility_enforcement` | visibility-monkeypatch |
