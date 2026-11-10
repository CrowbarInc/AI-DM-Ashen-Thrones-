# PR-PLAY-72V — PERSISTENCE AND RESUME

Both HTTP campaigns save, restore, continue and cross-load using the existing snapshots API. Both browser campaigns use Save Slots, reload and Load followed by typed actions. browser_persistence.json compares exact timestamp/input/assistant-text order against each saved log: 8/8 A turns, 11/11 B turns and 8/8 A on cross-load, all exact. Identity/world/character/combat checks pass.

Final-source resumed browser questions on both branches are read-only; repeats do not duplicate discoveries, journals, inventory or branch effects. Existing normal ticks for actions remain permitted. Isolated lifecycle/Windows atomic-write/rollback results are reported separately in regression_results.json.
