# PR-CW Context Dependency Matrix

| Surface | Classification | Handling |
|---|---|---|
| `active_interlocutor` | A - generation/continuity | Retained exactly |
| `active_topic_anchor` | F - uncertain or required | Retained exactly |
| `anti_railroading_contract` | F - uncertain or required | Retained exactly |
| `bounded_improvisation` | F - uncertain or required | Retained exactly |
| `campaign` | F - uncertain or required | Retained exactly |
| `character` | F - uncertain or required | Retained exactly |
| `clues` | F - uncertain or required | Retained exactly |
| `combat` | F - uncertain or required | Retained exactly |
| `context_separation_contract` | F - uncertain or required | Retained exactly |
| `conversational_memory_window` | F - uncertain or required | Retained exactly |
| `decision_facing_answer_recipe` | C - generation and validation | Retained exactly |
| `dialogue_social_plan` | C - generation and validation | Retained exactly |
| `discoverable_hinting` | F - uncertain or required | Retained exactly |
| `fallback_behavior` | F - uncertain or required | Retained exactly |
| `first_mention_contract` | F - uncertain or required | Retained exactly |
| `follow_up_pressure` | F - uncertain or required | Retained exactly |
| `gm_resolution_decision` | C - generation and validation | Retained exactly |
| `instructions` | F - uncertain or required | Retained exactly |
| `interaction_continuity` | F - uncertain or required | Retained exactly |
| `interaction_continuity_contract` | F - uncertain or required | Retained exactly |
| `interlocutor_lead_behavior_hints` | E - inactive/irrelevant | Omitted after eligibility checks |
| `interlocutor_lead_context` | F - uncertain or required | Retained exactly |
| `known_answer_hint` | F - uncertain or required | Retained exactly |
| `lead_context` | F - uncertain or required | Retained exactly |
| `mechanical_resolution` | D - conditional/duplicate | Compacted; authority retained separately |
| `narration_obligations` | F - uncertain or required | Retained exactly |
| `narration_temporal_provenance` | F - uncertain or required | Retained exactly |
| `narration_visibility` | C - generation and validation | Retained exactly |
| `narrative_plan` | D - conditional/duplicate | Compacted; authority retained separately |
| `opening_curated_facts` | E - inactive/irrelevant | Omitted after eligibility checks |
| `opening_inputs_are_curated` | E - inactive/irrelevant | Omitted after eligibility checks |
| `opening_narration_obligations` | E - inactive/irrelevant | Omitted after eligibility checks |
| `opening_scene_realization` | E - inactive/irrelevant | Omitted after eligibility checks |
| `opening_selector_selected_facts` | E - inactive/irrelevant | Omitted after eligibility checks |
| `opening_selector_source_used` | E - inactive/irrelevant | Omitted after eligibility checks |
| `player_expression_contract` | F - uncertain or required | Retained exactly |
| `player_facing_narration_purity_contract` | F - uncertain or required | Retained exactly |
| `player_input` | A - generation/continuity | Retained exactly |
| `recent_log` | A - generation/continuity | Retained exactly |
| `referent_clause_prompt_hints` | F - uncertain or required | Retained exactly |
| `referent_tracking` | F - uncertain or required | Retained exactly |
| `resolution_contract` | C - generation and validation | Retained exactly |
| `response_policy` | C - generation and validation | Retained exactly |
| `response_type_contract` | F - uncertain or required | Retained exactly |
| `scene` | C - generation and validation | Retained exactly |
| `scene_advancement` | E - inactive/irrelevant | Omitted after eligibility checks |
| `scene_state_anchor_contract` | F - uncertain or required | Retained exactly |
| `selected_conversational_memory` | A - generation/continuity | Retained exactly |
| `session` | F - uncertain or required | Retained exactly |
| `social_context` | F - uncertain or required | Retained exactly |
| `social_response_structure_contract` | F - uncertain or required | Retained exactly |
| `speaker_selection` | C - generation and validation | Retained exactly |
| `transition` | E - inactive/irrelevant | Omitted after eligibility checks |
| `turn_packet` | D - conditional/duplicate | Compacted; authority retained separately |
| `turn_summary` | F - uncertain or required | Retained exactly |
| `uncertainty_hint` | F - uncertain or required | Retained exactly |
| `world` | F - uncertain or required | Retained exactly |
| `world_progression_summary` | E - inactive/irrelevant | Omitted after eligibility checks |
| `world_state` | F - uncertain or required | Retained exactly |

Removed nested fields inspected in controls:

- `mechanical_resolution`: hint, requires_check
- `narrative_plan`: action_outcome, narrative_roles, required_new_information, transition_node
- `turn_packet`: debug, response_policy

Full engine state, CTIR, and deterministic validator inputs remain outside this projection. Duplicate public/resolution/debug packet branches remain in the engine; top-level scene, resolution, decision, speaker, memory, and policy retain generation constraints. Narrative-role derivation telemetry and empty outcome scaffolding are compacted. Nonempty lead, inventory, faction, NPC, and world records are retained conservatively.
