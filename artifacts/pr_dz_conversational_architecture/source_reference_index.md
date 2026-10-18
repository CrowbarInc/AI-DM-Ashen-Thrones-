# Source Reference Index

Primary production files:

- `static/app.js:577` chat submit posts `/api/chat`.
- `static/app.js:649` Start Campaign button posts `/api/start_campaign`.
- `static/app.js:722` affordance submit posts structured `/api/action`.
- `game/api.py:4157` `_is_campaign_start_turn_request` exact chat start recognizer.
- `game/api.py:4215` opening-scene normalized action/resolution builder.
- `game/api.py:4248` fresh-session start eligibility.
- `game/api.py:4676` structured action endpoint handler.
- `game/api.py:5592` `/api/start_campaign` lifecycle endpoint.
- `game/api.py:5829` `/api/chat` endpoint.
- `game/api.py:5837` production `chat()` path.
- `game/api.py:5883` live interpretation call.
- `game/api.py:6071` coarse interaction route selection.
- `game/api.py:6094` ordinary resolution contract establishment.
- `game/api.py:6470` resolved-turn pipeline invocation for parsed chat action.
- `game/api.py:2755` narration from authoritative state.
- `game/api.py:2269` manual play GPT call cap.
- `game/api.py:3285` narration GPT call budget check.
- `game/live_chat_interpretation.py:207` live production interpretation connector.
- `game/live_chat_interpretation.py:309` generic clarification fallback.
- `game/live_chat_interpretation.py:324` multi-component rejection.
- `game/player_interpretation_bridge.py:14` connected operations.
- `game/player_interpretation_bridge.py:36` visible catalog construction.
- `game/player_interpretation_bridge.py:124` unsupported-operation rejection.
- `game/ordinary_semantic_ownership.py:59` resolver-stage table.
- `game/ordinary_semantic_ownership.py:142` contract establishment.
- `game/ordinary_semantic_ownership.py:202` resolver selection.
- `game/interaction_routing.py:365` chat lane selection.
- `game/interaction_routing.py:409` dialogue-first action builder.
- `game/prompt_context.py:217` recent-log prompt cap.
- `game/prompt_context.py:2549` conversational memory contract.
- `game/prompt_context.py:2571` conversational memory selection.
- `game/semantic_interpreter.py:127` recent visible turn extraction.
- `game/social.py:3834` social action resolver.
- `game/exploration.py:191` exploration action resolver.
- `game/gm.py:4997` provider narration call.
- `game/provider_budget.py:18` provider-call disable/budget controls.

Runtime/data evidence:

- `data/session_log.jsonl`: playtest traces, including successful notice-board/social turns and failed movement multi-component rejection.
- `data/session.json`: active scene and active social target after playtest.
- `data/scenes/frontier_gate.json`: visible facts, opening facts, exits, addressables, interactables.
- `data/world.json`: NPC topics and event log.
- `artifacts/pr_dy_live_gameplay/raw_live_responses.json`: existing provider telemetry snapshots.
- `artifacts/pr_dy_live_gameplay/PR-DY_regression_results.md`: inherited 29-failure regression cluster.
