# BV13 — Final Emission Text Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only — every direct importer of `game.final_emission_text`
**Method:** `python tools/bv13_final_emission_text_discovery.py` + BU CSV reconciliation

---

## Hub baseline (current)

| Module | BU fan-in | AST direct importers | Exported symbols | LOC | Fan-out |
| --- | --- | --- | --- | --- | --- |
| `game.final_emission_text` | **52** | 52 | 20 | 465 | 4 (`diegetic_fallback_narration` only production dep) |

**BV12 context:** Smoke bridge cluster retired; `final_emission_text` is the largest remaining **production-core** FI node (tied with `social_exchange_emission` at 52).

## Importer split

| Layer | Count | Share |
| --- | --- | --- |
| Production (`game/`) | 39 | 75% |
| Tests (`tests/`) | 13 | 25% |

## Summary by subsystem

| Subsystem | Importers | Primary symbol |
| --- | --- | --- |
| final emission pipeline | 24 | `_normalize_text` |
| final emission gate | 7 | `_normalize_text` |
| narrative/social | 6 | `_normalize_text` |
| fallback | 4 | `_normalize_text` |
| integration/regression | 4 | `_normalize_text` |
| production runtime | 3 | `_normalize_text` |
| speaker helpers | 3 | `_normalize_text` |
| ownership governance | 1 | `emission_text` |

## Full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
| --- | --- | --- | --- |
| `game/acceptance_quality.py` | production runtime | `_normalize_text` | normalize-primitive |
| `game/dialogue_social_plan.py` | narrative/social | `_normalize_text` | normalize-primitive |
| `game/emitted_speaker_signature.py` | narrative/social | `_normalize_text` | normalize-primitive |
| `game/fallback_provenance_debug.py` | fallback | `_normalize_text`, `_sanitize_output_text` | formatting-sanitize |
| `game/final_emission_acceptance_quality.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_answer_shape_primacy.py` | final emission pipeline | `_ACTION_RESULT_PATTERNS`, `_ANSWER_DIRECT_PATTERNS`, `_normalize_text` | validator-pattern |
| `game/final_emission_context_separation.py` | final emission pipeline | `_normalize_text_preserve_paragraphs` | normalize-primitive |
| `game/final_emission_fast_fallback_composition.py` | final emission pipeline | `_global_narrative_fallback_stock_line`, `_normalize_text` | fallback-content-bridge |
| `game/final_emission_finalize.py` | final emission pipeline | `_normalize_text`, `_sanitize_output_text` | formatting-sanitize |
| `game/final_emission_first_mention_composition.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_gate.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `game/final_emission_gate_preflight_pregate_text.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `game/final_emission_gate_preflight_strict_social.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `game/final_emission_gate_preflight_telemetry.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `game/final_emission_generic_exit.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_narrative_authority.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_non_strict_stack.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_opening_fallback.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_opening_mode.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_passive_scene_pressure.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_referential_clarity.py` | final emission pipeline | `_ANSWER_DIRECT_PATTERNS`, `_normalize_text` | validator-pattern |
| `game/final_emission_repairs.py` | final emission pipeline | `_normalize_terminal_punctuation`, `_normalize_text` | formatting-punctuation |
| `game/final_emission_response_type.py` | final emission pipeline | `_normalize_text`, `_normalize_text_preserve_paragraphs` | normalize-primitive |
| `game/final_emission_scene_emit_integrity.py` | final emission pipeline | `_global_narrative_fallback_stock_line` | fallback-content-bridge |
| `game/final_emission_scene_facts.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_scene_state_anchor.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_sealed_fallback.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_strict_social_stack.py` | final emission pipeline | `_normalize_text`, `_normalize_text_preserve_paragraphs` | normalize-primitive |
| `game/final_emission_terminal_pipeline.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_tone_escalation.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/final_emission_validators.py` | final emission pipeline | `_ACTION_RESULT_PATTERNS`, `_ACTION_STOPWORDS`, `_AGENCY_SUBSTITUTE_PATTERNS`, `_ANSWER_DIRECT_PATTERNS`, `_ANSWER_FILLER_PATTERNS`, `_normalize_terminal_punctuation`, `_normalize_text` | validator-pattern |
| `game/final_emission_visibility_fallback.py` | final emission pipeline | `_normalize_text` | normalize-primitive |
| `game/interaction_continuity.py` | narrative/social | `_RESPONSE_TYPE_VALUES`, `_normalize_text` | policy-constant |
| `game/narrative_authenticity.py` | narrative/social | `_normalize_terminal_punctuation`, `_normalize_text` | formatting-punctuation |
| `game/narrative_mode_contract.py` | narrative/social | `_ACTION_RESULT_PATTERNS`, `_ANSWER_FILLER_PATTERNS`, `_normalize_text` | validator-pattern |
| `game/opening_deterministic_fallback.py` | fallback | `_normalize_text` | normalize-primitive |
| `game/response_policy_contracts.py` | production runtime | `_RESPONSE_TYPE_VALUES` | policy-constant |
| `game/speaker_contract_enforcement.py` | narrative/social | `_normalize_text` | normalize-primitive |
| `game/upstream_response_repairs.py` | production runtime | `_capitalize_sentence_fragment`, `_normalize_terminal_punctuation`, `_normalize_text` | formatting-punctuation |
| `tests/helpers/post_speaker_finalize_probe.py` | speaker helpers | `_normalize_text` | normalize-primitive |
| `tests/helpers/speaker_contract_risk.py` | speaker helpers | `_normalize_text` | normalize-primitive |
| `tests/helpers/speaker_gate_order.py` | speaker helpers | `_normalize_text` | normalize-primitive |
| `tests/test_acceptance_quality.py` | integration/regression | `_normalize_text` | normalize-primitive |
| `tests/test_diegetic_fallback_block4.py` | fallback | `_global_narrative_fallback_stock_line` | fallback-content-bridge |
| `tests/test_final_emission_boundary_convergence.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | final emission gate | `_normalize_text` | normalize-primitive |
| `tests/test_final_emission_opening_accept_debug.py` | fallback | `_normalize_text` | normalize-primitive |
| `tests/test_final_emission_visibility.py` | final emission gate | `_decompress_overpacked_sentences`, `_normalize_text`, `_repair_fragmentary_participial_splits` | legacy-semantic-repair |
| `tests/test_narrative_authority_rules.py` | integration/regression | `_normalize_text` | normalize-primitive |
| `tests/test_ownership_registry.py` | ownership governance | `emission_text (module)` | ownership-governance |
| `tests/test_prompt_context.py` | integration/regression | `_normalize_text` | normalize-primitive |
| `tests/test_referential_clarity_player_coref.py` | integration/regression | `_normalize_text` | normalize-primitive |
