# Post mixed-action repair extended playtest

Evidence preservation only. Captured on 2026-09-23 (local) / 2026-09-24 (UTC) from the canonical local data directory and read-only debug GETs against the already-running app at `http://127.0.0.1:8000`. No gameplay turn was issued. No production code, tests, prompts, validators, authored content, or live game state were edited for this capture.

This bundle is a new run. It is not `20260923_cinderwatch_crowd_observation_failure`.

## Session Identification

The current human session is the live canonical store under `data/`, not an older artifact directory.

How it was identified:

- `data/session.json` `saved_at` / `payload.last_saved_at` is `2026-09-24T00:23:06.172189Z`.
- `payload.session_id` and `payload.campaign_run_id` are `ba70eb525862575033539357`.
- `data/session_log.jsonl` has 8 entries. The first player-facing log timestamp is `2026-09-24T00:17:08.223631Z`. The latest is `2026-09-24T00:23:06.242189Z`.
- The latest player text in that log matches `payload.last_action_debug.player_input`.
- The running server console (`server_console/terminal_3_server_snapshot.txt`) records, in order: campaign `ec79b93a51bc6b5da11507c0`, then `[SESSION RESET]`, then `[API] New campaign started ba70eb525862575033539357`, then `POST /api/start_campaign`, then seven `POST /api/chat` calls. That second campaign id is the one still on disk.
- The previous crowd-observation bundle is a different session: `423d201401cb9c57d502650f`, `saved_at` `2026-09-23T09:31:34.551548Z`, `turn_counter` 2, different player text.

| Field | Value |
| --- | --- |
| Session ID | `ba70eb525862575033539357` |
| First log timestamp | `2026-09-24T00:17:08.223631Z` |
| Latest log timestamp | `2026-09-24T00:23:06.242189Z` |
| Authoritative turn counter at capture | `8` |
| Log entries | 8 |
| Player turns with non-empty input | 7 (log entries 1–7) |
| GM player-facing outputs | 8 (opening plus 7 replies) |
| Opening scene | `frontier_gate` |
| Current scene | `frontier_gate` |
| Visited scenes | `frontier_gate` only |
| Character name on session | Galinor |
| Current date | Day 1 |

An earlier campaign id, `ec79b93a51bc6b5da11507c0`, was started in this same server process and then cleared by session reset before the persisted run. Its gameplay rows are not on disk. The console snapshot is the only retained trace of that reset.

## Bundle Contents

### RAW

- `persisted_data/session_log.jsonl` — Canonical append-only log, copied unchanged. Eight JSON lines. Primary transcript and primary per-turn structured record.
- `persisted_data/session.json` — Canonical session file after log entry 7. Current scene, clocks, interaction context, scene state, scene runtime (including topic pressure and last-perception fields), NPC runtime, clue/lead registries, last action debug, and 20 debug traces.
- `persisted_data/world.json` — Canonical world file at the same save time. Settlements, factions, event log, and the tavern-runner NPC record.
- `persisted_data/combat.json` — Canonical combat file at the same save time. `in_combat` is false.
- `persisted_data/campaign.json` — Campaign file present in `data/`. Filesystem time is 2026-05-05; it was not rewritten during this playtest.
- `persisted_data/character.json` — Character file present in `data/`. Filesystem time is 2026-05-05; it was not rewritten during this playtest.
- `persisted_data/conditions.json` — Conditions file present in `data/`. Filesystem time is 2026-05-05; it was not rewritten during this playtest.
- `scene_definitions/frontier_gate.json` — Authored scene definition copied from `data/scenes/frontier_gate.json` (filesystem time 2026-09-19). This is the scene document, not a per-turn runtime snapshot.
- `api_exports/api_state_debug.json` — Read-only `GET /api/state?ui_mode=debug` at capture. Contains `public_state` and `debug_state`. Session id `ba70eb525862575033539357` is present.
- `api_exports/api_log_debug.json` — Read-only `GET /api/log?ui_mode=debug`. Eight entries. Debug projection of the same log.
- `api_exports/api_debug_trace.json` — Read-only `GET /api/debug_trace?ui_mode=debug`. Twenty traces, matching `session.json`.
- `server_console/terminal_3_server_snapshot.txt` — Copy of the running server console for this process, including model-route lines, one retry/fallback console sequence, the earlier reset, and the campaign id above.

### DERIVED

- `derived/transcript_readable.md` — Readable transcript built from `session_log.jsonl`. Wording is unchanged. Not a canonical source.
- `derived/turn_index.json` — Per-log-entry navigation index. Missing log fields are JSON `null`. Values are copied from the log; they are not inferred.
- `derived/log_entries/entry_00.json` through `entry_07.json` — Pretty-printed copies of each `session_log.jsonl` line. Same JSON content; whitespace differs from the raw line.
- `derived/current_authoritative_state_extract.json` — Selected current fields from `session.json`, including `scene_runtime.frontier_gate`. Current state only.
- `derived/key_presence_scan.json` — Key-name scan across the log and session payload for perception, listen, eavesdrop, overhear, observation, wire, messages, completion, and travel.
- `README.md` — This file.
- `ANALYSIS_HANDOFF.md` — Chronological pointer sheet for the next reviewer. Not a diagnosis.

## Primary Evidence

- Primary transcript: `persisted_data/session_log.jsonl` (`gm_output.player_facing_text` and `player_input`). Readable copy: `derived/transcript_readable.md`.
- Primary structured session log: `persisted_data/session_log.jsonl`.
- Best routing / intent evidence: each log line’s `resolution`, `resolution.metadata` (`turn_segmentation`, `intent_route_debug`, `social_turn_contract`, `route`, `canonical_entry_*`), `resolution.social` when present, and `log_meta.intent_classification` / `log_meta.response_type_contract`. Indexed in `derived/turn_index.json`.
- Best authoritative state evidence: `persisted_data/session.json` for post-run session state. `persisted_data/world.json` and `persisted_data/combat.json` for the other persisted channels. Per-turn `resolution.state_changes`, `log_meta.approved_state_updates`, and `log_meta.clocks_changed` are the retained deltas.
- Best NPC / social-state evidence: `session.json` `npc_runtime`, `interaction_context`, `scene_state`, and `scene_runtime.frontier_gate` (including `topic_pressure`). Social fields on log entries that contain `resolution.social`.
- Best model-realization evidence: `gm_output.metadata` model-route fields, `log_meta.gm_raw_output_meta`, `gm_output.upstream_prepared_emission`, `resolution.hint`, and `gm_output.player_facing_text`. `gm_raw_output_meta` on these entries records `has_output` only.
- Best integrity / validator evidence: `gm_output.internal_state.emission_debug_lane._final_emission_meta`, `resolution.metadata.emission_debug`, and `gm_output.response_policy`, plus top-level `gm_output` retry/fallback fields where those keys exist (present on log entry 4).
- Best continuity / topic evidence: `session.json` `scene_runtime.frontier_gate.topic_pressure` and `topic_pressure_current`, conversational memory on each `gm_output`, and the full ordered transcript.

## Missing Evidence

- Raw model wire payloads were not retained. No request messages, full prompt body, or raw completion body was found. `resolution.prompt`, when present, is a stored string on the resolution object (often the player/action text), not an upstream model transcript. `gm_raw_output_meta` is only `{"has_output": true}`.
- No historical world or session snapshot from the start of the run, or from before each turn, was on disk. Pre-turn state is not reconstructable from a saved snapshot. The log does retain per-entry `state_changes`, `approved_state_updates`, and `clocks_changed`.
- Log entry 3’s `resolution` object does not contain `kind`, `action_id`, `social`, `turn_segmentation`, or `intent_route_debug`. Those index fields are null because the keys are absent.
- `intent_route_debug` (and therefore `routed_to`, `route_reason`, `addressed_actor_id`, `addressed_actor_source`) is absent on log entries 0–3. It is present on later entries; see the index.
- No per-turn perception or listen classification field was found in the log. Key scan found no `listen`, `eavesdrop`, or `overhear` keys. Current `scene_runtime.frontier_gate` has `last_perception_visible_facts`, `last_perception_narration`, and `last_perception_turn`; at capture `last_perception_turn` is null.
- `clue_knowledge` and `lead_registry` on the session are empty objects at capture. Per-turn `discovered_clues_added` in the log is an empty list on each entry.
- Campaign, character, and conditions files were not updated during this run.
- Server console text is a terminal snapshot, not a structured application log. It does not contain prompts or model bodies.
- The reset campaign `ec79b93a51bc6b5da11507c0` has no persisted transcript.

## Mutation Risk

Issuing another player turn would append `data/session_log.jsonl` and rewrite `data/session.json`, `data/world.json`, and `data/combat.json`, including `last_action_debug`, social/scene runtime, topic pressure, and `debug_traces`. This session currently stores 20 debug traces. A later turn can change that list.

`POST /api/new_campaign` in this same server process already cleared a prior campaign before the persisted run. Starting another session can drop the association between the live files and this playtest. The copies in this bundle would remain.

Restarting the server was not done. Persisted files on disk are what a later process would load unless a reset endpoint is called. Do not restart the server if the goal is to keep the live process and this on-disk session tied together.

The read-only debug GETs used for `api_exports/` did not change the hashes of `session.json`, `session_log.jsonl`, `world.json`, or `combat.json` relative to the copies taken immediately before those GETs.

## Previous Bundle Relationship

`artifacts/human_playtests/20260923_cinderwatch_crowd_observation_failure/` is an earlier playtest:

- session `423d201401cb9c57d502650f`
- saved `2026-09-23T09:31:34.551548Z`
- turn counter 2
- player text about crowd eavesdropping

This directory is the later playtest after that capture, session `ba70eb525862575033539357`, eight log entries, first timestamp `2026-09-24T00:17:08.223631Z`. Do not merge the two bundles.
