# Production Call Graph

Actual browser chat path:

1. `static/app.js:577` `sendChat()` posts JSON to `/api/chat`.
2. `game/api.py:5829` `api_chat()` resolves UI mode and delegates to `chat()`.
3. `game/api.py:5837` `chat()` enforces player runtime mode, resolves IC/OOC, loads state, snapshots interlocutor, and syncs scene addressability.
4. `game/api.py:5883` calls `interpret_production_turn()` when live interpretation is enabled and provider calls are allowed.
5. `game/live_chat_interpretation.py:207` builds visible catalog, recent visible turns, and structured provider request.
6. `game/live_chat_interpretation.py:294-327` adapts interpretation. Blocked dispositions return non-mutating clarification; multiple components return "Which single action...".
7. `game/player_interpretation_bridge.py:14-25` permits only `PERCEIVE`, `INSPECT`, `ASK`, `MOVE` and requires visible compatible targets.
8. `game/api.py:6071` otherwise chooses deterministic route: `dialogue`, `action`, or `undecided`.
9. `game/api.py:6094` establishes ordinary resolution contract; `game/ordinary_semantic_ownership.py:142` can use fast path and model proposal when allowed.
10. `game/ordinary_semantic_ownership.py:202` selects resolver family.
11. `game/api.py:6160-6470` tries permitted parser/resolver stages and rejects actions contradicting the contract.
12. `game/noncombat_resolution.py:496` delegates social/exploration noncombat resolution; `game/exploration.py:191` and `game/social.py:3834` own domain results.
13. `game/api.py:3922` `_run_resolved_turn_pipeline()` applies authoritative mutation and builds narration.
14. `game/api.py:2755` `_build_gpt_narration_from_authoritative_state()` constructs CTIR, narration-plan bundle, prompt context, and calls GPT.
15. `game/gm.py:4997` `call_gpt()` sends narration unless provider calls/budget disable it.
16. `game/api.py:3240-3705` validates/repairs narration through preservation, targeted retry, and fallback repair.
17. Response assembly persists log/session/world/combat and returns `gm_output.player_facing_text`.

Start Campaign path: `static/app.js:649` posts `/api/start_campaign`; `game/api.py:5592` builds a `scene_opening` resolution and uses the same resolved-turn pipeline. Chat has an exact cue recognizer at `game/api.py:4157`.
