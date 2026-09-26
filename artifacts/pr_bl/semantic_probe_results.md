# Semantic Probe Results

Fixture scenes are `ferry_landing` / `bell_loft` unless a row says the authored Frontier Gate file. That file is used only to prove the existing rumor exit still binds. The repair does not special-case it.

| Probe | Input | Result |
| --- | --- | --- |
| A | `I proceed northwest.` | `travel`, destination `northwest`, `resolved_transition` not true, no scene change |
| B | `I proceed North-West, as the runner directed.` on Frontier Gate | `travel`, not `old_milestone`, no transition |
| C | `I follow the northwest mud track.` | `scene_transition` `old_milestone` |
| D | `I follow the missing patrol rumor.` | `scene_transition` `old_milestone`, `resolved_transition` true |
| E | `I'll head northwest.` | `travel`, no target, no transition |
| F | `I go to the old milestone.` and `I proceed toward the bell loft.` | authored targets `old_milestone` and `bell_loft` |
| G | `I walk a few steps closer to the crates.` | `custom` / `local_physical_movement`. Narration `You step closer to the notice board.` is kept |
| H | `I proceed with the inspection.` | not travel. `I proceed with caution.` is not travel. `I proceed to question the guard.` is not scene travel |
| I | kind absent, model claims a road that stretches ahead and steps into a new stretch | player text is `That destination is not available from here.` |
| J | same authority, scene_update with reached-road, clue, hidden watcher, `mode: exploration` | those fields are not adopted. Scene id stays `ferry_landing` |
| K | no transition, visible fact `The mooring ring has worked loose.` | fact is adopted |
| L | `resolved_transition` true, arrival narration plus a non-claim visible fact | narration and the fact stay |
| Cascade | `I proceed north.` Model claims the cedar mill and proposes mill facts | scene stays `ferry_landing`, visited scenes do not gain the mill, narration does not say the mill was reached, overlay does not store the mill clue |

`We proceed north.` is travel with destination `north` and no exit bind. `I proceed along the northwest mud track.` is unresolved travel. It does not invent `old_milestone`. Follow/pursue still does, through the existing matcher.
