# State progression audit

Capture state is after turn 7. Per-turn deltas are the logged `state_changes` (empty on player turns that have them) plus fields that exist only in the final snapshot.

| Turn | Scene | Counter (`time_pressure`) | Date | NPC runtime | Topics revealed | Clues / leads | Interactables | Transition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `frontier_gate` | 1 | Day 1 | none yet | none | empty | none | arrive only |
| 1 | same | 2 | Day 1 | none | none | empty | not resolved. Action id later in `searched_targets` | no |
| 2 | same | 3 | Day 1 | none | none | empty | not resolved. Second `searched_targets` id | no |
| 3 | same | 4 | Day 1 | none | none | empty. Patrol clue not landed | `resolved_interactables` still `[]` | no |
| 4 | same | 5 | Day 1 | no row | none | lead landing empty | none | no |
| 5 | same | 6 | Day 1 | runner row by end: scores 0, topics empty, `last_interaction_turn` 8 | `topic_revealed` null | registry empty | none | no |
| 6 | same | 7 | Day 1 | same scores | null | registry empty | none | no |
| 7 | same | 8 | Day 1 | same | null | `clue_knowledge` `{}`, `lead_registry` `{}` | none | no |

Final social bindings that are real state, not clues:

- `current_interlocutor`: `tavern_runner`
- `active_interaction_target_id`: `tavern_runner`
- `entity_presence`: runner, captain, refugee, threadbare watcher all `active` (addressable roster, not discoveries)
- `topic_pressure`: five keys whose `last_answer` values are model paragraphs
- `recent_contextual_leads`: six `active_event` fragments cut from those paragraphs, plus `scene_npc_tavern_runner`
- `last_perception_turn`: null. This session never took the listen path

Clocks other than `time_pressure` stay 0. `visited_scene_ids` is only `frontier_gate`.

## How much progression existed only in prose?

All of the apparent investigation did.

The player hears curfew hours, penalties, a cause (unrest and bandits), a captain who watches trouble, a roster-board location, a role as the official speaker, and an introduction requirement. None of those are clues, leads, revealed topics, interactable resolutions, relationship changes, or clock facts.

What state actually records is: eight chats, two untargeted search stamps, a dialogue lock onto the only world NPC, and copies of the model paragraphs in `topic_pressure.last_answer` and `recent_contextual_leads`.

Low mutation would have been legitimate if the replies had been refusals or the authored patrol sentence. The prose asserted progress the registries do not contain.
