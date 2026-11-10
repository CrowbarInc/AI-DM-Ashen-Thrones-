# Implementation

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

Production changes: game/storage.py: route _load_json/bootstrap and _save_json character dispatch to existing atomic primitive; save_character takes existing persistence guard; _atomic_write_bytes uses exclusive same-directory temps, modes, cleanup and honest directory sync reporting. game/object_marking.py (new): pure schema/authorization/revision/digest/receipt validation and detached prepare_marking proposal. game/api.py: internal add_inventory_object_marking entry reloads in existing ordered_turn lane plus persistence guard, delegates validation, checks existing WORLD_STATE API mutation authority, commits candidate with existing runtime_commit_scope and save_character, verifies byte rollback on exceptions and returns committed result. No new authority in object_instances; state_authority.py and identity code unchanged.

Architecture refinements: use character receipt ledger rather than proposed session ledger because a single-file commit makes marking/receipt indivisible. Separate pure marking helper keeps the identity owner narrow; existing API remains the mutation coordinator. No ExplorationEngineResult/noncombat/CTIR changes because this cycle explicitly excludes conversational activation. No competing action result or publication system is introduced. Positive preconditions are trusted evidence references with explicit no-mechanics decision in controlled requests, not an installed adapter or physical adjudication engine.

No parser/routing/T04/T05/T06/ruleset/scene/equipment/travel changes. See authenticated incremental production.diff.
