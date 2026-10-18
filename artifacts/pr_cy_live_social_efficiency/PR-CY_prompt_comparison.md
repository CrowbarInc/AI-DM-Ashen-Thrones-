# PR-CY Prompt Comparison

Deterministic reconstruction only; no provider calls.

| Payload | Reduced-context eligible | Response envelope | Serialized prompt bytes | Rough estimated tokens | Payload hash |
|---|---:|---|---:|---:|---|
| Full context | None | narration_only | 126926 | 31732 | `6018dc2fed20672b8aa4e26b4c8e4ec94bd7a79b9acc3d8ae4d11a4cbcfb9615` |
| Reduced context | True | narration_only | 116087 | 29022 | `faf834cfa43b7b7050c7e06100d5bc6feb7e688ef81ca60456c1d076230f0aae` |

Byte reduction: 10839 bytes.

Retained top-level context: `active_interlocutor, active_topic_anchor, anti_railroading_contract, bounded_improvisation, campaign, character, clues, combat, context_separation_contract, conversational_memory_window, decision_facing_answer_recipe, dialogue_social_plan, discoverable_hinting, fallback_behavior, first_mention_contract, follow_up_pressure, gm_resolution_decision, instructions, interaction_continuity, interaction_continuity_contract, interlocutor_lead_context, known_answer_hint, lead_context, mechanical_resolution, narration_obligations, narration_visibility, narrative_plan, player_expression_contract, player_facing_narration_purity_contract, player_input, recent_log, referent_clause_prompt_hints, referent_tracking, resolution_contract, response_policy, scene, scene_state_anchor_contract, selected_conversational_memory, session, social_context, social_response_structure_contract, speaker_selection, turn_packet, turn_summary, uncertainty_hint, world, world_state`.

Omitted top-level context: `interlocutor_lead_behavior_hints, opening_curated_facts, opening_inputs_are_curated, opening_narration_obligations, opening_scene_realization, opening_selector_selected_facts, opening_selector_source_used, scene_advancement, transition, world_progression_summary`.

Changed retained context sizes:

```json
{
  "mechanical_resolution": {
    "full_bytes": 3091,
    "reduced_bytes": 2685,
    "delta_bytes": -406
  },
  "narrative_plan": {
    "full_bytes": 5405,
    "reduced_bytes": 2626,
    "delta_bytes": -2779
  },
  "turn_packet": {
    "full_bytes": 10815,
    "reduced_bytes": 4422,
    "delta_bytes": -6393
  }
}
```
