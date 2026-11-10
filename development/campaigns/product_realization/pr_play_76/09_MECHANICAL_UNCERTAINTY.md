# Mechanical Uncertainty

`game.skill_checks.resolve_skill_check` is used only when `properties.skill_check` has a skill id and an integer DC. Boolean DCs are rejected. The seed uses turn, scene, target, skill, and DC. A DC of 30 with modifier 0 fails. A DC of 1 succeeds. The publication includes the roll only when a roll happened. `skill_check` is omitted from the result when no roll occurred.

A heavy movable object with no authored check returns category B and states that no strength check is configured. Nothing is lifted. No DC is hardcoded to force a demonstration.
