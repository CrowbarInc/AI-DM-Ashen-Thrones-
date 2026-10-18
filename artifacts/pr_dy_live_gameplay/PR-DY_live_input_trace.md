# PR-DY live input trace

Ordinary text entered in the existing page follows this path. The gap before this cycle was step 4: production chat never called the PR-DO/PR-DR interpreter.

1. Browser submission. `static/app.js` `sendChat()` posts `{text, ui_mode}` to `/api/chat?ui_mode=player`. The page is `static/index.html` served at `/`. No UI rebuild.

2. HTTP endpoint. FastAPI `game.api:chat` receives the body. The live server was `python -m uvicorn game.api:app --host 127.0.0.1 --port 8765` with `ASHEN_DATA_DIR` pointed at `artifacts/pr_dy_live_gameplay/disposable_data`.

3. Communication mode. `_resolve_communication_mode` returns IC, OOC, or AUTO. Prefixes `IC:`, `OOC:`, `In character:`, and `Out of character:` are case-insensitive. Explicit OOC returns `_nonmutating_ooc_response` before interpretation, parsing, and turn advance.

4. Live interpretation. For AUTO and explicit IC, `interpret_production_turn` builds the existing PR-DR catalog prompt from the PR-DU visible catalog, requests one structured completion, and adapts it with `adapt_interpretation`. This call was absent from production chat before PR-DY. It stays absent while live interpretation or provider calls are disabled.

5. Authority validation. Eligibility dispositions other than a single eligible component block execution. Explicit IC forces the payload communication mode to `IN_WORLD_ACTION` before adaptation, so the model cannot relabel an explicit IC message as OOC. Clarification, unsupported operations, and unresolved references still block. The PR-DU bridge then binds the component to a visible catalog row. A rejected bridge does not execute.

6. Gameplay resolver. An accepted bridge action is locked. INSPECT of a clue-bearing interactable uses the existing investigate resolver. ASK uses the existing question resolver. The phrase-parser cascade does not run while the action is locked.

7. Persistence. Resolver results are written through the existing session save. The disposable session after the live turns has `turn_counter` 3, `time_pressure` 3, scene `frontier_gate`, and `clue_knowledge.notice_patrol_route.state` `discovered`.

8. Response generation. Narration still goes through `call_gpt`. Under the 8,000 input-token ceiling those prompts are refused before send. Inspect and ask then show the resolver's own player text. Narration text is not applied as a state mutation.

9. Browser display. The response is rendered in `#chatLog`. The four player messages and the GM replies below were read from that log and from `disposable_data/session_log.jsonl`.

## Messages observed on the live path

- "I take a closer look at the notice board." AUTO, INSPECT `notice_board`, discover_clue.
- "I ask the captain what he thinks happened to them." AUTO, ASK `guard_captain`, question. The interpretation names the missing patrol, which was the clue from the previous turn.
- "How does searching work at the table? I'm not doing anything in the scene." AUTO, disposition OUT_OF_CHARACTER, no state change.
- "OOC: please leave the scene exactly as it is." Explicit OOC, no interpretation call, no state change.

These were automated browser submissions during verification. They are not a human playtest.
