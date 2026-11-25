# Extended live continuity validation

**B/PARTIAL.** One authorized persistent session completed all twelve frozen utterances. HTTP 200 on every turn is not a pass. Ordinary looking did not execute, the patrol route was not available when the player asked for it, and the last turn answered a different question.

Fixture `frontier_gate_historical_n1`, SHA-256 `1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a`. Manifest SHA-256 `b770bfac015460006b0272600a414e145416c0a1e4f4ce3bbf1ca8309bc173b4`. One campaign id, `d4b0f326006cc6695085801d`, Galinor at the Cinderwatch gate, Day 1, turn 4, empty clue ledger. The frozen utterances were not rewritten.

Approved cap: OpenAI `gpt-4.1-mini`, 8 calls, $0.10, 24,000 input tokens, 600 output tokens, 45 seconds, retries off, fallback off, live narration off. Actual use: 5 calls, 11,966 input, 1,125 output, 0 cached, $0.0065864. Returned model `gpt-4.1-mini-2025-04-14`. No retries, fallbacks, narration calls, timeouts, or provider errors.

| Metric | Result |
|---|---|
| Turns | 12 completed, 0 dependency-blocked, 0 not tested |
| Genuine live interpretations | 5 (T01, T04, T08, T10, T11) |
| Deterministic interceptions | 7 (T02, T03, T05, T06, T07, T09, T12) |
| Successful live actions | 2 (T10 dialogue, T11 inspection) |
| Successful deterministic actions | 2 (T03 and T07 moves) |
| Legitimate consequences | 2 scene changes, 1 clue disclosure, 1 NPC topic plus existing lead, 4 world ticks |
| Unauthorized state writes | 0 |
| Prints clue | never discovered |
| Duplicate of T01 | same response, same state, no provider call |

Final state: `frontier_gate`, turn 8, time pressure 4. Clues: `notice_patrol_route`, `social_frontier_gate_guard_captain_patrol`, `lead_frontier_gate_old_milestone`. Inventory, hit points, and prepared spells unchanged. No canary text.

The first material failure is T01. The model named `INSPECT notice_board` and marked the turn GM/QUESTION. The host stopped at `unresolved_inspection_communication_conflict`. T02 and T06 then correctly said the route was not established. T11 stored the route later, on the first actual examination. T04 added a targetless MOVE and was refused. T08 published a gate fact beside the milestone mud sentence. T12 replayed the captain through `repeat_delivered_statement` and never reached the prints question.

The three faction agenda flags on T10 are the existing threshold of 3 after the third committed world tick. They are expected, not an unauthorized faction write.

Regression after the live run: combined 455/17, focused 470/1, scoped 191/0, recall acceptance 71/71. New failure identities 0. Missing baseline identities 0. No external network during the suites.

No production gameplay change, no new content, no commit, and no push. The narrow inspection-admission repair is not started. Social repeat and legacy stance stay paused.
