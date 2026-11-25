# pr_play_fresh_live_foundational_capability_validation

**EXECUTION: COMPLETE. INTEGRITY: PASS. CAPABILITY: MIXED.**

One fresh campaign, `ca6032632047ed6aa7ffe8e1`, ran for 20 player turns without a reset. The player could read the gate notice and travel twice. They could not get an answer from the tavern runner or the guard, and most other turns were clarifications or misreads.

| Measure | Result |
| --- | --- |
| Campaign / opening scene | `ca6032632047ed6aa7ffe8e1` / `frontier_gate` |
| Opening | Live candidate rejected (`safe_nonresolution`). Deterministic recovery published. |
| Player turns | 20/20 |
| Provider / model | OpenAI / `gpt-4.1-mini` wire snapshot `gpt-4.1-mini-2025-04-14` |
| Calls / tokens / retries | 14 / 59,732 / 0 |
| Spend | $0.0292472 of the $0.25 ceiling |
| Interpretation accuracy | 5/13 (38.5%) |
| Legitimate-action completion | 3/14 (21.4%) |
| Unnecessary refusal | 11/14 (78.6%) |
| Conversational continuity | 4/14 (28.6%) |
| Useful grounded responses | 4/20 (20.0%) |
| Unauthorized consequences | 0 |
| Median / P90 latency | 3.476 s / 3.947 s |

The historical 20-turn counts are unchanged as the baseline. On this sample, completion and unnecessary refusal match that baseline exactly. Interpretation and usefulness are lower. Continuity is slightly higher. Latency is a little faster. This is one campaign, not a significance claim.

Authorized consequences were the opening bootstrap, the notice-board clue on T06, the move to Market Quarter on T13, and the move to Old Milestone on T19. Refused turns spent nothing. Inventory, hit points, and combat did not change.

[Scores](evidence/scores.json) · [Compact turns](evidence/turn_compact.json) · [Comparison](HISTORICAL_COMPARISON.md)
