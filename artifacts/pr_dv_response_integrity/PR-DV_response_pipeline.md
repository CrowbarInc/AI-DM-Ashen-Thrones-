PR-DV Response Pipeline

Production path traced:

`game.api.chat()` increments gameplay counters only for normal turns, routes through stored interpretation or existing parsers, resolves via `_resolve_engine_noncombat_seam()`, mutates state in `_apply_authoritative_resolution_state_mutation()`, builds narration through `_build_gpt_narration_from_authoritative_state()`, then finalizes through `_finalize_player_facing_for_turn()` and later post-GM transforms in `_complete_opening_turn_persistence_like_chat()`.

Loss point:
- Resolver facts were present on `resolution` and persisted state.
- Generic narrator text survived final-emission layers because existing preservation handled only selected obligation and contract cases.
- Later post-GM transforms could reintroduce generic text after an earlier finalization repair.

Repair point:
- Added `_preserve_authoritative_resolution_facts_after_gate()` in `game.api_turn_support`.
- Called it inside finalization and again after late post-GM mutation/adoption in `game.api`.
