# BV13B — Remaining Imports

**Date:** 2026-06-21

**Compat barrel residual FI:** 5 (target ≤15 — **met**)

## compatibility-only (delegate verification) (1)

- `tests/test_bv13a_final_emission_text_facade_delegates.py`

## fallback wrapper users (3)

- `game/final_emission_fast_fallback_composition.py`
- `game/final_emission_scene_emit_integrity.py`
- `tests/test_diegetic_fallback_block4.py`

## formatting authority consumers (52)

- `game/acceptance_quality.py`
- `game/dialogue_social_plan.py`
- `game/emitted_speaker_signature.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_acceptance_quality.py`
- `game/final_emission_answer_shape_primacy.py`
- `game/final_emission_context_separation.py`
- `game/final_emission_fast_fallback_composition.py`
- `game/final_emission_finalize.py`
- `game/final_emission_first_mention_composition.py`
- `game/final_emission_gate_preflight_pregate_text.py`
- `game/final_emission_gate_preflight_strict_social.py`
- `game/final_emission_gate_preflight_telemetry.py`
- `game/final_emission_generic_exit.py`
- `game/final_emission_narrative_authority.py`
- `game/final_emission_non_strict_stack.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_opening_mode.py`
- `game/final_emission_passive_scene_pressure.py`
- `game/final_emission_referential_clarity.py`
- `game/final_emission_repairs.py`
- `game/final_emission_response_type.py`
- `game/final_emission_scene_facts.py`
- `game/final_emission_scene_state_anchor.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_strict_social_stack.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_text.py`
- `game/final_emission_text_legacy_semantic_repair.py`
- `game/final_emission_tone_escalation.py`
- `game/final_emission_validators.py`
- `game/final_emission_visibility_fallback.py`
- `game/interaction_continuity.py`
- `game/narrative_authenticity.py`
- `game/narrative_mode_contract.py`
- `game/opening_deterministic_fallback.py`
- `game/speaker_contract_enforcement.py`
- `game/upstream_response_repairs.py`
- `tests/helpers/gate_thin_boundary_locks.py`
- `tests/helpers/post_speaker_finalize_probe.py`
- `tests/helpers/speaker_contract_risk.py`
- `tests/helpers/speaker_gate_order.py`
- `tests/test_acceptance_quality.py`
- `tests/test_bv13a_final_emission_text_facade_delegates.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_boundary_no_semantic_repair.py`
- `tests/test_final_emission_opening_accept_debug.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_narrative_authority_rules.py`
- `tests/test_ownership_registry.py`
- `tests/test_prompt_context.py`
- `tests/test_referential_clarity_player_coref.py`

## legacy/test-only (3)

- `game/final_emission_text.py`
- `tests/test_bv13a_final_emission_text_facade_delegates.py`
- `tests/test_final_emission_visibility.py`

## other compat (1)

- `tests/helpers/gate_thin_boundary_locks.py`

## policy authority consumers (8)

- `game/final_emission_answer_shape_primacy.py`
- `game/final_emission_referential_clarity.py`
- `game/final_emission_text.py`
- `game/final_emission_validators.py`
- `game/interaction_continuity.py`
- `game/narrative_mode_contract.py`
- `game/response_policy_contracts.py`
- `tests/test_bv13a_final_emission_text_facade_delegates.py`

## Migration candidates (BV13C)

| Consumer | Recommendation |
| --- | --- |
| Fallback wrapper users (3 prod + 1 test) | Keep on compat until diegetic facade extraction |
| `test_bv13a_*` | Keep — compat delegate verification |
| Governance string markers in `gate_thin_boundary_locks` | Update only when BN9/BV13C guards land |
