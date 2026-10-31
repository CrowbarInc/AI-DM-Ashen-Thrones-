# 04 — Opening Prompt Inventory

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

Current production messages captured immediately before the synthetic SDK dispatch
for frontier_gate and market_quarter. Historical 26593-token input is measured
provider evidence; current sizes below are reconstruction character counts and
chars/4 estimates, not a replay of original provider tokens. No original full
request was retained in the October 28 package.

A required: opening/scene/character/campaign identity, structured response and
declaration contracts, authorized facts, visibility/hidden protection, rules,
state-authority and mechanical resolution. B conditional: NPC/social/combat/clue,
lead and memory context when relevant; retain because opening can include NPCs.
E uncertain: overlapping response_policy, decision, recipe, plan, world views,
turn packet/session summaries. Large size alone supplies no removal authority.
The system includes response contract/structured instructions; user.instructions
and response_policy supply rules/authority; scene/opening realization and clue
views supply visible and protected knowledge; character supplies identity; world
and world_state carry distinct views; decision/recipe/plan convey claims and
completion requirements. Inventory is top-level disjoint serialization size;
JSON separators/outer keys add overhead. Do not sum overlapping nested views as
independent additions to the system/user total.

C exact repeated-string candidates are enumerated with both source paths and
lengths in prompt_inventory.json. Their location may convey independent validation
or authority semantics. No major component was established safe to remove. D
unused: none proven. Exact duplicate values do not prove redundant instructions.
No reductions proposed or implemented. Thus no removal loses an alternative
authority source, and no fabricated removal evidence is supplied.

Before/after: system 9568/9568 chars for both fixtures; frontier user
102796/102796; market user 79071/79071. Reduction 0 chars / 0 estimated tokens.
AST comparisons prove build_messages, context collection, parser and envelope
selection plus all module-level contract assignments unchanged. Prompt-integrity
matrix preserves scene, character, NPC, visible facts, hidden protection,
declarations, gameplay authority and opening instructions for both scene fixtures.
This is structural preservation evidence, not a semantic model test.

## minimal

System 9568 chars; user 79071 chars.

| Component | Chars | Estimated tokens | Class |
|---|---:|---:|---|
| response_policy | 20698 | 5175 | E |
| instructions | 14225 | 3557 | A |
| turn_packet | 8647 | 2162 | E |
| narrative_plan | 6171 | 1543 | E |
| gm_resolution_decision | 4791 | 1198 | A |
| decision_facing_answer_recipe | 3641 | 911 | E |
| opening_scene_realization | 2295 | 574 | A |
| dialogue_social_plan | 2245 | 562 | E |
| scene | 2120 | 530 | A |
| mechanical_resolution | 1409 | 353 | A |
| referent_tracking | 1250 | 313 | A |
| speaker_selection | 1142 | 286 | A |
| character | 1059 | 265 | A |
| campaign | 1057 | 265 | A |
| scene_state_anchor_contract | 833 | 209 | A |
| transition | 817 | 205 | A |
| opening_narration_obligations | 451 | 113 | A |
| narration_obligations | 401 | 101 | A |
| response_type_contract | 390 | 98 | A |
| resolution_contract | 364 | 91 | A |
| bounded_improvisation | 359 | 90 | A |
| turn_summary | 358 | 90 | E |
| world | 349 | 88 | E |
| session | 341 | 86 | E |
| lead_context | 337 | 85 | B |
| interlocutor_lead_context | 270 | 68 | B |
| narration_visibility | 266 | 67 | A |
| interaction_continuity | 230 | 58 | B |
| player_expression_contract | 210 | 53 | A |
| world_progression_summary | 200 | 50 | A |
| social_context | 175 | 44 | B |
| first_mention_contract | 159 | 40 | A |
| scene_advancement | 99 | 25 | A |
| opening_selector_selected_facts | 98 | 25 | A |
| opening_curated_facts | 98 | 25 | A |
| active_topic_anchor | 75 | 19 | B |
| clues | 63 | 16 | B |
| world_state | 51 | 13 | E |
| opening_selector_source_used | 20 | 5 | A |
| combat | 20 | 5 | B |
| active_interlocutor | 4 | 1 | B |
| follow_up_pressure | 4 | 1 | B |
| uncertainty_hint | 4 | 1 | A |
| opening_inputs_are_curated | 4 | 1 | A |
| discoverable_hinting | 4 | 1 | B |
| recent_log | 2 | 1 | B |
| selected_conversational_memory | 2 | 1 | B |
| player_input | 2 | 1 | A |
| interlocutor_lead_behavior_hints | 2 | 1 | B |

## declarations

System 9568 chars; user 102796 chars.

| Component | Chars | Estimated tokens | Class |
|---|---:|---:|---|
| response_policy | 21636 | 5409 | E |
| instructions | 14433 | 3609 | A |
| gm_resolution_decision | 10714 | 2679 | A |
| scene | 10304 | 2576 | A |
| turn_packet | 8654 | 2164 | E |
| decision_facing_answer_recipe | 7244 | 1811 | E |
| narrative_plan | 6679 | 1670 | E |
| opening_scene_realization | 3538 | 885 | A |
| referent_tracking | 2650 | 663 | A |
| dialogue_social_plan | 2245 | 562 | E |
| mechanical_resolution | 1406 | 352 | A |
| speaker_selection | 1142 | 286 | A |
| character | 1059 | 265 | A |
| campaign | 1057 | 265 | A |
| scene_state_anchor_contract | 995 | 249 | A |
| transition | 814 | 204 | A |
| narration_visibility | 759 | 190 | A |
| opening_selector_selected_facts | 582 | 146 | A |
| opening_curated_facts | 582 | 146 | A |
| opening_narration_obligations | 451 | 113 | A |
| narration_obligations | 401 | 101 | A |
| response_type_contract | 390 | 98 | A |
| resolution_contract | 364 | 91 | A |
| bounded_improvisation | 359 | 90 | A |
| turn_summary | 358 | 90 | E |
| world | 349 | 88 | E |
| session | 340 | 85 | E |
| lead_context | 337 | 85 | B |
| interlocutor_lead_context | 270 | 68 | B |
| interaction_continuity | 230 | 58 | B |
| player_expression_contract | 210 | 53 | A |
| world_progression_summary | 200 | 50 | A |
| social_context | 175 | 44 | B |
| first_mention_contract | 159 | 40 | A |
| scene_advancement | 99 | 25 | A |
| active_topic_anchor | 75 | 19 | B |
| clues | 63 | 16 | B |
| world_state | 51 | 13 | E |
| opening_selector_source_used | 20 | 5 | A |
| combat | 20 | 5 | B |
| active_interlocutor | 4 | 1 | B |
| follow_up_pressure | 4 | 1 | B |
| uncertainty_hint | 4 | 1 | A |
| opening_inputs_are_curated | 4 | 1 | A |
| discoverable_hinting | 4 | 1 | B |
| recent_log | 2 | 1 | B |
| selected_conversational_memory | 2 | 1 | B |
| player_input | 2 | 1 | A |
| interlocutor_lead_behavior_hints | 2 | 1 | B |
