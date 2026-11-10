# Narrow repair and finite safety extension

Skip public_observation and player_knowledge in must_communicate; retain original immutable anchors for safety. Resolver-selected facts remain mandatory even if already in post-state. Current engine_status still requires no-new outcome and repeat continuity. Inventory coverage unchanged.

No change to mandatory_outcome_coverage.py, deterministic resolution, inventory projection or validation precedence. PASS requires semantic PASS, legacy hard_valid and coverage PASS.

Offline isolation found a pre-existing gap: “was last seen taking” route text passed without an authorized route. preexisting_route_gap.json records it; nothing published. Added that finite reported-movement form to existing _route_assertion. It closes the tested negative but causes conservative false rejection of the live “You study ... and learn that” discovery: the existing token check evaluates the whole introductory clause. This new runtime regression remains documented and deferred after source freeze. No broad validator rewrite.
