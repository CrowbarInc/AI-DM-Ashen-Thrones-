# 01 Executive summary

**A — PASS / CONTROLLED GAMEPLAY DEMONSTRATED.**

An isolated copy of the frontier-gate campaign loaded through the application chat route. The player examined the notice board, the rain barrel, the notice board again, and the gate. The engine resolved each action. Two live narrations passed the existing integrated validators and were published. Two candidates failed validation. Their rejected text was not published. After a same-cycle repair, those turns publish the engine sentence instead of the provider-disabled stub. Replaying the saved provider text confirmed that repair without another provider call.

The experimental flag is off by default and is bound to one campaign run id. A second session in the same process kept its ordinary sentence. Inventory, hit points, scene, clues, and NPC attitude matched the provider-disabled control. The only identity difference is the campaign run id.

Provider use: 4 requests, 1663 input tokens, 263 output tokens, 1926 total, 0 retries. Average action-to-response time 2.601 seconds. Maximum 3.331 seconds. Quality is provisional and separate from the validator result: the two published turns are usable; the engine fallback reads as a fact list.

No critical safety failure. No commit and no push.

| Check | Result |
|---|---|
| A Flag disabled | PASS |
| B Flag enabled for one session | PASS |
| C Supported investigation | PASS |
| D Follow-up | PARTIAL — resolved, narration rejected, engine fallback used |
| E Repeated investigation | PASS |
| F Four-action sequence | PASS |
| G Valid narration published | PASS — 2 responses |
| H Invalid narration rejected | PASS |
| I Deterministic fallback | PASS after the same-cycle stub repair |
| J Timeout recovery | PASS |
| K Provider-error recovery | PASS |
| L Validation-error recovery | PASS |
| M State comparison | PASS |
| N Session persistence | PASS |
| O Frontend rendering | PASS — log rendered; one later input accepted |
| P Regression | PASS focused, 3 known failures; 9 known broader failures |
| Q Provider accounting | PASS |
| R Latency | PASS — recorded, not optimized |
| S Quality | PROVISIONAL |
