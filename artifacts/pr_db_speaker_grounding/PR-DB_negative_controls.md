# PR-DB Negative Controls

All of these were run through the same deterministic `play_turn` helper. No provider calls.

| # | Case | Result |
|---|---|---|
| 1 | Explicit switch: "Tavern Runner, do you prefer the stew or the rain?" | Social target, allowed speakers, and active target become `tavern_runner`. `guard_captain` is not allowed. |
| 2 | Two names: "Guard Captain and Tavern Runner, which of you prefers the rain?" | At most one allowed speaker. |
| 3 | Departure | Removing the captain from world NPCs, scene addressables, and active entities, then `rebuild_active_scene_entities`, clears the interaction target. The follow-up does not authorize `guard_captain`. |
| 4 | Scene transition | `clear_for_scene_change` clears the target. The follow-up authorizes nobody. |
| 5 | Group: "Can anyone tell me if the rain makes watch harder?" | Directed entry reason is `open_social_solicitation`, not `active_interlocutor_followup`. Entry target is empty. The existing dialogue-first / open-call path can still bind one in-scene NPC. It does not invent an off-scene id. |
| 6 | Unrelated watch: "He keeps watching the gate for anything unusual." | Social route is false. Active target clears. Allowed speakers are empty. |
| 7 | Consequential: "Does the rain hide the cult's secret passage?" | Reply plan is not `harmless_subjective_response_permitted`. |
| 8 | Hidden-knowledge question about the threadbare watcher's signal | Reply plan is not the harmless-subjective plan. No reduced-context selection from that plan. |
| 9 | Authored factual question: "What happened to the missing patrol?" | Reply plan is not the harmless-subjective plan. |
| 10 | Physical: "I climb the gate wall." | Social route is false. Active target clears. Allowed speakers are empty. |
| 11 | Combat: "I attack the guard captain." | Social route is false. Mode becomes `activity`, kind `attack`, active target clears. Speaker selection can still name `guard_captain` because the attack action's normalized target matches that NPC. That is the existing explicit-target rule, not continuity. |
| 12 | Unresolved: "Does it get any easier after a while?" with no prior interlocutor | Allowed speakers empty. Social target unresolved. |
| 13 | Contradictory start: discourse `tavern_runner`, interaction target `guard_captain`, then the rain follow-up | The turn grounds `guard_captain` in the contract, social target, allowed speakers, active target, and the committed discourse slot. It does not authorize both. The stale discourse id does not win. |
| 14 | Missing NPC id `not_a_real_npc` | Allowed speakers empty. Social target unresolved. |
| 15 | Stale target after scene clear | Same as the scene-transition row. No speaker is authorized from the cleared target. |

Reduced context was not forced on any of these controls.
