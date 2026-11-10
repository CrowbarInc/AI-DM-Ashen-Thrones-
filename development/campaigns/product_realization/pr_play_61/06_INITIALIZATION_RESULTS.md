# 06 Initialization

The isolated seed set `campaign_started`, scene `frontier_gate`, and turn counter 1, using the existing frontier-gate scene file and default character. `GET /api/state?ui_mode=player` returned 200 before the first action.

The player UI showed Cinderwatch Gate District, Galinor, Level 1 Wizard, HP 8/8, and no conditions. After the actions it showed one discovered clue and four log entries.

No initialization exception was recorded. The player-mode state projection did not expose `active_scene_id` at the key the experiment script checked. The saved session and the rendered scene title did.
