# Analysis handoff

DERIVED navigation sheet. Not a diagnosis. Do not treat this file as evidence. Use the raw paths below.

Session `ba70eb525862575033539357`. Opening and current scene: `frontier_gate`. Turn counter at capture: 8. Log entries 0–7.

Shared raw locations for every entry:

- Transcript line: `persisted_data/session_log.jsonl` (one JSON object per line; line number = log index + 1)
- Pretty copy: `derived/log_entries/entry_NN.json`
- Field index: `derived/turn_index.json` → `entries[N]`
- Current state after entry 7: `persisted_data/session.json`, extract in `derived/current_authoritative_state_extract.json`
- World / combat at capture: `persisted_data/world.json`, `persisted_data/combat.json`
- Debug API projections: `api_exports/api_log_debug.json`, `api_exports/api_state_debug.json`, `api_exports/api_debug_trace.json`
- Server console: `server_console/terminal_3_server_snapshot.txt`

Model wire request/response bodies: not retained. See README Missing Evidence.

Per-turn perception/listen classification: not present on log entries. Current scene runtime perception fields are on `session.json` → `payload.scene_runtime.frontier_gate` (`last_perception_turn` is null at capture).

## Log entry 0 — opening

- Timestamp: `2026-09-24T00:17:08.223631Z`
- Player input: empty string
- Recorded `resolution.kind`: `scene_opening`
- Recorded `resolution.action_id`: `campaign_start_opening_scene`
- `intent_route_debug`: absent
- `turn_segmentation`: absent
- GM player-facing text is the opening paragraph beginning “Rain spatters against the soot-dark stone…” in `derived/transcript_readable.md`
- Pointers: `derived/log_entries/entry_00.json` — `resolution`, `resolution.state_changes`, `log_meta`, `gm_output.metadata`, `gm_output.upstream_prepared_emission`, `gm_output.internal_state.emission_debug_lane._final_emission_meta`

## Log entry 1

- Timestamp: `2026-09-24T00:17:27.164433Z`
- Player input: `I look to the banners as I enter the Eastern Gate; can I make out the heraldry?`
- Recorded `resolution.kind`: `investigate`
- Recorded `resolution.action_id`: `i_look_to_the_banners_as_i_enter_the_eas`
- Recorded `source_route`: `mixed`
- `intent_route_debug`: absent
- Recorded `turn_segmentation`: `adjudication_question_text` set to the full player input. `declared_action_text` and `spoken_text` keys absent.
- `resolution.social`: absent
- GM: `You look again. Nothing new resolves into evidence. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.`
- Pointers: `derived/log_entries/entry_01.json` — `resolution.metadata.turn_segmentation`, `resolution.metadata.embedded_adjudication`, `resolution.metadata.referenced_surface_*`, `resolution.hint`, `log_meta.intent_classification`, `gm_output.player_facing_text`, emission meta as above

## Log entry 2

- Timestamp: `2026-09-24T00:18:29.734049Z`
- Player input: `Looking to the sky, can I make out the time of day despite the rain?`
- Recorded `resolution.kind`: `investigate`
- Recorded `resolution.action_id`: `looking_to_the_sky_can_i_make_out_the_ti`
- Recorded `source_route`: `mixed`
- `intent_route_debug`: absent
- Recorded `turn_segmentation`: `adjudication_question_text` set to the full player input. `declared_action_text` and `spoken_text` keys absent.
- `resolution.social`: absent
- GM: `You look again. Nothing new resolves into evidence. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.`
- Pointers: `derived/log_entries/entry_02.json`

## Log entry 3

- Timestamp: `2026-09-24T00:19:10.827801Z`
- Player input: `I step toward the notice board, particularly interested in the curfew rules. What do they say?`
- Recorded `resolution.kind`: null (key absent)
- Recorded `resolution.action_id`: null (key absent)
- Recorded `log_meta.response_type_contract.source_route`: `exploration`
- `resolution` keys present: `world_tick_events`, `metadata` (`emission_debug` only)
- `intent_route_debug`: absent
- `turn_segmentation`: absent
- `resolution.social`: absent
- `log_meta.intent_classification.labels`: `["downtime"]`
- GM text is stored at 280 characters and ends with the ellipsis character. Full string: `derived/transcript_readable.md` log entry 3, and `entry_03.json` `gm_output.player_facing_text`
- Pointers: `derived/log_entries/entry_03.json` — note the thin `resolution` object; realization and validator material that does exist is under `gm_output`

## Log entry 4

- Timestamp: `2026-09-24T00:20:14.607170Z`
- Player input: `I'll ask anyone near the board, "Do you have any idea how many hours until dusk?"`
- Recorded `resolution.kind`: `question`
- Recorded `resolution.action_id`: `question_anyone_near_the_board_do_you_ha`
- Recorded `source_route`: `social`
- Recorded `resolution.social.reply_kind`: `reaction`
- `resolution.metadata.route`: absent
- `gm_output` includes `fallback_kind`, `final_route`, `accepted_via`, `retry_exhausted`, `targeted_retry_terminal`, `retry_failure_class`, `retry_failure_reasons`
- Server console contains a retry sequence immediately before one of the later `POST /api/chat` lines in this window. The console does not label a log index. Correlate by order in `server_console/terminal_3_server_snapshot.txt` versus log timestamps.
- GM: `The guard says, "I do not know enough to answer that."`
- Pointers: `derived/log_entries/entry_04.json` — `resolution.social`, `resolution.metadata`, `gm_output` retry/fallback keys, emission meta

## Log entry 5

- Timestamp: `2026-09-24T00:21:39.877342Z`
- Player input: `"Do you know what incident caused the curfew? I can't imagine bandits easily raiding a gated settlement."`
- Recorded `resolution.kind`: `question`
- Recorded `resolution.action_id`: `question_tavern_runner`
- Recorded `intent_route_debug.routed_to`: `social_exchange`
- Recorded `addressed_actor_id`: `tavern_runner`
- `resolution.social`: present (`reply_kind` and `topic_revealed` are on that object; copy from the entry, do not substitute)
- GM text is stored at 313 characters and ends with an ellipsis character inside the quoted speech. Full string: `derived/transcript_readable.md` log entry 5
- Visible text begins: `Tavern Runner mutters, "Word is, the tavern runner shakes their head with a shrug, saying, I don’t have the details on what exactly sparked the curfew.`
- Pointers: `derived/log_entries/entry_05.json` — `resolution.metadata.intent_route_debug`, `resolution.metadata.social_turn_contract`, `resolution.metadata.turn_segmentation`, `resolution.social`, `gm_output.player_facing_text`

## Log entry 6

- Timestamp: `2026-09-24T00:22:31.251919Z`
- Player input, copied exactly, including the unclosed quote: `"Does that require an appointment? Would he be willing to speak to a newcomer like me?`
- Recorded `resolution.kind`: `question`
- Recorded `resolution.action_id`: `question_tavern_runner`
- Recorded `turn_segmentation`: `declared_action_text` = `"Does that require an appointment?` and `adjudication_question_text` = `Would he be willing to speak to a newcomer like me?`
- Recorded `intent_route_debug`: `routed_to` `social_exchange`, `route_reason` `active_interlocutor_followup`, `addressed_actor_id` `tavern_runner`, `addressed_actor_source` `active_interlocutor`
- Recorded `social_turn_contract.reply_owner_actor_id`: `tavern_runner`
- GM: `Tavern Runner mutters, "Word is, he’s the one who handles official talk and might give you an answer."`
- Pointers: `derived/log_entries/entry_06.json` — segmentation, intent route debug, social turn contract, `resolution.social`, emission meta

## Log entry 7 — latest completed exchange

- Timestamp: `2026-09-24T00:23:06.242189Z`
- Player input: `"Sure, but is he known to meet and mingle with common folk? If he isn't, I don't feel I should waste my time."`
- Recorded `resolution.kind`: `question`
- Recorded `resolution.action_id`: `question_tavern_runner`
- Recorded `turn_segmentation`: `spoken_text` set to the utterance without the wrapping quotes. `declared_action_text` and `adjudication_question_text` keys absent.
- Recorded `intent_route_debug`: `routed_to` `social_exchange`, `route_reason` `active_interlocutor_followup`, `addressed_actor_id` `tavern_runner`, `addressed_actor_source` `active_interlocutor`
- Recorded `source_route` on `log_meta.response_type_contract`: `social`
- GM: `Tavern Runner mutters, "Word is, but don't expect an easy ear without some introduction."`
- Post-turn state for this exchange is the current `persisted_data/session.json` (`last_action_debug.player_input` matches this turn).
- Pointers: `derived/log_entries/entry_07.json` and `derived/current_authoritative_state_extract.json`

## Evidence gaps that apply across the run

- No raw model prompt or raw model response body for any entry.
- No saved pre-turn world/session snapshot. Deltas that were logged are on each entry as `state_changes`, `approved_state_updates`, and `clocks_changed`.
- Log entry 3 does not carry the resolution fields the other player turns carry.
- `intent_route_debug` begins later in the log; entries 0–3 do not have it.
- Listen / eavesdrop / overhear keys: none found.
- `clue_knowledge` and `lead_registry` are empty at capture.
- Campaign `ec79b93a51bc6b5da11507c0` was reset before this persisted run and has no transcript in this bundle.
