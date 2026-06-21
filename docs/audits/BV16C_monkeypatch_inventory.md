# BV16C — Monkeypatch Inventory

**Date:** 2026-06-21
**Scope:** Post-migration owner-module monkeypatch consumers

---

## Summary

| Metric | Pre-BV16C | Post-BV16C |
| --- | --- | --- |
| Terminal pipeline AST importers | 26 | **9** |
| Stale terminal delegate patches | 16+ | **0** |

## Classification

| Class | Owner alias | Symbol | Consumers |
| --- | --- | --- | --- |
| **visibility** | `visibility_fallback` | `apply_visibility_enforcement` | 15 |
| **N4** | `acceptance_quality` | `apply_acceptance_quality_n4_floor_seam` | 2 |
| **IC** | `interaction_continuity` | `apply_interaction_continuity_emission_step` | 4 |
| **repairs** | `emission_repairs` | `_apply_fallback_behavior_layer` | 3 |
| opening | — | — | 0 |
| **terminal orchestration** | `terminal_pipeline` | `_apply_referent_clarity_pre_finalize` | 2 |

## Stale terminal_pipeline delegate patches

**None** — all delegate monkeypatches routed to owner modules.

## Full consumer table

| File | Class | Owner | Symbol |
| --- | --- | --- | --- |
| `tests/helpers/post_speaker_finalize_probe.py` | IC | `interaction_continuity` | `apply_interaction_continuity_emission_step` |
| `tests/test_fallback_behavior_gate.py` | IC | `interaction_continuity` | `apply_interaction_continuity_emission_step` |
| `tests/test_final_emission_gate_n4.py` | IC | `interaction_continuity` | `attach_interaction_continuity_validation` |
| `tests/test_interaction_continuity_repair.py` | IC | `interaction_continuity` | `apply_interaction_continuity_emission_step` |
| `tests/helpers/post_speaker_finalize_probe.py` | N4 | `acceptance_quality` | `apply_acceptance_quality_n4_floor_seam` |
| `tests/test_final_emission_gate_selector_snapshots.py` | N4 | `acceptance_quality` | `apply_acceptance_quality_n4_floor_seam` |
| `tests/helpers/post_speaker_finalize_probe.py` | repairs | `emission_repairs` | `_apply_fallback_behavior_layer` |
| `tests/test_fallback_behavior_gate.py` | repairs | `emission_repairs` | `_apply_fallback_behavior_layer` |
| `tests/test_final_emission_repairs.py` | repairs | `emission_repairs` | `_apply_fallback_behavior_layer` |
| `tests/helpers/post_speaker_finalize_probe.py` | terminal orchestration | `terminal_pipeline` | `_apply_referent_clarity_pre_finalize` |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | terminal orchestration | `terminal_pipeline` | `_apply_referent_clarity_pre_finalize` |
| `tests/helpers/post_speaker_finalize_probe.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/helpers/terminal_owner_test_seams.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_anti_railroading.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_anti_railroading_transcript_regressions.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_context_separation.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_final_emission_boundary_convergence.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_final_emission_gate_orchestration_order.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_final_emission_gate_selector_snapshots.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_narration_transcript_regressions.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_ownership_registry.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_player_facing_narration_purity.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_prompt_context.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_social_exchange_emission.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_speaker_contract_enforcement.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
| `tests/test_tone_escalation_rules.py` | visibility | `visibility_fallback` | `apply_visibility_enforcement` |
