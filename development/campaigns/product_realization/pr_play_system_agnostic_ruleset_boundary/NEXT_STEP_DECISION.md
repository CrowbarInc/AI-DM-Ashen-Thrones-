# Next-step decision

Do not start the next milestone from this handoff.

Primary recommendation: `pr_play_character_equipment_lifecycle_feasibility`.

The equipment policy and the ruleset boundary now exist. A lifecycle milestone may study one character-owned association only if it calls `evaluate_policy` on the selected ruleset, keeps unresolved mechanical consequences explicit, and refuses execution while readiness is blocked. It must not invent possession, treat a missing equipped field as unequipped, or call `evaluate_equipment_eligibility` from generic orchestration in place of the boundary.

Separately, the latest gameplay assessment still recommends `pr_play_authored_transition_recovery` for the play bottleneck. This milestone does not change that evidence and does not displace it. It is not started here.

Do not next migrate every Pathfinder module, add a plugin loader, or build a generic equipment action.
