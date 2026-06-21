# BV16C — Owner Mapping

**Date:** 2026-06-21

Monkeypatch and test seam targets must use the **canonical owner module**, not ``terminal_pipeline`` namespace bindings.

| Concern | Symbol | Canonical owner module | Test import alias |
| --- | --- | --- | --- |
| visibility | `apply_visibility_enforcement` | `game.final_emission_visibility_fallback` | `visibility_fallback` |
| N4 | `apply_acceptance_quality_n4_floor_seam` | `game.final_emission_acceptance_quality` | `acceptance_quality` |
| IC step | `apply_interaction_continuity_emission_step` | `game.interaction_continuity` | `interaction_continuity` |
| IC attach | `attach_interaction_continuity_validation` | `game.interaction_continuity` | `interaction_continuity` |
| opening | `reassert_scene_opening_accepted_candidate` | `game.final_emission_opening_fallback` | `opening_fallback` |
| repairs / fallback behavior | `_apply_fallback_behavior_layer` | `game.final_emission_repairs` | `emission_repairs` |
| terminal orchestration | `run_gate_terminal_enforcement_pipeline` | `game.final_emission_terminal_pipeline` | `terminal_pipeline` |
| terminal orchestration | `_apply_referent_clarity_pre_finalize` | `game.final_emission_terminal_pipeline` | `terminal_pipeline` |
| realization helper | `apply_strict_social_emergency_fallback_patch` | `game.final_emission_terminal_pipeline` | `terminal_pipeline` |

## Governance

Forbidden in tests (enforced by ``test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance``):

- `monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", ...)`
- `monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam", ...)`
- `monkeypatch.setattr(terminal_pipeline, "attach_interaction_continuity_validation", ...)`
- `monkeypatch.setattr(terminal_pipeline, "apply_interaction_continuity_emission_step", ...)`
- `monkeypatch.setattr(terminal_pipeline, "_apply_fallback_behavior_layer", ...)`

Allowed on terminal pipeline: orchestration symbols only (`run_gate_terminal_enforcement_pipeline`, `_apply_referent_clarity_pre_finalize`, source-order governance tests).
