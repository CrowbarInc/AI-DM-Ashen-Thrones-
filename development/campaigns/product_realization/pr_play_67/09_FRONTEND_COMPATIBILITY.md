# FRONTEND COMPATIBILITY

static/app.js was inspected and left unchanged. It reads character.hp/ac/attacks/spells/skills/inventory, public scene header/summary, session response_mode/active_scene_id, save summaries/snapshots, player name, ui affordances/living enemies/NPCs/interaction, and journal facts/clues/leads/status. These have explicit projected representations. Optional resolution details now display {}; internal GM metadata has no legitimate player display purpose.

World factions/projects/events were convenience reads of raw internal structures; they now render existing empty-state UI because visibility is not established. The scene picker lists known locations only. No UI redesign was introduced. Existing frontend static contract tests, backend mode tests and snapshot tests run in the boundary lane.

Browser-originated smoke observed the real app rendering current scene, character/inventory, notice-board action, existing patrol exit and exact discovered milestone journal text. A structured milestone action narration refusal reproduces unchanged in the entry source; browser_entry_comparison.json and browser_smoke.png preserve evidence. HTTP separately verifies campaign reset/start, load/resume and safe errors; those were not browser-verified.
