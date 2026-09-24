# Authoritative fact ledger

Sources: bundle `scene_definitions/frontier_gate.json`, `persisted_data/world.json`, and post-run `session.json`. No medieval plausibility.

Classes: A explicit, B derivable, C authorized presentation detail, D unsupported, E contradicted.

## Scene and time

| Claim | Class | Source |
| --- | --- | --- |
| Current scene is `frontier_gate` for the whole session | A | session `active_scene_id`; no transition |
| Date is `Day 1` | A | `session.current_date`. It does not change |
| A diegetic hour or time of day exists | D | `world.world_state.clocks` is not a clock face. `time_pressure` counts chats (1 through 8). PR-BE already settled that this is not a world clock |
| Rain at the eastern gate | A | opening seeds and visible framing |
| Frayed banners hang above the eastern gate | A | `opening_seed_facts` / `journal_seed_facts` |
| Those banners identify a house, faction, or person | D | no heraldic blazon, house, or faction mark is authored on the banners |
| "Banners likely once bore local authorities or nobles" | D | only in turn 1 `last_answer`, not authored, not shown |
| Player can read a time of day from the sky | D | no sun, hour, or weather-to-time fact |

## Notice board and curfew

| Claim | Class | Source |
| --- | --- | --- |
| A notice board is present | A | visible fact, opening seed, interactable `notice_board` |
| The board lists taxes, curfew rules, and a missing-patrol warning | A | `visible_facts[0]` and opening seeds. This is a list of topics, not the text of the rules |
| Alias `curfew notice` refers to `notice_board` | A | interactable aliases |
| Inspecting `notice_board` reveals clue `notice_patrol_route`: the patrol was last seen on the northwest mud track past the crates | A | `reveals_clue` + `discoverable_clues`. This clue was not revealed. `discovered_clues` stays `[]` |
| The board has no separate inspectable statute text | A | interactable has no `inspectable_text` |
| Curfew hours are dusk until dawn | D | not authored. Appears in turn 3 model prose and `last_answer` |
| Civilians must be off the streets | D | same |
| Violators face fines or detainment until morning | D | same |
| The curfew exists to curb unrest and bandit activity | D | same. Session clocks `unrest` and `danger` are 0 |
| A gate serjeant enforces those edicts | D as an enforcement fact | A gate serjeant managing the crowd is an opening/visible presence line. Enforcement of a dusk rule is not authored |
| Missing patrol last seen heading northwest | B if stated as the clue | The clue text is the northwest mud track. Turn 3's `last_answer` states a shortened form that was not landed in `clue_knowledge` |
| Taxes were freshly imposed | C at most | "new taxes" is authored as a listing. "Freshly imposed" as a dated event is not |

## People present

| Claim | Class | Source |
| --- | --- | --- |
| Tavern Runner is a world NPC at `frontier_gate` | A | `world.npcs` sole row. Location `frontier_gate` |
| Tavern Runner shouts offers of hot stew and paid rumor | A | opening seed |
| Tavern Runner's only authored topic is `patrol_milestone`: "The patrol never came back from the old milestone." Leads to `old_milestone` | A | `world.npcs[0].topics`. `known_topics` and `revealed_topics` at capture are `[]`. This topic was never revealed |
| `speaks_authoritatively_for_scene` for the runner on these turns | E if treated as scene authority | social profile says false |
| Refugees and a threadbare watcher are addressable scene actors | A | `addressables` `refugee`, `threadbare_watcher`. Presence `active` |
| A gate serjeant is described managing the crowd | C | visible fact and opening prose. There is no `gate_serjeant` addressable in this scene file |
| Guards hold the choke | C | opening seed. No individual guard NPC row besides the addressables below |
| Someone near the notice board is resolved as an addressee on turn 4 | E | `npc_id` null, `target_resolved` false |
| "The guard" is a bound interlocutor | E | display label only. No id, no runtime row, no `current_interlocutor` from turn 4 |

## Guard Captain

| Claim | Class | Source |
| --- | --- | --- |
| `guard_captain` is an addressable in `frontier_gate` | A | addressables. Name `Guard Captain`. Roles include `guard` and `captain`. Priority 0 |
| `guard_captain` is in `active_entities` with presence `active` | A | session `scene_state` at capture |
| `guard_captain` is a world NPC with location, topics, or availability | D | absent from `world.npcs` |
| The player has met the captain | D | no runtime row, no conversation |
| The captain keeps watch near the roster board | D | model prose and `recent_contextual_leads` only. Visible fact says the serjeant keeps an eye on the roster board, not the captain |
| The captain handles official talk | D | turn 6 model `last_answer` |
| The captain would answer a newcomer, requires an appointment, mingles, keeps to himself, or needs an introduction | D | turns 6–7 model prose. No relationship or access state changed |
| Tavern Runner is authored to know any of those captain facts | D | runner topics are only the milestone patrol sentence |
| Asking the captain is a landed lead | E if treated as a lead | `lead_registry` is `{}`. Fragments exist only as `recent_contextual_leads` of kind `active_event` |

## What play did not make true

No turn wrote a clue, a canonical lead, a revealed topic, a revealed hidden fact, a resolved interactable, a scene transition, a date change, or a relationship score. `npc_runtime.tavern_runner` attitude, trust, fear, and suspicion stay 0. Hidden facts (noble watcher, Ash Cowl, signal, spotter) stay unrevealed.
