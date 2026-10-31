# Session Causal Timeline

Session `735ebd1cfb4567c4f97df6dc`. Log entries 00–09. Timestamps `2026-09-26T01:44:59Z` through `2026-09-26T01:54:18Z`. Scene `frontier_gate` before and after every entry. Human chat turns: 9, plus the empty `start_campaign` opening.

Evidence limits, from the bundle README: raw model prompts and completions were not retained. Historical pre-turn / post-turn snapshots were not retained. Fields below that are not in the log row are marked unavailable. Session turn numbers in runtime (`last_turn`, `recent_player_actions`) are log index + 1.

Authoritative scene content used for comparison is `scene_definitions/frontier_gate.json` in the bundle, plus `data/scenes/old_milestone.json` for the exit target. Ending overlay is `derived/current_authoritative_state_extract.json`.

---

## TURN 00 — opening

PLAYER INPUT: empty (`start_campaign`)

PLAYER-FACING OUTPUT: Eastern-gate opening. Soot-dark stone, rain-slick mud, frayed banners, refugees and wagons, guards at the choke, a townhouse with noble colors, a still threadbare figure, a notice board listing new taxes, strict curfews, and a missing-patrol warning, a tavern runner offering stew and rumors by a rain barrel.

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: unavailable (no player text)
RESOLUTION KIND: `scene_opening`
ACTION ID: `campaign_start_opening_scene`
ROUTE / OWNER: opening deterministic fallback
TARGET ACTOR / INTERACTABLE / EXIT: none
ADDRESSED NPC / ACTIVE INTERLOCUTOR: none / none recorded

AUTHORITATIVE FACTS AVAILABLE BEFORE TURN: authored `opening_seed_facts` and `visible_facts` for `frontier_gate`
AUTHORITATIVE RESULT: opening succeeded. `resolved_transition` false. `activate_scene_id` `frontier_gate`
STATE MUTATIONS: no `scene_update`. No clue discovery.
CLUE / LEAD / TOPIC / INTERACTABLE / TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_primary_turn`, `gm_raw_output_meta.has_output` true. Raw completion unavailable.
FINAL EMITTED SOURCE: `opening_deterministic_fallback`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. Lineage: `opening_fallback_selection`, `sealed_fallback_replacement`, `finalize_packaging`. `producer_repair_kind` `first_mention_enforcement`.
FALLBACK USED: yes, opening deterministic fallback (`gate_terminal_repair`)

LAST_ANSWER BEFORE / AFTER: not present on this row. Ending topic pressure was created on later turns.

NARRATED NEW WORLD FACTS: gate, banners, crowd, guards, townhouse, threadbare figure, notice board topics (taxes, curfews, missing patrol), tavern runner, rain barrel, stew and rumors.
WERE THEY AUTHORITATIVELY ESTABLISHED?: yes. Each of those is an opening seed or visible fact. The route past the crates, curfew hours, sheds, lanterns, and broken patrol banners are not in this output.

PLAYER-PERCEIVED WORLD: at Cinderwatch's eastern gate. A board lists taxes, curfews, and a missing patrol. A runner is offering stew and rumors.
AUTHORITATIVE WORLD: `frontier_gate`. Same facts. No clue discovered yet. Exits exist but were not offered as traveled.

---

## TURN 01 — approach the notice board

PLAYER INPUT: `I'm new to the city, so I approach the notice board with curiosity; it's too early to be thrown in the dungeons for breaking simple rules.`

PLAYER-FACING OUTPUT: The board is weathered and plastered with decrees. It lists new taxes imposed this month, a schedule for the town's strict curfew hours, and a warning about a patrol gone missing near the northwest mud track past the nearby crates. A gate serjeant watches the crowd and glances at a roster of patrolling guards.

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: one declared clause, the whole utterance. No spoken-text split.
RESOLUTION KIND: `social_probe`
ACTION ID: `social_probe_notice_board_with_curiosity`
ROUTE / OWNER: `canonical_entry_path` `social`, reason `no_addressable_target`
TARGET ACTOR: none (`target_resolved` false, `target_source` `none`, candidate `notice board with curiosity; it's too early to be`, invalid)
TARGET INTERACTABLE: none (`interactable_id` absent)
TARGET LOCATION / EXIT: none
ADDRESSED NPC: none
ACTIVE INTERLOCUTOR: none

AUTHORITATIVE FACTS AVAILABLE BEFORE TURN: visible facts include that the board lists taxes, curfew rules, and a missing-patrol warning, and that a gate serjeant watches a roster board. Discoverable clue `notice_patrol_route` exists and is not yet discovered. No curfew hours, districts, penalties, or reasons are authored.
AUTHORITATIVE RESULT: social probe failed (`success` false). Hint text: narrate that the social attempt has no clear target. `clue_id` null. `discovered_clues` empty.
STATE MUTATIONS: `scene_update` null. Approved state updates null.
CLUE / LEAD / TOPIC / INTERACTABLE / TRANSITION: no discovery. `resolved_transition` false.

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_primary_turn`
FINAL EMITTED SOURCE: `generated_candidate`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. `reply_kind` `reaction`. Lineage: `finalize_packaging` only. No fallback replacement.
FALLBACK USED: no

LAST_ANSWER: not written on this row. Unavailable as a before/after snapshot.

NARRATED NEW WORLD FACTS:
- a readable schedule of curfew hours
- the patrol was last seen near the northwest mud track past the crates
- a roster of patrolling guards (the roster board itself is a visible fact)
WERE THEY AUTHORITATIVELY ESTABLISHED?: the schedule of hours was not. The northwest route and crates are the undiscovered clue `notice_patrol_route`, and this turn did not discover it. The serjeant and the roster board are visible facts.

PLAYER-PERCEIVED WORLD: the player has read the board. It states curfew hours as a schedule, and it states the patrol's northwest route past crates.
AUTHORITATIVE WORLD: still `frontier_gate`. No clue discovered. `searched_targets` does not yet include `notice_board`.

---

## TURN 02 — examine the curfew section

PLAYER INPUT: `I examine the curfew section more carefully. I need to know what times are limited, and potentially what parts of Cinderwatch.`

PLAYER-FACING OUTPUT: Threadbare watchers and refugees along the muddy gate line. A gate serjeant manages the crowd and watches the roster board. Then: `The missing patrol was last seen taking the northwest mud track past the crates.`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: declared action is the whole utterance. Probe of the same sentence with the scene loaded: `investigate` / `notice_board`.
RESOLUTION KIND: `discover_clue`
ACTION ID: `notice_board`
ROUTE / OWNER: referenced-surface authority `authored_interactable`. `referenced_surface_target` `curfew`. `referenced_surface_interactable_id` `notice_board`. `skip_unrelated_clue_discovery` false.
TARGET ACTOR: none
TARGET INTERACTABLE: `notice_board` (`reveals_clue` `notice_patrol_route`)
TARGET LOCATION / EXIT: none
ADDRESSED NPC / ACTIVE INTERLOCUTOR: none / none

AUTHORITATIVE FACTS AVAILABLE BEFORE TURN: same visible facts. Clue `notice_patrol_route` still undiscovered at resolution start. Alias `curfew notice` is on `notice_board`. No hours, districts, penalties, or reasons exist.
AUTHORITATIVE RESULT: `success` true. `clue_id` `notice_patrol_route`. `clue_text` is the northwest mud-track sentence. `state_changes.clue_revealed` true. `interactable_id` `notice_board`. Hint: narrate that discovery.
STATE MUTATIONS: no `scene_update`. Lead registry later shows `notice_patrol_route` `first_discovered_turn` 3 (this log entry). `searched_targets` includes `notice_board`.
CLUE / LEAD: discovered `notice_patrol_route`. `pending_leads` stayed empty. Lead `related_scene_ids` is only `frontier_gate`. `next_step` empty. It does not store `old_milestone`.
TOPIC: none
INTERACTABLE: `notice_board` resolved / searched
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_strict_social`, escalated, family `high_precision`
FINAL EMITTED SOURCE: `passive_scene_pressure_fallback`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. Tags include `authored_knowledge_realization` with note `resolution:authored_discovery`, plus `visibility_enforcement_replaced` and `visibility_violation:undiscovered_fact_assertion` on the patrol sentence. `producer_repair_kind` `visibility_enforcement`. `post_gate_mutation_detected` true.
FALLBACK USED: yes. Passive scene pressure supplied the two visible-fact sentences. Authored-discovery realization appended the clue.

LAST_ANSWER: not a social topic write. Unavailable on this row.

NARRATED NEW WORLD FACTS: the patrol route sentence, now also an authoritative discovery. The curfew hours and districts the player asked for are absent from the output.
WERE THEY AUTHORITATIVELY ESTABLISHED?: the route sentence is the interactable's only reveal, and this turn did discover it. The hours and districts were not established and were not answered.

PLAYER-PERCEIVED WORLD: examining the curfew section produced the patrol's northwest route past the crates, not times or districts.
AUTHORITATIVE WORLD: `frontier_gate`. `notice_patrol_route` is now discovered. The player is not on that track.

---

## TURN 03 — ask the tavern runner how to get around

PLAYER INPUT: `Moving away from the board, I approach the tavern runner I passed earlier. "Friend, I'm new to Cinderwatch. What should I stranger know to get around in this city?"`

PLAYER-FACING OUTPUT: `Tavern Runner mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: `declared_action_text` is the approach sentence. `spoken_text` is the quoted question.
RESOLUTION KIND: `social_probe`
ACTION ID: `social_probe_tavern_runner_i_passed_earl`
ROUTE / OWNER: `canonical_entry_path` `social`, reason `explicit_non_social_action_escapes_social_lock`, then a runner bind. `authority_source_used` `substring`. `target_reason` `conservative slug substring matched one roster NPC`.
TARGET ACTOR: `tavern_runner` (`target_resolved` true, `npc_name` Tavern Runner)
TARGET INTERACTABLE: none
ADDRESSED NPC: Tavern Runner, by name in the declared clause
ACTIVE INTERLOCUTOR: `tavern_runner` (`active_interaction_target_id` in emission debug)

AUTHORITATIVE FACTS AVAILABLE: discovered clue `notice_patrol_route`. Runner topic `patrol_rumor`: `The runner heard the patrol vanished near muddy footprints northwest of the crates.` (`clue_id` `muddy_footprints_northwest`). No city-navigation topic.
AUTHORITATIVE RESULT: `reply_kind` `refusal`. `topic_revealed` null. `social_question_dimension` `general`. `prior_same_dimension_answer_exists` false. `anchor_tokens_extracted` includes `patrol` even though the player did not say patrol. `strategy_forced_to_answer` false.
STATE MUTATIONS: no scene update, no new clue.
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_strict_social`, escalated
FINAL EMITTED SOURCE: `minimal_social_emergency_fallback`
INTEGRITY / VALIDATION: early snapshots and the final player text are the `Word is` patrol line. A later snapshot is `Tavern Runner grimaces. "Not something I can say here."` Visibility flagged `undiscovered_fact_assertion` on the patrol sentence and set `final_text_preview` to the grimace. Tags include `authored_knowledge_realization` and `visibility_enforcement_replaced`. `post_gate_mutation_detected` true. The grimace did not remain the player-facing text.
FALLBACK USED: yes. Emergency/visibility ignorance was computed, then authored-knowledge realization put the discovered patrol sentence back in a `Word is` envelope (`format_structured_fact_social_line`).

LAST_ANSWER BEFORE: unavailable (no snapshot).
LAST_ANSWER AFTER: this row does not store a topic-pressure last_answer. The quantity topic is written on turn 04.

NARRATED NEW WORLD FACTS: none beyond the already discovered patrol sentence, now spoken by the runner.
WERE THEY AUTHORITATIVELY ESTABLISHED?: the sentence is the board clue, not the runner's own topic sentence. It is true as a discovered clue. It does not answer how a stranger gets around the city.

PLAYER-PERCEIVED WORLD: the runner's guidance for getting around the city is the northwest mud track past the crates.
AUTHORITATIVE WORLD: still `frontier_gate`. Runner was correctly addressed. Runner's authored topic was not the line spoken.

---

## TURN 04 — how many soldiers

PLAYER INPUT: `"A missing patrol? That's strange. How many soldiers disappeared?"`

PLAYER-FACING OUTPUT: `Tavern Runner says, "No. I cannot answer that from what I know."`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: `spoken_text` is the whole quote.
RESOLUTION KIND: `question`
ACTION ID: `question_tavern_runner`
ROUTE / OWNER: `canonical_entry_reason` `active_interlocutor_followup`. `target_source` `explicit_target`. `target_reason` `normalized target_id matches scene-addressable roster`.
TARGET ACTOR: `tavern_runner`
ADDRESSED NPC: none by a new name. Continuity kept the runner.
ACTIVE INTERLOCUTOR: `tavern_runner`

AUTHORITATIVE FACTS: runner topic and the discovered route sentence. Neither states a count.
AUTHORITATIVE RESULT: `social_question_dimension` `quantity`. `reply_kind` on the social object is `answer`, while narration constraints say `refusal`. `topic_revealed` null. `strategy_forced_to_answer` true, reason `valid_followup_alignment`. `prior_same_dimension_answer_exists` false.
STATE MUTATIONS: no scene update, no new clue.
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_strict_social`, escalated
FINAL EMITTED SOURCE: `generated_candidate`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. Lineage `finalize_packaging` only. No fallback replacement of the player text.
FALLBACK USED: no

LAST_ANSWER BEFORE: unavailable.
LAST_ANSWER AFTER: topic `topic:approach_around_away`, `last_turn` 5 (this entry). Stored text is a model paragraph: the runner guesses half a dozen, then points the player at a guard captain inside the gate who keeps rosters. `last_answer_provenance` `generative_reply`. No `last_answer_authoritative_text` on this topic. The player did not see that paragraph.

NARRATED NEW WORLD FACTS: none in the player-facing line. The stored last_answer invents a count range and a captain inside the gate. That invention was not emitted.
WERE THEY AUTHORITATIVELY ESTABLISHED?: the spoken refusal matches the absence of a count. The stored paragraph was not established and was not shown.

PLAYER-PERCEIVED WORLD: the runner does not know how many soldiers disappeared.
AUTHORITATIVE WORLD: unchanged scene. Runner remains the interlocutor. No count exists.

---

## TURN 05 — reward / the watch

PLAYER INPUT: `"Well, is there a reward for who finds out? Or perhaps, can turn in useful information to the watch?"`

PLAYER-FACING OUTPUT: `Gate Guard shrugs.`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: `spoken_text` is the whole quote. `declared_switch_detected` false. `spoken_vocative_detected` false.
RESOLUTION KIND: `question`
ACTION ID: `question_gate_guard`
ROUTE / OWNER: `canonical_entry_reason` `directed_social_question`. `target_source` `explicit_target`. `target_reason` `normalized target_id matches scene-addressable roster`. `grounding_reason_code` `authoritative_speaker_eligible_topic_salience_ignored`.
TARGET ACTOR: `gate_guard`
ADDRESSED NPC: not by name. The phrase `to the watch` is present.
ACTIVE INTERLOCUTOR BEFORE: `tavern_runner` (turns 03–04)
ACTIVE INTERLOCUTOR AFTER: `gate_guard` (`active_interaction_target_id`, speaker label `Gate Guard`)

AUTHORITATIVE FACTS: Gate Guard topic `watch_command`: `Captain Thoran commands the gate watch tonight.` No reward, bounty, or informant procedure is authored. Alias list includes `watch`.
AUTHORITATIVE RESULT: `reply_kind` `refusal`. `social_question_dimension` `identity`. `topic_revealed` null. `prior_same_dimension_answer_exists` false. `strategy_forced_to_answer` false.
STATE MUTATIONS: no scene update. `recent_contextual_leads` later includes fragments of an unshown model line about there being no reward, attributed to the gate guard, `last_turn` 6.
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_strict_social`, escalated
FINAL EMITTED SOURCE: `deterministic_social_fallback`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. `producer_repair_kind` `strict_social_repair`. `post_gate_mutation_detected` true.
FALLBACK USED: yes, deterministic social fallback. The shrug is the player-facing result.

LAST_ANSWER BEFORE: quantity topic holds the unshown generative paragraph (`generative_reply`).
LAST_ANSWER AFTER: topic `topic:find_information_perhap`, `last_turn` 6, speaker `gate_guard`. `last_answer` is a paragraph about a muddied northwest trail, broken banners, uniform sigils, twigs, footprints, and smoke. `last_answer_provenance` `clue_knowledge`. `last_answer_authoritative_text` is the patrol-route clue, not the banner paragraph. The player did not see the banner paragraph. They saw the shrug.

NARRATED NEW WORLD FACTS: a gate guard shrugged. No reward was stated.
WERE THEY AUTHORITATIVELY ESTABLISHED?: Gate Guard is present at `frontier_gate`. No reward fact exists, so a refusal is consistent with content. The speaker change is not something the player asked for by name. The banner paragraph was stored and not shown.

PLAYER-PERCEIVED WORLD: the conversation is now with a gate guard, who shrugs at the reward question. The runner has dropped out without an explicit goodbye.
AUTHORITATIVE WORLD: still `frontier_gate`. Interlocutor state is `gate_guard`. No reward fact. No banners. No movement.

---

## TURN 06 — proceed northwest

PLAYER INPUT: `Inclined to take this matter into my own hands, I proceed North-West, as the runner directed.`

PLAYER-FACING OUTPUT: The player threads the crowd, turns northwest, passes weather-beaten crates at the edge of the gate district, and continues on a mud track flanked by storage sheds and lanterns. Broken patrol banners flutter on nails in the crates. The last sentence places the player's steps in the stretch where the missing soldiers were last seen.

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: no segmentation object on the resolution. Isolated probe of this sentence against the authored scene: `parse_freeform_to_action` returns `None`. `extract_travel_destination_phrase` returns `None`. `resolve_authored_exit_from_player_travel` returns `None`.
RESOLUTION KIND: null. Resolution keys are only `world_tick_events` and `metadata.emission_debug`.
ACTION ID: null
ROUTE / OWNER: none. `parse_freeform_to_action` documents `None` as ambiguous input that falls through to generative narration.
TARGET ACTOR / INTERACTABLE / EXIT: none
ADDRESSED NPC: none
ACTIVE INTERLOCUTOR: emission continuity fields are empty. Topic-pressure current speaker remains `gate_guard` from turn 05. This turn did not reselect that speaker in the player text.

AUTHORITATIVE FACTS AVAILABLE: discovered route sentence. Exits: `Enter Cinderwatch` → `market_quarter`; `Follow the missing patrol rumor` → `old_milestone`. `old_milestone` describes a stone milestone and mud prints on the northwest mud track. It does not author crates, sheds, lanterns, or broken banners. Lead row does not point at `old_milestone`.
AUTHORITATIVE RESULT: no transition. `resolved_transition` null. `activate_scene_id` null. Scene id stays `frontier_gate`.
STATE MUTATIONS: approved `scene_update`:
- `visible_facts_add`: `You have reached the northwest mud track past the crates, the last known route of the missing patrol.`
- `discoverable_clues_add`: `Broken patrol banners along the mud track bear a sigil matching those on the missing patrol’s uniforms.`
- `hidden_facts_add`: `The path ahead is watched by unseen eyes; subtle signs suggest someone follows quietly.`
- `mode`: `exploration`
CLUE / LEAD: no registry discovery. The new clue string exists only as an overlay mutation. Contextual lead stores a fragment of the travel prose (`last_turn` 7).
TOPIC: no new topic key
INTERACTABLE: none
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_primary_turn`, not escalated. `generated_candidate`.
FINAL EMITTED SOURCE: `generated_candidate`
INTEGRITY / VALIDATION: `narrative_authority_failed` false. Reasons empty. Lineage `finalize_packaging` only. `scene_integrity_named_destination` null. `realization_fallback_family` null.
FALLBACK USED: no

LAST_ANSWER: unchanged by a social commit on this row. The banner paragraph already stored on turn 05 was not the player-facing text here. This turn's player text is a new generation.

NARRATED NEW WORLD FACTS: the player left the crowd along a northwest mud track; crates, sheds, lanterns, and broken patrol banners are present; the player has entered the patrol's last known stretch.
WERE THEY AUTHORITATIVELY ESTABLISHED?: no transition occurred. Those objects are not in `frontier_gate` or `old_milestone`. The route sentence names crates as where the patrol was seen, not as objects the player is passing. The same turn's `scene_update` then wrote the arrival and the banner clue into the runtime overlay.

PLAYER-PERCEIVED WORLD: the player is on the northwest mud track, past crates, among sheds, lanterns, and broken patrol banners.
AUTHORITATIVE WORLD: `active_scene_id` is still `frontier_gate`. `visited_scene_ids` remains only `frontier_gate`. Overlay now claims the player has reached the track and adds banner/hidden-watcher prose as if it were scene content.

---

## TURN 07 — crates opened or rummaged

PLAYER INPUT: `As I pass the crates, can I tell whether any of them have been opened or rummaged through?`

PLAYER-FACING OUTPUT: `The missing patrol was last seen taking the northwest mud track past the crates.`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: `adjudication_question_text` is the whole utterance.
RESOLUTION KIND: `adjudication_query`
ACTION ID: `adjudication_query`
ROUTE / OWNER: `canonical_entry_path` `adjudication`, reason `gm_feasibility`
TARGET ACTOR / INTERACTABLE: none. No crates interactable exists.
ADDRESSED NPC: none
ACTIVE INTERLOCUTOR: not changed by this resolution

AUTHORITATIVE FACTS: the route sentence mentions crates. No crate objects, opened/closed state, or rummage fact exists in the scene or in `old_milestone`.
AUTHORITATIVE RESULT: adjudication query. No clue, no transition, `scene_update` null.
STATE MUTATIONS: none approved.
TRANSITION: none

MODEL / REALIZATION SOURCE: selected model null on this row. `gm_raw_output_meta.has_output` true. Raw completion unavailable.
FINAL EMITTED SOURCE: `anti_reset_local_continuation_fallback`
INTEGRITY / VALIDATION: `final_text_preview` is `The guard says, "I do not know enough to answer that."` Tags: `adjudication_query`, anti-reset continuation, and `authored_knowledge_realization`. Debug note: `authored_knowledge_realization:topic_pressure:last_answer`. `post_gate_mutation_detected` true. The player-facing text is the patrol clue, not the guard line.
FALLBACK USED: yes. Anti-reset computed the empty-speaker guard line. Authored-knowledge realization then replaced that concealment with `topic_pressure` last-answer authority, which is the patrol clue payload.

LAST_ANSWER BEFORE: `topic:find_information_perhap` holds the unshown banner paragraph, provenance `clue_knowledge`, authoritative text = the patrol sentence.
LAST_ANSWER AFTER: not rewritten on this row. The emitted sentence matches `last_answer_authoritative_text`, not the banner paragraph.

NARRATED NEW WORLD FACTS: none new. The route sentence is repeated.
WERE THEY AUTHORITATIVELY ESTABLISHED?: the sentence is a real discovered clue. It does not say whether any crate is open.

PLAYER-PERCEIVED WORLD: still on the track, passing crates. The answer does not say whether they were opened. It repeats the route.
AUTHORITATIVE WORLD: still `frontier_gate`. No crate object. Overlay still contains turn 06's arrival sentence.

---

## TURN 08 — broken banners

PLAYER INPUT: `I move closer to one of the broken banners, studying it carefully. How was this thing destroyed?`

PLAYER-FACING OUTPUT: `The guard says, "I do not know enough to answer that."`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: `declared_action_text` is the move-closer sentence. `adjudication_question_text` is `How was this thing destroyed?` Probe of the full sentence against the authored scene returns `None` (banners are not an interactable). Executed kind is `custom`.
RESOLUTION KIND: `custom`
ACTION ID: `i_move_closer_to_one_of_the_broken_banne`
ROUTE / OWNER: custom local action. The detail question was segmented and not given its own resolution kind.
TARGET ACTOR: none (`strict_target_id` null, `active_interaction_target_id` null in the social plan)
TARGET INTERACTABLE: none
ADDRESSED NPC: none
ACTIVE INTERLOCUTOR: not set by this resolution

AUTHORITATIVE FACTS: no banner interactable, visible fact, or clue in `frontier_gate` or `old_milestone`. Turn 06's overlay mutation added a banner sentence as `discoverable_clues_add`. That string is model-written, not authored content.
AUTHORITATIVE RESULT: `custom`. `success` null. No clue id. No transition.
STATE MUTATIONS: approved `scene_update` again adds the banner discoverable-clue sentence and `mode` `exploration`. Player-facing text does not mention banners.
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_primary_turn`
FINAL EMITTED SOURCE: `anti_reset_local_continuation_fallback`
INTEGRITY / VALIDATION: `final_text_preview` matches the player text. `post_gate_mutation_detected` true. No visibility violation. No authored-knowledge tag.
FALLBACK USED: yes. `local_exchange_continuation_fallback_line` calls `minimal_social_emergency_fallback_line`. With no `npc_name` and no `npc_id`, `speaker_label` returns `The guard`. Index of the three-line catalog yields `The guard says, "I do not know enough to answer that."`

LAST_ANSWER: not updated on this row.

NARRATED NEW WORLD FACTS: a guard spoke. No destruction method.
WERE THEY AUTHORITATIVELY ESTABLISHED?: no social target was resolved. No guard speech is in the resolution social object (the social object is empty). The line is the empty-identity catalog default.

PLAYER-PERCEIVED WORLD: the broken banners are real enough to approach, and a guard answers that they cannot say how one was destroyed.
AUTHORITATIVE WORLD: still `frontier_gate`. No banner object in authored content. Overlay repeats the model banner sentence. `current_interlocutor` at end of session is null. This turn did not store a guard id.

---

## TURN 09 — continue following the path

PLAYER INPUT: `Not deterred, I continue following the path.`

PLAYER-FACING OUTPUT: `The guard says, "I do not know enough to answer that."`

SCENE BEFORE / AFTER: `frontier_gate` / `frontier_gate`

PARSED / SEGMENTED ATTEMPT: none on the resolution. Probe: `parse_freeform_to_action` returns `None`. Not travel. Not an exit bind.
RESOLUTION KIND: null
ACTION ID: null
ROUTE / OWNER: none, same unparsed fallthrough as turn 06
TARGET ACTOR / INTERACTABLE / EXIT: none
ADDRESSED NPC: none
ACTIVE INTERLOCUTOR: continuity fields empty

AUTHORITATIVE FACTS: no path-continuation transition. The rumor exit remains available and was not selected. Scene id is still `frontier_gate`.
AUTHORITATIVE RESULT: no transition. `resolved_transition` null.
STATE MUTATIONS: approved `scene_update`:
- `visible_facts_add` repeats the arrival sentence and adds `Broken banners along the path bear the sigil matching those on the missing patrol’s uniforms.`
- `mode` `exploration`
The player did not see those sentences.
TRANSITION: none

MODEL / REALIZATION SOURCE: `gpt-4.1-mini`, `purpose_primary_turn`
FINAL EMITTED SOURCE: `anti_reset_local_continuation_fallback`
INTEGRITY / VALIDATION: `referential_clarity_replacement_applied` true. `producer_repair_kind` `referential_clarity_enforcement`. Tag `referential_clarity_violation:ambiguous_entity_reference`. `post_gate_mutation_detected` true. `narrative_authority_failed` false.
FALLBACK USED: yes. Same empty-speaker guard line as turn 08.

LAST_ANSWER: not updated. Ending `topic_pressure_current` is still the turn 05 gate-guard reward exchange.

NARRATED NEW WORLD FACTS: a guard spoke again. The path was not described.
WERE THEY AUTHORITATIVELY ESTABLISHED?: no speaker was resolved. The overlay nevertheless gained another arrival/banner visible fact.

PLAYER-PERCEIVED WORLD: still on a path, and a guard still cannot answer.
AUTHORITATIVE WORLD: `frontier_gate` only. Overlay asserts arrival and banners. `turn_counter` 10. `current_date` `Day 1`. `world_state.clocks` empty. `time_pressure` 10. Combat inactive. `current_interlocutor` null.
