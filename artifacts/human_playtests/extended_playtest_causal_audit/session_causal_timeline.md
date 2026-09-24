# Session causal timeline

Source: `artifacts/human_playtests/20260923_post_mixed_action_repair_extended_playtest/`.
Session `ba70eb525862575033539357`. Scene stays `frontier_gate`. `current_date` stays `Day 1`.
Log index is the turn id below. Session `time_pressure` after each entry is `log_index + 1`.
Raw model wire bodies were not retained. `last_answer` before each turn is `unavailable` (no pre-turn snapshot). Values below are the surviving post-run topic entry when this turn is the last writer, otherwise the later consumer that preserved the text.

## Turn 0 — opening

| Field | Value |
| --- | --- |
| Turn | 0 |
| Exact player input | *(empty)* |
| Exact GM output | Rain spatters against the soot-dark stone that frames the eastern gate of Cinderwatch, where frayed banners flap wearily on their lines. The muddy approach is clogged with a jostling crowd: refugees draped in threadbare cloaks, creaking wagons overloaded with belongings, and foot traffic pushing toward the guarded choke. Nearby, a tavern runner shouts over the noise, hawking hot stew and whispered rumors for coin. Watching the gate with keen eyes, a figure garbed in threadbare clothes stands unnervingly still, their gaze flicking from the waiting crowd to the gate itself more often than to the queue. Off to one side, a solid notice board displays official proclamations—new taxes, curfew rules etched in bold, and a stark warning about a patrol gone missing in the muddy outskirts. A gate serjeant manages the crowd with hard discipline, their vigilant presence lending weight to the uneasy atmosphere that presses on the assembled travelers and locals. |
| Parsed kind | `scene_opening` |
| Action ID | `campaign_start_opening_scene` |
| Segmentation | unavailable |
| Route | `exploration` (`source_route`) |
| Routed owner | scene opening |
| Route reason | `scene_opening_requires_opening_response` |
| Target | `frontier_gate` |
| Addressed NPC | none |
| Address source | unavailable |
| Question dimension | unavailable |
| Resolution | opening narration. `final_emitted_source`: `opening_deterministic_fallback` |
| State changes | arrived at `frontier_gate`; new scene context |
| Topic changes | none |
| Lead/clue changes | none |
| Transition | false |
| Model/realization evidence | `gpt-4.1-mini`, `primary_turn`. Raw body unavailable. `narrative_authority_failed`: false |
| Integrity result | candidate passed; `fallback_family_used`: `scene_opening` |
| Fallback/repair | opening fallback family |
| `last_answer` before | unavailable |
| `last_answer` after | none on this entry |
| Other persisted context | `time_pressure` 1. Clues and leads empty |

Classification: correct. Wording tracks authored opening seeds (banners, crowd, runner shout, notice board, still figure, gate discipline).

## Turn 1 — heraldry

| Field | Value |
| --- | --- |
| Turn | 1 |
| Exact player input | `I look to the banners as I enter the Eastern Gate; can I make out the heraldry?` |
| Exact GM output | `You look again. Nothing new resolves into evidence. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.` |
| Parsed kind | `investigate` |
| Action ID | `i_look_to_the_banners_as_i_enter_the_eas` |
| Segmentation | whole input stored as `adjudication_question_text`. `embedded_adjudication.category`: `action_feasibility_query` |
| Route | `mixed` |
| Routed owner | referenced-surface inspection |
| Route reason | unavailable (`intent_route_debug` absent) |
| Target | empty. `referenced_surface_authority`: `untargeted` |
| Addressed NPC | none |
| Address source | none |
| Question dimension | unavailable |
| Resolution | hint: looked or investigated without a grounded discoverable target. `final_emitted_source`: `global_scene_fallback` |
| State changes | `{}`. Action id later present in `searched_targets` |
| Topic changes | creates `topic:banner_eastern_enter` (`__scene__`, `last_turn` 2) |
| Lead/clue changes | none. `resolved_interactables` stays empty |
| Transition | false |
| Model/realization evidence | `strict_social`, escalated. Raw body unavailable. Surviving `last_answer` is a banner paragraph that was not shown |
| Integrity result | `candidate_validation_passed`: false. Coercion: `suppressed_non_social_narration:exploration_resolution_kind`. `narrative_authority_failed`: false |
| Fallback/repair | untargeted inspection line from `visible_facts[0]` |
| `last_answer` before | unavailable |
| `last_answer` after | `Above the eastern gate of Cinderwatch, frayed banners flap weakly in the rain. The worn cloth is too tattered and soaked to make out clear heraldry or recognizable symbols from your position amidst the crowd. Some faint traces of color and pattern are visible, but nothing definitive enough to identify a house or faction crest. The banners likely once bore the marks of local authorities or nobles, but years of wear and neglect have reduced them to weather-beaten shreds.` |
| Other persisted context | `time_pressure` 2 |

## Turn 2 — time of day

| Field | Value |
| --- | --- |
| Turn | 2 |
| Exact player input | `Looking to the sky, can I make out the time of day despite the rain?` |
| Exact GM output | same notice-board sentence as turn 1 |
| Parsed kind | `investigate` |
| Action ID | `looking_to_the_sky_can_i_make_out_the_ti` |
| Segmentation | whole input as `adjudication_question_text`. Category `action_feasibility_query` |
| Route | `mixed` |
| Routed owner | referenced-surface inspection |
| Route reason | unavailable |
| Target | empty. `referenced_surface_authority`: `untargeted` |
| Addressed NPC | none |
| Address source | none |
| Question dimension | unavailable |
| Resolution | same untargeted hint. `final_emitted_source`: `anti_reset_local_continuation_fallback` |
| State changes | `{}`. Action id later in `searched_targets` |
| Topic changes | topic key `topic:despite_look_make` is minted from this wording. Its final `last_answer` was overwritten on turn 3 |
| Lead/clue changes | none |
| Transition | false |
| Model/realization evidence | `primary_turn`. Raw body unavailable. Player-facing line is the untargeted template, not a time answer |
| Integrity result | `candidate_validation_passed`: false. `narrative_authority_failed`: false. `coercion_reason`: `strict_social_inactive` |
| Fallback/repair | same untargeted surroundings clause (`visible_facts[0]`) |
| `last_answer` before | unavailable |
| `last_answer` after | overwritten. Final value on `topic:despite_look_make` is turn 3's curfew paragraph |
| Other persisted context | `time_pressure` 3. `current_date` still `Day 1`. `world_state.clocks` not a time of day |

## Turn 3 — curfew notice

| Field | Value |
| --- | --- |
| Turn | 3 |
| Exact player input | `I step toward the notice board, particularly interested in the curfew rules. What do they say?` |
| Exact GM output | `The notice board spells out that the new curfew requires all civilians to be off the streets by dusk until dawn, a strict measure to curb recent unrest and bandit activity. Violators face fines or detainment until morning. This rule accompanies freshly imposed taxes and a posted…` |
| Parsed kind | unavailable (key absent) |
| Action ID | unavailable |
| Segmentation | unavailable |
| Route | `exploration` |
| Routed owner | none. `intent_classification.labels`: `["downtime"]`. Contract: `neutral_narration` / `no_stricter_authoritative_contract` |
| Route reason | unavailable |
| Target | notice board not bound. `referenced_surface_*` absent. `resolved_interactables` stays `[]` |
| Addressed NPC | none |
| Address source | none |
| Question dimension | unavailable |
| Resolution | thin resolution: `world_tick_events` and `emission_debug` only. `final_emitted_source`: `anti_reset_local_continuation_fallback` |
| State changes | unavailable on the resolution object. No clue added. Patrol clue `notice_patrol_route` not revealed |
| Topic changes | writes into existing `topic:despite_look_make` (`__scene__` `repeat_count` 2, `last_turn` 4, `last_player_input` is this notice question) |
| Lead/clue changes | none |
| Transition | unavailable / no scene change |
| Model/realization evidence | `primary_turn`. Shown text is shorter than the stored `last_answer`, which also adds "a posted warning about a missing patrol last seen heading northwest" and a gate serjeant enforcing the edicts |
| Integrity result | `candidate_validation_passed`: false. `answer_completeness_failed`: `direct_answer_not_frontloaded`, not repaired. `narrative_authority_failed`: false. Invented-outcome flags false. Exposition plan missing |
| Fallback/repair | none of the prepared "no direct answer" line was emitted |
| `last_answer` before | unavailable (sky topic existed; its previous text was replaced) |
| `last_answer` after | `The notice board spells out that the new curfew requires all civilians to be off the streets by dusk until dawn, a strict measure to curb recent unrest and bandit activity. Violators face fines or detainment until morning. This rule accompanies freshly imposed taxes and a posted warning about a missing patrol last seen heading northwest. A gate serjeant nearby keeps a watchful eye to enforce these edicts amid the crowd's murmur.` |
| Other persisted context | `time_pressure` 4 |

## Turn 4 — anyone near the board

| Field | Value |
| --- | --- |
| Turn | 4 |
| Exact player input | `I'll ask anyone near the board, "Do you have any idea how many hours until dusk?"` |
| Exact GM output | `The guard says, "I do not know enough to answer that."` |
| Parsed kind | `question` |
| Action ID | `question_anyone_near_the_board_do_you_ha` |
| Segmentation | declared: `I'll ask anyone near the board,` / spoken: `Do you have any idea how many hours until dusk?` |
| Route | `social`. `canonical_entry_path`: `social` |
| Routed owner | social exchange, open solicitation |
| Route reason | `open_social_solicitation` |
| Target | unresolved. `social.target_resolved`: false. `target_candidate_id`: slug of the sentence. `target_candidate_valid`: false |
| Addressed NPC | none (`npc_id` null, `npc_name` null) |
| Address source | `target_source`: `none`. `target_reason`: `no addressable target resolved` |
| Question dimension | stored topic uses `quantity` |
| Resolution | `reply_kind`: `reaction`. Hint: no matching NPC; narrate no clear target. `final_emitted_source`: `anti_reset_local_continuation_fallback` |
| State changes | `{}`. No NPC runtime row. No interlocutor |
| Topic changes | `topic:anyone_board_dusk`, speaker `__scene__` |
| Lead/clue changes | lead landing arrays empty |
| Transition | false |
| Model/realization evidence | `retry_escalation`, attempt 1. Raw body unavailable |
| Integrity result | candidate failed. Completeness: `direct_answer_not_frontloaded`, not repaired. `narrative_authority_failed`: false |
| Fallback/repair | `fallback_kind`: `retry_escape_hatch`. `final_route`: `forced_retry_fallback`. `retry_exhausted`: true. Reason: `question_rule:social_exchange_first_sentence_not_speaker_grounded`. `prepared_answer_fallback_text` equals the player-facing line |
| `last_answer` before | unavailable |
| `last_answer` after | a quantity template about the missing-patrol notice and "threadbare watchers and refugees…", not the guard line. Not shown |
| Other persisted context | `time_pressure` 5. `current_interlocutor` is not set by this turn |

## Turn 5 — curfew cause, unaddressed "you"

| Field | Value |
| --- | --- |
| Turn | 5 |
| Exact player input | `"Do you know what incident caused the curfew? I can't imagine bandits easily raiding a gated settlement."` |
| Exact GM output | `Tavern Runner mutters, "Word is, the tavern runner shakes their head with a shrug, saying, I don’t have the details on what exactly sparked the curfew. Bandits getting past these gates? That’s not the usual story around here. You might want to ask the guard captain—he keeps a closer eye on that kind of trouble…"` |
| Parsed kind | `question` |
| Action ID | `question_tavern_runner` |
| Segmentation | spoken text is the quote without wrapping quotes |
| Route | `dialogue` / `routed_to`: `social_exchange` |
| Routed owner | social exchange |
| Route reason | `no_addressable_target`. `routed_via_dialogue_lock`: true |
| Target | `tavern_runner` |
| Addressed NPC | `tavern_runner` |
| Address source | `dialogue_target_resolution`. Social `target_source`: `explicit_target`. Contract `interlocutor_status`: `none`, `continuity_status`: `broken`, `reply_owner_actor_id`: null |
| Question dimension | `general` |
| Resolution | `reply_kind`: `refusal`. `topic_revealed`: null. Hint: no new information; do not invent facts. Escalation level 1, vague answer allowed. `final_emitted_source`: `normalized_social_candidate`. `speaks_authoritatively_for_scene`: false |
| State changes | `{}`. `npc_runtime.tavern_runner` exists by end of session with empty `known_topics` / `revealed_topics` |
| Topic changes | starts `topic:bandit_cant_caus` (overwritten on turn 6) |
| Lead/clue changes | canonical registry empty. Later `recent_contextual_leads` includes `you might want to ask the guard captain—he` at `last_turn` 6 |
| Transition | false |
| Model/realization evidence | `strict_social`. Turn 6's `social_answer_retry_anchor_text` preserves this turn's model paragraph through "he keeps a closer eye on that kind of trouble…" |
| Integrity result | candidate passed. Completeness failed: `missing_concrete_payload`, not repaired. `narrative_authority_failed`: false. Prepared refusal `Tavern Runner grimaces. "Not something I can say here."` was not emitted |
| Fallback/repair | none selected |
| `last_answer` before | unavailable |
| `last_answer` after | overwritten on turn 6. Preserved anchor text is the shrug / captain paragraph above |
| Other persisted context | `time_pressure` 6. `active_interaction_target_id` becomes `tavern_runner` |

## Turn 6 — appointment / willingness

| Field | Value |
| --- | --- |
| Turn | 6 |
| Exact player input | `"Does that require an appointment? Would he be willing to speak to a newcomer like me?` |
| Exact GM output | `Tavern Runner mutters, "Word is, he’s the one who handles official talk and might give you an answer."` |
| Parsed kind | `question` |
| Action ID | `question_tavern_runner` |
| Segmentation | declared: `"Does that require an appointment?` / adjudication: `Would he be willing to speak to a newcomer like me?` |
| Route | `mixed` on the contract; `routed_to`: `social_exchange` |
| Routed owner | social exchange |
| Route reason | `active_interlocutor_followup` |
| Target | `tavern_runner` |
| Addressed NPC | `tavern_runner` |
| Address source | `active_interlocutor`. Contract: `interlocutor_status` `retained`, `continuity_status` `preserved` |
| Question dimension | `general` |
| Resolution | `reply_kind`: `answer` because escalation level 2 `force_partial_answer` and `prior_same_dimension_answer_exists`: true. Hint still says no new information. `social_answer_retry_candidate_source`: `topic_pressure:last_answer`. `final_emitted_source`: `minimal_social_emergency_fallback` |
| State changes | `{}`. `topic_revealed`: null |
| Topic changes | updates `topic:bandit_cant_caus`, speaker `tavern_runner`, `last_turn` 7 |
| Lead/clue changes | `recent_contextual_leads` gains roster-board / official-talk fragments. `lead_registry` stays `{}` |
| Transition | false |
| Model/realization evidence | `strict_social`. Stored `last_answer` is the full model paragraph; the shown sentence is its ending |
| Integrity result | candidate passed. Completeness passed. `narrative_authority_failed`: false. Realization family: `strict_social_deterministic_fallback` |
| Fallback/repair | emergency social fallback. Prepared grimace line not emitted |
| `last_answer` before | turn 5 model paragraph (retry anchor) |
| `last_answer` after | `The tavern runner shakes their head again, voice low and cautious. "I can’t say if you need an appointment or if he’d speak with a newcomer like you. Best you try asking the guard captain—the one keeping watch near the roster board. He’s the one who handles official talk and might give you an answer."` |
| Other persisted context | `time_pressure` 7 |

## Turn 7 — mingling

| Field | Value |
| --- | --- |
| Turn | 7 |
| Exact player input | `"Sure, but is he known to meet and mingle with common folk? If he isn't, I don't feel I should waste my time."` |
| Exact GM output | `Tavern Runner mutters, "Word is, but don't expect an easy ear without some introduction."` |
| Parsed kind | `question` |
| Action ID | `question_tavern_runner` |
| Segmentation | spoken text is the quote without wrapping quotes |
| Route | `social` |
| Routed owner | social exchange |
| Route reason | `active_interlocutor_followup` |
| Target | `tavern_runner` |
| Addressed NPC | `tavern_runner` |
| Address source | `active_interlocutor`. Continuity preserved |
| Question dimension | `general`. Escalation level 1. `prior_same_dimension_answer_exists`: false (new topic key) |
| Resolution | `reply_kind`: `refusal`. Hint: no new information. `final_emitted_source`: `structured_fact_candidate_emission`. Completeness skipped: `strict_social_structured_or_bridge_source` |
| State changes | `{}`. `topic_revealed`: null. `revealed_topics`: `[]` |
| Topic changes | new key `topic:common_dont_feel`, speaker `tavern_runner`, `last_turn` 8 |
| Lead/clue changes | more `recent_contextual_leads` from this prose. `lead_registry` and `clue_knowledge` stay empty |
| Transition | false |
| Model/realization evidence | `strict_social`. Shown clause is the last sentence of the stored model paragraph |
| Integrity result | candidate passed. `narrative_authority_failed`: false. Invented-outcome flags false |
| Fallback/repair | structured-fact emission, not the prepared grimace |
| `last_answer` before | unavailable for this new topic key. Prior captain topic still stored |
| `last_answer` after | `"I can't say for sure if he mingles much with common folk," the tavern runner mutters, casting a cautious glance around. "The guard captain tends to keep to himself and his duties. If you want to try, your best bet is to find him near the roster board. But don't expect an easy ear without some introduction."` |
| Other persisted context | `time_pressure` 8. `current_interlocutor`: `tavern_runner`. `current_date`: `Day 1`. Scene still `frontier_gate` |
