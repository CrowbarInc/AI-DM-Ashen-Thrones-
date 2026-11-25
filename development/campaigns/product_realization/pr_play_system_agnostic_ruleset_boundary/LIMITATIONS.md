# Limitations

- The turn spine does not consult the boundary. Combat, skills, conditions, non-combat resolution, and character import still run as legacy Pathfinder-oriented modules.
- `rules_light@1` and `scifi@1` are identity sentinels. They are not implemented game systems.
- No campaign document stores an active ruleset. Selection is an argument to each call.
- Mid-campaign switching, package installation, dependency resolution, permissions, sandboxing, and third-party loading are not implemented.
- Equipment actions remain non-executable. Padded armor stays mechanically unresolved and blocked.
- `supported` on a resolved incompatibility is a policy answer, not an authorization to equip.
- Architectural tests do not scan every future edit to `game/api.py`. A later caller could bypass the boundary by importing a legacy module, which is still the allowed migration exception until that module is migrated.
- The broad gameplay sample was not rerun. Applicability is argued from an unchanged runtime path, not from a fresh forty-probe.
- The constitution's reconciliation with the AI GM contract and AR-AD is the reading in `CONSTITUTIONAL_ALIGNMENT.md`. Those documents were not rewritten.
