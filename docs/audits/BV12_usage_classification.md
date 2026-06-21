# BV12 — Usage Classification

**Date:** 2026-06-21  
**Method:** Heuristic domain tagging from file path + imported symbols  

---

## Domain totals

| Domain | Consumer files (deduped) | Primary symbols |
| --- | --- | --- |
| replay acceptance | 53 | final_emission_meta_from_output |
| gate orchestration | 30 | apply_final_emission_gate_consumer |
| fallback testing | 6 | both bridge symbols |
| gate validation | 4 | apply_final_emission_gate_consumer |
| observability testing | 3 | final_emission_meta_from_output |
| replay projection | 1 | final_emission_meta_from_output |

## Classification notes

- **replay acceptance** — integration/regression suites asserting FEM wiring after gate output (largest bucket).
- **gate orchestration** — suites that run full `finalize_player_facing_emission` via consumer helper.
- **fallback testing** — opening/diegetic/fallback suites; frequently **dual-bridge** (gate + FEM read).
- **gate validation** — owner-adjacent gate suites (`test_final_emission_gate_*`, boundary convergence).
- **observability testing** — dead-turn / telemetry confidence reads.
- **replay projection** — golden-replay-adjacent seams (small; most projection uses `golden_replay_projection`).

## Sample consumers by domain

### replay acceptance

- `tests/helpers/behavioral_gauntlet_eval.py`
- `tests/helpers/emission_smoke_assertions.py`
- `tests/helpers/transcript_snapshots.py`
- `tests/test_anti_railroading.py`
- `tests/test_anti_railroading_retry_alignment.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_api_narration_path_selection.py`
- `tests/test_block_s_speaker_local_rebind_equivalence.py`
- … and 45 more

### gate orchestration

- `tests/helpers/emission_smoke_assertions.py`
- `tests/helpers/strict_social_harness.py`
- `tests/helpers/turn_pipeline_http_fixtures.py`
- `tests/test_answer_completeness_rules.py`
- `tests/test_anti_railroading.py`
- `tests/test_anti_railroading_transcript_regressions.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_bv3a_observe_referential_clarity_repair.py`
- … and 22 more

### fallback testing

- `tests/test_diegetic_fallback_narration.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_lead_npc_payoff_and_fallback.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_upstream_fast_fallback_block_l.py`

### gate validation

- `tests/test_dialogue_plan_final_emission_gate.py`
- `tests/test_final_emission_answer_exposition_plan_convergence.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_scene_integrity.py`

### observability testing

- `tests/test_dead_turn_detection.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/test_observational_telemetry_confidence.py`

### replay projection

- `tests/test_golden_replay_direct_seam.py`

