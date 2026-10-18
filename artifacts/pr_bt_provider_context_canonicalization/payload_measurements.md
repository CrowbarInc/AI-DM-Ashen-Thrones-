# PR-BT Provider Payload Measurements

json.dumps(..., ensure_ascii=False, default=str) character counts against saved PR-BS provider_request_attempt_generation_1.json files; live token counts copied from PR-BS model_calls/digests; no model/API calls.

| Probe | Provider chars | Live input tokens | System chars | User JSON chars |
|---|---:|---:|---:|---:|
| P1 | 110,450 | 25,208 | 12,975 | 91,859 |
| P2 | 121,438 | 27,795 | 12,975 | 102,010 |
| P3 | 110,665 | 25,233 | 12,975 | 92,100 |

## Top-Level Component Chars

| Component | P1 | P2 | P3 | Classification | Dynamic | Duplication |
|---|---:|---:|---:|---|---|---|
| `provider_input_serialized` | 110,450 | 121,438 | 110,665 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `user_payload_serialized` | 91,859 | 102,010 | 92,100 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `instructions` | 25,788 | 26,675 | 25,856 | A/E/F | MIXED_STATIC_TURN_SPECIFIC | major duplicate of system prompt and response_policy objects |
| `response_policy` | 20,630 | 21,237 | 20,913 | B/C/E | MIXED_STATIC_TURN_SPECIFIC | duplicated by top-level contract mirrors and turn_packet.response_policy |
| `system_prompt` | 12,975 | 12,975 | 12,975 | A/E | STATIC | duplicates instructions and response_policy prose |
| `turn_packet` | 10,676 | 10,640 | 10,910 | C/D/E | TURN_SPECIFIC | duplicates response_policy plus contracts already top-level |
| `mechanical_resolution` | 662 | 6,253 | 1,126 | B/C/D | TURN_SPECIFIC | provider copy still carries debug/emission fields in some turns |
| `narrative_plan` | 4,472 | 4,965 | 4,244 | B/E/G | TURN_SPECIFIC | partially duplicates mode/visibility/policy guidance |
| `context_separation_contract` | 3,509 | 3,359 | 3,437 | E | TURN_SPECIFIC | duplicates response_policy.context_separation |
| `referent_tracking` | 1,250 | 3,005 | 1,250 | B/C/D | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `decision_facing_answer_recipe` | 2,356 | 1,876 | 1,691 | A | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `interaction_continuity_contract` | 1,805 | 2,157 | 1,808 | B/E | SESSION_GROWING_BOUNDED | duplicates response_policy.interaction_continuity and turn_packet contracts |
| `scene` | 1,731 | 1,630 | 1,705 | A/B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `dialogue_social_plan` | 1,649 | 557 | 1,649 | B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `fallback_behavior` | 1,315 | 1,403 | 1,482 | B/E | TURN_SPECIFIC | duplicates response_policy.fallback_behavior and instruction prose |
| `speaker_selection` | 1,241 | 1,455 | 1,269 | A/B | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `anti_railroading_contract` | 1,451 | 1,451 | 1,451 | A/E | STATIC_POLICY_PROJECTION | duplicates response_policy.anti_railroading and instructions |
| `gm_resolution_decision` | 1,073 | 1,184 | 1,073 | C/E | TURN_SPECIFIC | partly projected by recipe and claims |
| `character` | 1,059 | 1,059 | 1,059 | B | STATIC_OR_SESSION_GROWING | not a dominant duplication or not assessed as duplicate |
| `campaign` | 1,057 | 1,057 | 1,057 | B/G | STATIC | not a dominant duplication or not assessed as duplicate |
| `scene_state_anchor_contract` | 870 | 930 | 741 | A/E | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `conversational_memory_window` | 725 | 886 | 725 | C/E | TURN_SPECIFIC | duplicated in response_policy |
| `social_context` | 175 | 779 | 175 | B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `resolution_contract` | 569 | 723 | 537 | A/C | TURN_SPECIFIC | partly projected by recipe and turn_summary |
| `social_response_structure_contract` | 628 | 623 | 634 | B/E | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `transition` | 535 | 529 | 535 | B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `referent_clause_prompt_hints` | 0 | 502 | 0 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `turn_summary` | 456 | 385 | 449 | A | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `response_type_contract` | 389 | 416 | 388 | A/E | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `narration_obligations` | 402 | 404 | 402 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `player_facing_narration_purity_contract` | 369 | 373 | 369 | A/E | STATIC_POLICY_PROJECTION | not a dominant duplication or not assessed as duplicate |
| `bounded_improvisation` | 359 | 359 | 359 | A | STATIC_POLICY_PROJECTION | not a dominant duplication or not assessed as duplicate |
| `session` | 340 | 353 | 340 | C/D | SESSION_GROWING | not a dominant duplication or not assessed as duplicate |
| `world` | 349 | 349 | 349 | B | WORLD_GROWING | not a dominant duplication or not assessed as duplicate |
| `lead_context` | 337 | 337 | 337 | B | SESSION_GROWING_BOUNDED | not a dominant duplication or not assessed as duplicate |
| `world_progression_summary` | 200 | 200 | 288 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `active_interlocutor` | 4 | 277 | 4 | B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `interlocutor_lead_context` | 270 | 273 | 270 | B | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `interaction_continuity` | 230 | 245 | 230 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `narration_visibility` | 242 | 229 | 242 | A | TURN_SPECIFIC | not a dominant duplication or not assessed as duplicate |
| `player_expression_contract` | 210 | 210 | 210 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `follow_up_pressure` | 4 | 180 | 4 | B | SESSION_GROWING_BOUNDED | not a dominant duplication or not assessed as duplicate |
| `opening_scene_realization` | 177 | 177 | 177 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `first_mention_contract` | 159 | 159 | 159 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `player_input` | 69 | 53 | 129 | A | TURN_SPECIFIC | also appears in recipe/requested_answer, turn_packet.player_text, turn_summary/mechanical_resolution |
| `opening_narration_obligations` | 101 | 101 | 101 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
| `scene_advancement` | 101 | 101 | 101 | G | CONDITIONALLY_PRESENT | not a dominant duplication or not assessed as duplicate |
