# 04 — Production Integration Evidence

Actual transport: FastAPI TestClient POST `/api/chat?ui_mode=player`. One disposable authored campaign includes the gate, barred side gate, concerned Sergeant Mara, lantern and reachable waystation street. Runtime fixture paths are confined to a temporary directory in `development/tmp`; no active save is used as provider context. The script restores interpretation mode after historical experiment imports disable it.

`live_ten_turns.json` and `live_final_ten_turns.json` contain real provider raw interpretations, full resolutions, response text, state differences and usage records. These are failed development runs and remain included. `final_recorded_http_ten_turns.json` replays the second run's exact raw interpretations against final code; narration is associated with the corresponding recorded turn. No stored-interpretation bypass or manual player-message rewriting is used. Adapter, orchestration, bridge, resolvers, HTTP serialization, persistence and final emission are real.

The final replay routes turns 1/2/3/6/8/9 through non-mutating conversation; 4/5 through visible-NPC ASK and social authority; 7 through inspection/discovery; 10 through authoritative movement with no redundant narration request. Turn five now uses the NPC's selected previously revealed authored topic, revalidated against the current NPC/runtime. Turn six answers with that established topic instead of attributing a new NPC utterance.

Limits: recorded-provider execution is stronger than isolated unit tests but cannot prove the final prompt/model will choose the same records on a fresh run. The remaining live holdout recipient error prevents acceptance.
