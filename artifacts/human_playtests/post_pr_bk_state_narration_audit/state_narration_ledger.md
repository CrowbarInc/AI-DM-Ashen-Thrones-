# State ↔ Narration Ledger

Session `735ebd1cfb4567c4f97df6dc`. Categories:

- A — explicit authoritative state or content
- B — deterministically derived from that state
- C — authorized presentation detail
- D — unsupported actionable world assertion
- E — unsupported non-actionable flavor
- F — contradicted by authoritative state

D and F rows record later reliance.

---

## TURN 00

| Claim | Class | Basis |
| --- | --- | --- |
| Player stands just outside Cinderwatch's eastern gate | A | Opening seed and scene location |
| Rain, soot-dark stone, frayed banners | A | Opening seeds |
| Refugees, wagons, guards holding the choke | A | Opening seeds |
| Townhouse with noble colors | A | Opening seed |
| Threadbare figure watching packs and faces | A | Opening seed |
| Notice board lists new taxes, curfews, and a missing-patrol warning | A | Opening seed and visible fact. No hours, districts, or route |
| Tavern runner offers hot stew and rumors by a rain barrel | A | Opening seed and visible fact |

No D or F claims. The word "strict" on curfews is presentation of the authored "curfews" / "curfew rules" (C).

## TURN 01

| Claim | Class | Basis |
| --- | --- | --- |
| The board is weathered, with decrees and handwritten scraps | C | Surface flavor. The board exists |
| New taxes imposed this month | C | "New taxes" is authored. "This month" adds no actionable rule |
| A schedule for the town's strict curfew hours | D | Visible text says the board lists curfew rules. No hours are authored |
| Patrol missing near the northwest mud track past the nearby crates | D | That sentence is discoverable clue `notice_patrol_route`. This turn did not discover it. It is not a visible fact |
| Gate serjeant watches the crowd | A | Visible fact |
| Roster of patrolling guards pinned nearby | C | Visible fact already names the roster board |

D claims:

1. Curfew-hour schedule.
   - Turn introduced: 01
   - Exact claim: `a schedule for the town's strict curfew hours`
   - Authoritative evidence: visible fact and opening seeds name curfew rules / curfews only. No hours in `data/` scene content.
   - Player later relied: yes
   - Later dependent turns: 02, which asks what times are limited and which parts of Cinderwatch

2. Northwest route past crates, presented as already read.
   - Turn introduced: 01
   - Exact claim: patrol gone missing near the northwest mud track past the nearby crates
   - Authoritative evidence: clue text exists; `discovered_clues` on this resolution is empty; `clue_id` null
   - Player later relied: the route is used from turn 03 onward, but turn 02 discovers the same sentence authoritatively. Later travel does not depend on the leak alone.
   - Later dependent turns: 02 is the direct read attempt. Turns 03 and 06 also use the route after it is discovered.

## TURN 02

| Claim | Class | Basis |
| --- | --- | --- |
| Threadbare watchers and refugees along the muddy gate line | A | Visible fact |
| Gate serjeant manages the crowd and watches the roster board | A | Visible fact |
| The missing patrol was last seen taking the northwest mud track past the crates | A | This turn's `discover_clue` result for `notice_patrol_route` |
| Curfew times or districts | absent | Asked, not stated. Not a false positive claim. The failure is substitution, recorded in the audit, not a D sentence of its own |

The patrol sentence is A as a discovery and F as an answer to the curfew-hours question: the player asked for times and districts, and the emitted examination result is a different subject. Recorded as F for answer-relevance, not for the sentence's truth.

F claim:

- Turn introduced: 02
- Exact claim: the examination of the curfew section yields the patrol route
- Authoritative evidence: `notice_board.reveals_clue` is only `notice_patrol_route`. `referenced_surface_target` is `curfew`. `skip_unrelated_clue_discovery` is false. No hours exist to reveal.
- Player later relied: yes. The route becomes the thread the runner is asked about and then followed.
- Later dependent turns: 03, 04, 06. Turn 06 would still be rational after a correct board reading, because the clue is real. The curfew question itself is not answered on any later turn.

## TURN 03

| Claim | Class | Basis |
| --- | --- | --- |
| Tavern Runner spoke | A | `tavern_runner` was resolved and present |
| Word is, the patrol took the northwest mud track past the crates | A as fact, not as an answer | Discovered clue. It is not the runner's topic sentence, and it is not city-navigation knowledge |
| This is what a stranger should know to get around the city | F | The question asked for city orientation. The only emitted fact is the patrol route |

F claim:

- Turn introduced: 03
- Exact claim: the runner's answer to getting around the city is the patrol route
- Authoritative evidence: runner topic is the muddy-footprints rumor. Resolution `reply_kind` is `refusal`. `topic_revealed` null. Dimension `general`.
- Player later relied: yes. Turn 06 says `as the runner directed`.
- Later dependent turns: 06. The direction is also in the discovered clue, so the player had a second source.

## TURN 04

| Claim | Class | Basis |
| --- | --- | --- |
| Tavern Runner cannot answer how many soldiers disappeared | A | No count is authored on the runner, the clue, or the scene |
| Opening `No.` | C | Awkward frame on a real refusal |

No D or F in the player-facing line. The stored `last_answer` (half a dozen, a captain inside the gate) is unshown generative text with provenance `generative_reply`. It is not a player-facing claim.

## TURN 05

| Claim | Class | Basis |
| --- | --- | --- |
| Gate Guard is the speaker | F as continuity | Gate Guard is present, so the speaker exists. The player did not address that NPC. The prior interlocutor was `tavern_runner`. |
| Gate Guard shrugs | C | Refusal shape. No reward content was invented in the player-facing line |
| A reward exists or does not exist | not stated | The shrug does not assert a reward. Content has no reward. |

F claim:

- Turn introduced: 05
- Exact claim: the answer comes from Gate Guard
- Authoritative evidence: `declared_switch_detected` false, `spoken_vocative_detected` false, `target_actor` `gate_guard`, reason `directed_social_question`, grounding `authoritative_speaker_eligible_topic_salience_ignored`
- Player later relied: no. Later turns do not speak to the guard by name. Turns 08–09 display `The guard says` from an empty speaker label, not from this shrug.
- Later dependent turns: none for the reward content. The stored banner paragraph on this topic was not shown.

## TURN 06

| Claim | Class | Basis |
| --- | --- | --- |
| Player threads the crowd in the drizzle and mud | C | Crowd, rain, and mud are authored at the gate. Local movement through them would be flavor if the player stayed |
| Turning northwest, the player passes crates at the edge of the gate district | D | No transition. Crates are words in the clue, not a passed location |
| Mud track stretches ahead | D | Names progress onto the track. Scene id did not change |
| Storage sheds | D | Not authored in `frontier_gate` or `old_milestone` |
| Flickering lanterns on crooked poles | D | Not authored in either scene |
| Broken patrol banners nailed to crates | D | Not authored. Not in the clue |
| Player's steps enter the stretch where the soldiers were last seen | F | `resolved_transition` is null. `visited_scene_ids` stays `frontier_gate`. `old_milestone` was not entered |

D/F claims, all introduced on turn 06:

| Claim | Player relied | Later turns |
| --- | --- | --- |
| Player is proceeding northwest along the mud track | yes | 07, 09 |
| Crates are being passed now | yes | 07 |
| Sheds and lanterns line the track | no direct interaction | none |
| Broken patrol banners are physically present | yes | 08 |
| Player has reached the patrol's last known stretch | yes | 07, 08, 09 |

The same turn wrote the arrival sentence, the banner clue, a hidden watcher, and `mode: exploration` into the runtime overlay. Those overlay strings are not authored content. They are model `scene_update` adopted after the narration.

## TURN 07

| Claim | Class | Basis |
| --- | --- | --- |
| The patrol was last seen taking the northwest mud track past the crates | A | Discovered clue, repeated |
| Any crate is open or rummaged | not stated | The question was not answered. No false opened/closed claim |

No new D object. The reply treats the route sentence as the response to a crate inspection. That is an answer substitution, not a new world fact.

## TURN 08

| Claim | Class | Basis |
| --- | --- | --- |
| The guard says they do not know how the banner was destroyed | F | No resolved speaker. `speaker_label` default is `The guard` when `npc_id` and `npc_name` are empty. Resolution kind is `custom`, not social |

F claim:

- Turn introduced: 08
- Exact claim: a guard spoke
- Authoritative evidence: `target_actor` null, social object empty, `active_interaction_target_id` null, final source `anti_reset_local_continuation_fallback`
- Player later relied: no further question is put to that guard
- Later dependent turns: 09 repeats the same line. It does not create a stored guard interlocutor (`current_interlocutor` ends null)

The approved `scene_update` again adds the banner clue. The player did not read that sentence on this turn.

## TURN 09

| Claim | Class | Basis |
| --- | --- | --- |
| The guard says they do not know enough | F | Same empty-speaker catalog line. Kind is null. No path was resolved |
| The path continues or the player advances | not in the player-facing line | The player asked to continue. The output does not narrate movement. Overlay still adds arrival and banner visible facts the player does not see |

F claim: same display attribution as turn 08. No new geographic sentence in the player-facing text.
