# PR-DP Remaining Risks

- `ELIGIBLE_FOR_VALIDATION` is still not execution, but a later consumer that ignores `execution_authorized: false` could run a submitted class. Eligible rows in this cycle: none.
- The model chooses `operation_class`. A sentence that asserts an NPC obligation can still be labeled with an allowlisted class. The adapter then submits that class without the premise text. That is a misroute risk, not an executed effect.
- `combat.ensure_target` falls back to the first living enemy. The slice design forbids that call. A direct connection of `ATTACK` would be unsafe.
- Intra-scene `MOVE`, `FOLLOW`, `SOCIAL_SIGNAL`, and free-form `USE_VISIBLE_OBJECT` are only partial. The designed slice avoids those branches.
- No live model output has been executed. Turn continuity, narration, and persistence of a played sequence remain undemonstrated.
- Selective gameplay routing was not redesigned and still is not the path that consumes this contract.
- Decision letter: G.
