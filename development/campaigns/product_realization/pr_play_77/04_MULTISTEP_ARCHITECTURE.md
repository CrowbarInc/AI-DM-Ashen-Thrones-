# Multi-Step Architecture

The path stays inside the existing owners:

1. Player text enters the initiative and controlled-improvisation request.
2. `plan_physical` interprets a bounded plan. The plan is proposed state only.
3. `commit_physical` walks eligible steps in order.
4. Each step calls the existing `_apply` path, which commits through the physical ledger.
5. The next step is planned again from the updated ledger.
6. `physical_plans` records statuses and sets `automatic_resume` false.
7. Player-facing text comes from the existing publication path.

The provider may propose an operation list. The host re-parses, compares the normalized operations with the deterministic plan, and adjudicates. A stamp is process-local. The provider does not write the ledger.

Combat blocks multi-step execution only. A single action is unchanged. No turn cost is invented. Multi-step play demonstrated here is noncombat exploration.

Statuses used: PROPOSED, READY, EXECUTING, SUCCEEDED, FAILED, BLOCKED, SKIPPED, UNSUPPORTED, CLARIFICATION.
