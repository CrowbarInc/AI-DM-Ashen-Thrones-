# Summary

Milestone: `pr_play_actionable_request_coverage_contract`.

Verdict: **B/PARTIAL**.

Feasibility passed. The existing conversational admission owner can withhold a selected operation when the original request still contains another command, using structural spans and the cue families already on that owner. Approach A (metadata only) would not have stopped singleton travel. Approach C (more verbs, including throw and put down) was rejected.

Production edits: `game/conversational_orchestration.py` and the existing `full_request_admission` call in `game/api.py`, which now receives the world and session already loaded for the turn. Tests: `tests/test_compound_action_admission.py`.

Before the edit, four requests traveled to market quarter and left the coat in inventory. After the edit they stay at the frontier gate, turn 4, clocks unchanged. The original "I drop my coat and enter Cinderwatch" stays withheld. Controlled HTTP: 75 requests, 76 assertion rows, 0 failures, 0 provider calls. Fresh-process reload holds, and a later explicit enter still arrives.

The partial mark is the sequence and the forty-probe comparison, not a leftover coat-and-travel move. "I abandon buying stew and return to the patrol question" is withheld because "return" is a travel cue. The next question, "What did the captain say about the patrol?", is then answered by the tavern runner. One primary probe, abandon-the-inquiry and ask about stew, changes from a partial NPC line to a stock refusal. SUCCESS stays 12/40. Minimum quality 21/40. Mean actionability 1.650/3. Supplementary visible text is unchanged: 18 / 5 / 3 / 17 / 5 / 4 / 3.

Combined regression: 408 passed / 17 failed, same identities as the predecessor, 0 provider records, no external sockets.

Reports in this directory. Machine evidence in `artifacts/pr_play_actionable_request_coverage_contract/`.
