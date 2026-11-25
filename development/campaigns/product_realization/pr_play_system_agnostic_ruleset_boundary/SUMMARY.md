# pr_play_system_agnostic_ruleset_boundary

Verdict: **A/PASS**.

The Ashen Thrones core now has an explicit ruleset boundary. `game/ruleset_contract.py` defines identity, capability discovery, and side-effect-free policy results without importing a ruleset. `game/ruleset_registry.py` selects `pf1e` version `1`, `rules_light` version `1`, and `scifi` version `1` with no default and no Pathfinder fallback. Only `pf1e` version `1` delegates `equipment_policy`, and that delegation stays in `game/pf1e_equipment_policy.py`.

Padded armor remains eligible, mechanically unresolved, and blocked. `rules_light` and `scifi` are identity sentinels, not implemented game systems. They refuse the same equipment request. Unknown rulesets and unsupported versions are rejected.

The constitution's Ruleset Independence section was applied in place on 2026-11-13 under the existing amendment rule. It does not name modules or slot identifiers. RCR-15 is the implementation contract.

Contract matrix 53/53. Boundary tests 54/54. Existing policy tests 56/56. HTTP preservation 21/21 against the equipment-policy probe, with the inherited travel-coat turn advance still present and still not an equip success. Combined regression 455/17 before and after. Focused regression 470/1 before and after. Provider calls 0.

The turn spine does not call the boundary. Legacy combat, skills, conditions, non-combat resolution, and character import are named migration exceptions. No gameplay improvement is claimed. No next milestone was started.

Reports in this directory. Evidence in `artifacts/pr_play_system_agnostic_ruleset_boundary/`. The sealed archive hash is external in `archive_verification.json`.
