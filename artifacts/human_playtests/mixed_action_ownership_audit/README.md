# Mixed-action ownership audit probes

Captured human turn (do not modify):

`artifacts/human_playtests/20260923_cinderwatch_crowd_observation_failure/`

Classification probes, persisted `data/world.json` roster (sole world NPC `tavern_runner`):

- `probe_baseline_persisted_world.json` — before the listen-question repair. The human turn is `question` / `question` path `dialogue_first`, addressed `tavern_runner`, reason `open_social_solicitation`.
- `probe_after_persisted_world.json` — after the repair. The human turn is `observe`, lane `human_adjacent_observe`, family `listen`, no addressed NPC. State does not change. The listen hint realizes only the authored runner shout about stew and rumor.

`probe_baseline.json` is an earlier run against `default_world()` (two world NPCs). That roster hides the sole-NPC fill. The persisted-world files are the production-roster evidence.

The driver was a disposable script under `development/tmp/` and is not repository evidence.
