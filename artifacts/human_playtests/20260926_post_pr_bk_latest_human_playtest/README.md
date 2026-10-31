# Latest Post-PR-BK Human Playthrough Evidence Bundle

## Identification

- Target session id: `735ebd1cfb4567c4f97df6dc` (from `data/session.json` payload).
- Date/time range: `2026-09-26T01:44:59.723460Z` to `2026-09-26T01:54:18.201243Z`.
- Log entries captured: 10.
- Human chat turns captured: 9 (excludes the empty `start_campaign` opening entry, which is still included as log entry 00).
- Starting scene: `frontier_gate`.
- Ending scene: `frontier_gate`.
- Latest-playthrough identification: `data/session_log.jsonl` contains a fresh `start_campaign` entry at `2026-09-26T01:44:59.723460Z` followed by the current ten-entry chronology through `2026-09-26T01:54:18.201243Z`; `data/session.json` was saved at `2026-09-26T01:54:18.130251Z` with matching `turn_counter` 10, current scene `frontier_gate`, and session id `735ebd1cfb4567c4f97df6dc`. No newer runtime session evidence was present in the canonical files inspected.

## Files Captured

- Raw persisted runtime copies: `persisted_data/session.json`, `persisted_data/session_log.jsonl`, `persisted_data/world.json`, `persisted_data/combat.json`, `persisted_data/campaign.json`, `persisted_data/character.json`, `persisted_data/conditions.json`.
- Derived per-entry log copies: `derived/log_entries/entry_00.json` through `entry_09.json`.
- Transcript: `derived/transcript_readable.md`.
- Turn index: `derived/turn_index.json`.
- Current state extract: `derived/current_authoritative_state_extract.json`.
- Key/provenance scan: `derived/key_presence_scan.json`.
- API exports: `api_exports/api_state_debug.json`, `api_exports/api_log_debug.json`, `api_exports/api_debug_trace.json`; `/api/snapshots` returned 403 and is documented in `api_exports/api_snapshots_debug_error.txt`.
- Scene definition copied: `scene_definitions/frontier_gate.json`.
- Authored-content manifest: `content_manifest/relevant_authored_content_manifest.json`.
- Server console note: `server_console/server_console_unavailable.txt`.

## Evidence Limitations

- Raw model prompts retained: no.
- Raw model completions retained: no.
- Stored evidence does retain `gm_raw_output_meta.has_output`, model route metadata, retry/repair/final-emission metadata where present, and final emitted player-facing text.
- Historical pre-turn/post-turn state snapshots available: no.
- Individual log rows do not retain a `session_id`; the session id comes from current `data/session.json` and is applied in derived indices as the active authoritative session id.
- No app terminal session was attached to this Codex thread, so no live server console buffer could be captured through the Codex terminal reader.

## Mutation Risk

- none. Capture used file reads/copies and read-only HTTP GET requests (`/api/state`, `/api/log`, `/api/debug_trace`, `/api/snapshots`) against the already-running server. No campaign reset, replay, chat/action POST, restore, commit, or push was run.

