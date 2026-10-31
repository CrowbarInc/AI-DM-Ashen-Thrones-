# PR-BT Source Evidence Notes

No model/API calls were made for PR-BT. Evidence comes from saved PR-BS provider requests and static source inspection.

## Provider Request Capture

- `artifacts/pr_bs_cooperative_gm_micro_live/run_probes.py` wraps `openai.resources.responses.Responses.create`, records `kwargs["input"]`, serializes it as `provider_request_attempt_generation_1.json`, and stores roles, input chars, recipe presence, and retry-context presence.
- Saved provider requests used for PR-BT:
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json`
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/provider_request_attempt_generation_1.json`
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/provider_request_attempt_generation_1.json`

## Message Assembly

- `game/gm.py:4005` defines `build_messages(...)`.
- `game/gm.py:4242-4243` returns exactly two messages: `{'role': 'system', 'content': SYSTEM_PROMPT}` and `{'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}`.
- `game/gm.py:127-183` builds the static system prompt header and body.
- `game/gm.py:246-323` includes the one-call JSON realization envelope and bounded improvisation authority in the static system prompt.

## Prompt Context Assembly

- `game/prompt_context.py:1558` defines `build_narration_context(...)`, the main provider payload builder.
- `game/prompt_context.py:2955-2963` attaches `response_policy`, `referent_tracking`, `turn_packet`, and other top-level provider keys.
- `game/prompt_context.py:3062-3075` attaches `resolution_contract`, `gm_resolution_decision`, and `decision_facing_answer_recipe` from `game.gm_resolution_decision.narration_authority_fields`.
- `game/prompt_context.py:3083-3085` replaces the provider copy of `mechanical_resolution` with `_provider_mechanical_resolution(...)` when decision authority fields are present.
- `game/prompt_context.py:3086-3091` projects temporal provenance into the provider payload when buckets are non-empty.

## Conversation History Selection

- `game/prompt_context.py:217-225` sets `MAX_RECENT_LOG = 5`, `MAX_LOG_ENTRY_SNIPPET = 200`, `CONVERSATIONAL_MEMORY_SOFT_LIMIT = 12`, and `CONVERSATIONAL_MEMORY_MAX_CANDIDATES = 36`.
- `game/prompt_context.py:1086-1098` builds recent-turn candidates from the last capped recent-log entries and clips GM text snippets to 200 chars.
- `game/prompt_context.py:2587-2619` builds the conversational memory window contract, selects memory, and maps selected memory back to legacy recent-log rows.
- `game/conversational_memory_window.py` implements deterministic ranking by recency, active scene entity overlap, active interaction target, anchored interlocutor, explicit reintroduction, and stale/inactive penalties.

## Turn Packet

- `game/turn_packet.py:3-12` says the turn packet is a separate compact artifact for contracts, route hints, continuity snapshots, debug metadata, gates, retries, and diagnostics; it is not authoritative engine state and does not replace runtime resolution or validators.
- `game/turn_packet.py:50-66` defines `build_turn_packet(...)`.
- `game/turn_packet.py:80-88` constructs the `contracts` subtree from response-policy children.
- `game/turn_packet.py:113-125` embeds `response_policy`, `contracts`, and `debug` in the packet. In the saved provider requests this accounts for about 10.6k-10.9k chars every turn.

## PR-BS Measurement Continuity

- `PR-BS_cooperative_gm_micro_live_validation.md` records the three successful generation input token counts: 25,208; 27,795; 25,233.
- `artifacts/pr_bs_cooperative_gm_micro_live/evidence/model_calls.json` and per-probe digests record the live usage and acceptance outcomes.
