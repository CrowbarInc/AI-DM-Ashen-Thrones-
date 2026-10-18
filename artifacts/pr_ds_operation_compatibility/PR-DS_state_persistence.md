# PR-DS State Persistence

Each of the ten replay rows wrote the disposable session, loaded it back, and matched the in-memory snapshot, the saved snapshot, and the history ids. Persistence failures: none. Final scene: `waystation_street`. `time_pressure`: 1. Turn counter: 4. Notice resolved: yes. Production saves were unchanged.

The disposable file is `artifacts/pr_ds_operation_compatibility/disposable_session.json`. It is not under `data/`.

## Meaningful world changes

Meaningful state here means scene, visited scenes, clocks, resolved interactables, discovered clues, inventory, hit points, combat, flags, and NPC runtime. Turn count and an empty scene-runtime shell are bookkeeping. `mutated_state` is true whenever the full authoritative snapshot changes, including bookkeeping.

| ID | Full snapshot changed | Meaningful change | What changed |
| --- | --- | --- | --- |
| DR01 | yes | no | Turn counter 0 to 1. Empty courtyard runtime shell. Scene, clock, clues, HP, and inventory unchanged. |
| DR02 | no | no | OOC correction. |
| DR03 | no | no | OOC mechanical request. |
| DR04 | no | no | OOC override over a stored ASK. |
| DR05 | yes | yes | Turn counter 1 to 2. `sergeant_mara` runtime gained `revealed_topics: ["street"]` and `trust: 1`. Scene and clock unchanged. |
| DR06 | no | no | OOC rules question. |
| DR07 | no | no | Unresolved clarification. |
| DR08 | yes | yes | Scene `waystation_courtyard` to `waystation_street`. Visited list gained the street. `time_pressure` 0 to 1. Turn counter 2 to 3. |
| DR09 | no | no | OOC retcon request. Street and clock stayed. |
| DR10 | yes | yes | `notice_board` added to the street resolved interactables. Turn counter 3 to 4. Clock stayed 1. |

No failed row advanced the clock. The only clock step is the accepted gate transition. OOC rows left the meaningful snapshot where the previous IC row had put it.

The stored DR10 interpretation, replayed on a courtyard session that had not crossed the gate, reloaded cleanly with the notice unresolved and the clock at 0.
