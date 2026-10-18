# 07 — Corrections and Pending Intentions

Pending ambiguous asks are stored as `pending_clarification` and `pending_intention` with kind `ambiguous_addressee`. A committed turn writes `last_executed_intention` before the turn counter increments. Scene-scoped pending records are what confirmation and correction read.

## Confirmation

- “Yes.” with one pending candidate executes that candidate (`confirmed_pending_addressee`). The bridge receives `authorized_target_id` so it does not re-ground the original ambiguous sentence.
- “Yes.” with two candidates clarifies: “Yes does not choose among them.” Nothing is attempted.
- “Yes.” with no pending proposal clarifies and does not invent an operation.
- Live was not required to say “Yes.” The live clarification used the name “The sergeant.”, which matched Sergeant Mara and not Corporal Bren, including after save/load.

## Correction

“Instead, make that a question about the lamp.”

- Against an unexecuted ambiguous ask: the pending record is revised, status stays pending, the superseded ask is not executed, and the world does not tick.
- Against `last_executed_intention`: “That action already resolved, so I cannot undo it.” Live turn 7 matched this after the clarified ask had executed. Turn counter stayed 3.
- With nothing pending: the engine asks what to change and does not answer with the lantern description.

The vocative “Instead,” is not treated as a person. Compound corrections of the form “Replace the first step with a question to Mara.” still rewrite the pending compound’s first step to ASK and leave the MOVE, without executing either. `question to` is a speech address so that rewrite stays grounded.

## Withdrawal

“Never mind, forget that question.” clears the pending ask and does not execute it.

## Stale proposals

A new bridged action clears an older unexecuted proposal. Confirmation of a pending record whose scene id does not match still clarifies. The existing compound confirmation test still executes the saved first step once and does not replay it after withdrawal.
