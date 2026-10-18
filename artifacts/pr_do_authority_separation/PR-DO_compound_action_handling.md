# PR-DO Compound Action Handling

Recognition of several attempts is not a transaction and is not execution.

DN01, sidle toward the notice board, then wrench it loose.

Components stay in order 1 then 2: `MOVE`, then `USE_VISIBLE_OBJECT`, both targeting `notice_board`. Disposition is `ELIGIBLE_FOR_VALIDATION`. `compound_transaction` is false. `execution_authorized` is false. The board is not removed and time is not advanced.

DN02, edge up to the gate, test the latch, and wave the guard over.

Components stay in order 1, 2, 3: `MOVE`, `INSPECT`, `SOCIAL_SIGNAL`. Disposition is `ELIGIBLE_FOR_VALIDATION`. The hope that the guard comes over is an unadjudicated requested outcome and is absent from the submission. The gate is not opened and the guard is not moved.

A compound that mixes an allowlisted class with an unsupported class, such as `ATTACK` plus `INVENTORY_GRANT`, is `UNSUPPORTED_OPERATION` for the whole turn. Both components remain in the record, in order. There is no partial submission and no transaction.

No compound executor was added.
