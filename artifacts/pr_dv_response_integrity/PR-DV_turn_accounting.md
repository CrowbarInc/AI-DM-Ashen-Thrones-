PR-DV Turn Accounting

Expected behavior confirmed in focused inherited tests:

- Four gameplay actions advance `turn_counter` and `time_pressure` once each.
- Explicit OOC correction advances neither.
- Rejected stored interpretation advances neither.
- Scene transition preserves same-turn increments across `activate_scene`.
- No duplicate resolver invocation was observed in PR-DV focused tests.

Final PR-DU/PR-DV sequence state:
- `active_scene_id = waystation_street`
- `turn_counter = 4`
- `time_pressure = 4`
- `notice_board` resolved
