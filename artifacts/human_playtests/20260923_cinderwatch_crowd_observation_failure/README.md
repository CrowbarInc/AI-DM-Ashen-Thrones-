# Cinderwatch Crowd Observation Failure Evidence Bundle

Captured on 2026-09-23 from the canonical local web app after the active playtest reached the reported turn. This bundle preserves existing runtime evidence only. No gameplay turn was issued during capture.

## Collected Files

- `persisted_data/session_log.jsonl` - Canonical append-only runtime log. Contains the complete two-entry transcript for this playtest: campaign opening, then the crowd/eavesdropping turn. This is the primary transcript.
- `persisted_data/session.json` - Canonical persisted session after the reported turn. Best source for authoritative post-turn session state, current scene id, current interlocutor, interaction context, debug traces, social memory, and last action debug.
- `persisted_data/world.json` - Canonical persisted world state after the reported turn.
- `persisted_data/combat.json` - Canonical persisted combat/runtime combat state after the reported turn.
- `persisted_data/campaign.json` - Campaign premise and character context used by the run.
- `persisted_data/character.json` - Character sheet/context for Galinor.
- `scene_definitions/frontier_gate.json` - Authored active scene definition for `frontier_gate`, including visible facts, opening seed facts, hidden facts, addressables, exits, and interactables.
- `api_exports/api_state_debug.json` - Read-only `/api/state?ui_mode=debug` export from the running local app. Mirrors the UI/debug state projection at capture time.
- `api_exports/api_log_debug.json` - Read-only `/api/log?ui_mode=debug` export from the running local app. This is a formatted debug projection of the transcript/log entries.
- `api_exports/api_debug_trace.json` - Read-only `/api/debug_trace?ui_mode=debug` export from the running local app. Contains the retained session debug traces.

## Evidence Map

- Primary transcript: `persisted_data/session_log.jsonl`. The easier-to-read debug projection is `api_exports/api_log_debug.json`.
- Best routing/intent evidence: `persisted_data/session_log.jsonl` and `api_exports/api_log_debug.json`, especially the second entry's `resolution.metadata`, `intent_route_debug`, `social_turn_contract`, `turn_segmentation`, `response_type_contract`, `log_meta.intent_classification`, and `log_meta.gm_prompt_context_summary`.
- Best authoritative state evidence: `persisted_data/session.json` for post-turn runtime/session state, plus `persisted_data/world.json` and `persisted_data/combat.json` for other persisted state channels.
- Current scene and NPC/addressable state: `scene_definitions/frontier_gate.json` for authored scene/addressables; `persisted_data/session.json` for active scene state, current interlocutor, and active interaction context.
- Perception/investigation/social routing decisions: second log entry in `persisted_data/session_log.jsonl` and `api_exports/api_log_debug.json`. The turn was recorded as `kind: question`, `action_id: question_tavern_runner`, `canonical_entry_path: social`, `route: dialogue`, with a segmented declared action and adjudication question.
- Realization input/output and validator evidence: final GM outputs, response contract, final-emission diagnostics, validation flags, fallback lineage, and mutation lineage are present in `persisted_data/session_log.jsonl`, `persisted_data/session.json`, and the API exports.
- Topic/lead/context state: `persisted_data/session.json` includes social memory and last answer state; the turn log includes `lead_landing` fields and selected conversational memory. No lead was recorded as revealed for this turn.
- Session metadata: `persisted_data/session.json`, `persisted_data/session_log.jsonl`, and `api_exports/api_state_debug.json`.

## Model Evidence

Model metadata is available, including selected model fields such as `selected_model: gpt-4.1-mini`, model route metadata, final GM output, `gm_raw_output_meta.has_output`, and detailed final-emission diagnostics.

Raw upstream model request payloads, full prompt/messages, and raw upstream model response bodies were not found in the persisted runtime evidence or read-only debug API exports.

## Recovered vs Missing

Recovered:

- Complete current two-turn transcript.
- Parsed/resolved action and social routing metadata for the failure turn.
- Authoritative post-turn persisted state.
- Active scene definition and addressable/NPC data.
- Final emission, validator, fallback, answer-completeness, speaker-binding, referential-clarity, and continuity diagnostics.
- Session/debug API projections from the running app.

Not recovered:

- A full authoritative pre-turn snapshot immediately before the failure turn. The opening log entry and current turn metadata provide context, but the persisted session file is post-turn.
- Raw upstream LLM request/response wire payloads.
- Any external server console logs beyond the repository-backed runtime files and read-only API exports collected here.

## Mutation Risk

Issuing another gameplay turn would append another row to `data/session_log.jsonl` and would likely mutate `data/session.json`, `data/world.json`, `data/combat.json`, `last_action_debug`, social memory, interaction context, and retained `debug_traces` state. `debug_traces` are capped in the repository code, so later turns can also displace older trace entries.
