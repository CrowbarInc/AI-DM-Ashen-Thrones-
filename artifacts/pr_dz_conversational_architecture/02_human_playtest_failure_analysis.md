# Human Playtest Failure Analysis

Observed cases:

1. Campaign initialization: plain text start requests returned "I need a clearer action or target...". The code now has `/api/start_campaign` plus a chat recognizer for exact start cues. The UI Start Campaign button calls `/api/start_campaign`; ordinary chat calls `/api/chat`.
2. Notice-board inspection succeeds because it maps to a visible interactable (`notice_board`) and deterministic exploration resolves `discover_clue`.
3. Repeated inspection succeeds mechanically but can repeat because the resolver/prompt stack tracks discovered/searched state while final narration has no product-level obligation to answer "you already checked that" unless response-delta/continuity catches it.
4. "I talk to Gate Sergeant" succeeds because it binds to a social target and the social resolver can emit the authored NPC topic.
5. "Who are the Ash Compact?" fails when treated as an unbound information request. In the current data, Ash Compact is a scene fact/topic phrase, not a canonical lore entity with a general answer.
6. Explicitly addressing the Gate Serjeant works because the utterance is reclassified as `ASK` with a social interlocutor.
7. "Angry, I leave..." fails as multi-component: the actual log shows live interpretation produced `SOCIAL_SIGNAL` plus `MOVE`; production returned "Which single action should I resolve first?" before mutation.
8. Latency is explained by sequential interpretation and narration calls, plus retry/repair loops after narration. Existing telemetry shows live interpretation calls around 2.4-3.2 seconds in PR-DY snapshots; this review did not create new measurements.

Runtime evidence: `data/session_log.jsonl`, `data/session.json`, `data/scenes/frontier_gate.json`, and `data/world.json`.

Inference: the system can perform action execution, but the conversational surface is brittle because non-executable or partially executable intentions are rejected at interpretation/bridge boundaries instead of being handled as conversational outcomes.
