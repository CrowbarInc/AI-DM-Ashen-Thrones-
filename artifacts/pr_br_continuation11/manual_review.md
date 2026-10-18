# Continuation 11 manual review

Six completed live turns. Isolated session. No rerun.

| Turn | Contract correct | Response correct | Evaluator | Note |
| --- | --- | --- | --- | --- |
| 1 | YES | NO | FAIL | Ask the gate guard what is required tonight. Reply denies that anyone is present and describes the notice board. |
| 2 | YES | NO | PASS | Inspect the notice board for use. Reply is the canned "no reliable use" line. False PASS. |
| 3 | YES | YES | PASS | "What does it say about the curfew?" inherits the notice board on the fast path and the reply describes the curfew. |
| 4 | NO | NO | PASS | "Who from?" stays a bare ask and does not bind a source. False PASS. |
| 5 | NO | NO | PASS | "I take the step he suggested" stays a bare ask. Narration invents a physical step. False PASS. |
| 6 | NO | NO | PASS | "I ask him about it" binds the notice board and drops "him". Reply does not answer. False PASS. |

Correct contracts: 3/6. Manual player-visible PASS: 1/6. Evaluator PASS: 5/6. False PASS: 4. False FAIL: 0.

Model-assisted turns: 1 and 2. Both contracts were correct. Neither reply was useful.

State integrity: turn 1 stored active_claim as the interlocutor "Gate Guard". That slot persisted. The catalog already contained gate_guard, gate_serjeant, and guard_captain; the model selected an existing id.
