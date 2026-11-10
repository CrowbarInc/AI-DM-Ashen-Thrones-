# Plan Representation

Each step carries an identifier, the player wording, a proposed action, a target reference, the intended outcome, explicit and inferred dependencies, preconditions, mechanical requirements, execution status, the authoritative result, a consequence reference when one exists, a failure reason, and publication status.

`physical_plans` stores the record on the ledger. A proposed plan is not published as a completed fact. Successful steps publish only the consequence the adjudicator committed.

"continue" and "resume the plan" do not execute leftover steps. The player must say the next action.
