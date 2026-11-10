# PR-PLAY-20 response path

| Stage | Source / function | Input -> output; representation and consumer |
| --- | --- | --- |
| Admission | `game/api.py:6362`, `game/api.py:6366` | HTTP Request -> player-mode admission, preflight gate and opening scope; denies author/debug runtime actions |
| Initialization | `game/api.py:6406` | persisted campaign/session/world -> engine opening resolution and prompt; authoritative, internal |
| Publication | `game/api.py:5909` | accepted GM output -> committed session/world/log and canonical narration; internal full object |
| State retrieval | `game/api.py:4946` | engine storage -> full state plus derived public UI/journal fields; mixed visibility, internal until projected |
| Initial packaging | `game/api_turn_support.py:1382` | GM + optional resolution + full state -> flat mixed payload; raw `**state` is original disclosure entry |
| Enrichment | opening persistence tail | canonical GM replacement + emission metadata + log persistence -> completed internal response |
| Repaired boundary | `game/api.py:5035` | complete dict or JSONResponse -> recursively public copy, preserving rejection HTTP status and headers |
| JSON serialization | FastAPI response serialization / Starlette JSONResponse | public result -> UTF-8 JSON response consumed by browser |
| State reads | `game/api.py:5109`, `game/api.py:5024` | full snapshot -> `public_state` plus selected explicit lane; previously already projected |

The confirmed mechanisms are direct full-state merging and bypass of the public projection (A/B/C in
the mission taxonomy). There is no evidence that this was a debug response accidentally selected for
player mode. The current projection itself excludes `hidden_truth` by its `hidden_` prefix.

Existing client contract: static/app.js consumes top-level gm_output.player_facing_text and resolution
from runtime responses, then refreshes `/api/state`. State reads consume the public_state envelope.
The repair keeps flat runtime fields, including public campaign/character/session/world/scene/UI,
journal, save/snapshot and campaign synchronization metadata. It introduces no new response envelope.
