# Short multi-turn live gameplay validation

**A/PASS — LIVE MULTI-TURN VALIDATED.** Explicit authorization on 2026-11-18 allowed one pass. OpenAI `gpt-4.1-mini` returned `gpt-4.1-mini-2025-04-14` twice. Usage was 4,574 input, 404 output, 0 cached tokens, and $0.002476 estimated. No retries, fallback, narration, or provider errors.

One persistent session on the frozen fixture completed all five utterances. T1 and T4 were fresh live interpretations and each committed one examination. T2 and T5 answered the patrol fact from `clue_knowledge` with no gameplay time. T3 moved to Old Milestone. Final state: Old Milestone, both clues, turn 7, time-pressure 3. A duplicate of the T1 request replayed the original response with no second provider call and no state change.

T1's model record labeled the examination `GM/DESCRIPTION` while also proposing `INSPECT notice_board`. Existing reconciliation admitted the examination. T4's record was `GM/ACTION` with `INSPECT prints`. Neither record was edited.

## Earlier continuation checkpoint

**AWAITING LIVE AUTHORIZATION.** The continuation rechecked the frozen sequence on current code and made zero provider calls.

Fixture and manifest hashes match the freeze. Campaign `d4b0f326006cc6695085801d` still starts as Galinor at Cinderwatch Gate District, Day 1, turn 4, with an empty clue ledger, the notice board, the Old Milestone exit, and the footprint target. One isolated persistent session then showed the current routes: T1 and T4 reach the interpretation boundary; T2 and T5 return `discovered_clue_recall` from `clue_knowledge` before the interpreter; T3 binds the patrol exit and arrives at Old Milestone. T1 used the retained N1 record and T4 used the authored mock only to keep that session moving. Neither is a fresh live interpretation. Final instrumentation state was Old Milestone, both clues, turn 7, and time-pressure 3. Provider attempts, tokens, network attempts and estimated cost were zero.

Live turn scores remain **NOT TESTED**. The earlier preparation record below is historical. Its T5 absent-NPC result predates the recall repair and is not the current route.

## Historical preparation record

**PREPARED/BLOCKED.** Separate live authorization is absent. Zero provider attempts or charges.

Five interactions ran through the normal player HTTP route on one isolated persistent fixture during offline preflight. T1 used the exact historical N1 record. T2 and T4 used explicitly authored mock records. T3 and T5 were deterministic. T1, T3 and T4 each committed one resolver consequence and one turn/world tick. Reloads confirmed both clues, arrival at Old Milestone and an uninterrupted timeline from turn 4 to 7. The informational turns caused no gameplay mutation.

T2 answered using the T1 public reply. T5 mistook a request to recap the notice for a conversation with an absent NPC. It skipped interpretation and failed to use the still-persisted clue. This is a player-facing failure already observable offline. It limits the prospect of a full pass on the frozen route.

Three turns are eligible for live interpretation. Run the same frozen sequence once only after explicit approval and mandatory provider preflight. Performance, scoring, source inventory and exact regression identities are in the companion reports.
