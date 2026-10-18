PR-DU Single Turn Execution

Input: Let me get a better look at the lantern beside the gate.
Entry point: game.api.chat (the function behind POST /api/chat).
Stored interpretation: DR01.
Resolver: existing exploration resolver through _resolve_engine_noncombat_seam.
Result: PASS.

Verified by test_pr_du_single_turn_uses_production_chat_entry_with_stored_interpretation:
- input accepted
- stored interpretation consumed
- target validated as courtyard_lantern
- resolver invoked through production route
- session stayed in waystation_courtyard
- one log entry written
- no hidden facts exposed in response
