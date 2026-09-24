# NPC knowledge audit

Tavern Runner is the only world NPC. Authored knowledge is one topic: `patrol_milestone` / "The patrol never came back from the old milestone." That sentence is never revealed. `known_topics` and `revealed_topics` stay empty. `topic_revealed` is null on every social turn.

Guard Captain is an addressable id with presence `active` and no world-NPC topics. Nothing in this session authorizes another character to promise access to the captain.

Plausibility is not authority. "Authorized?" means the claim is that authored topic or a deterministic consequence of it.

| Claim | Authored source | Authorized? | Persisted? | Later reused? |
| --- | --- | --- | --- | --- |
| Runner hawks stew and rumor | opening seed | yes | opening text only | no |
| Patrol never came back from the old milestone | `world.npcs` topic | yes, and not used | no | no |
| Runner does not have the details of what sparked the curfew | none | no | turn 5 model text in the retry anchor and the player line | turn 6 reads that paragraph as `topic_pressure:last_answer` |
| Bandits getting past the gates is not the usual story | none | no | same | player already supplied the bandit premise from turn 3 |
| Ask the guard captain; he keeps a closer eye on that trouble | none | no | player line, retry anchor, `recent_contextual_leads` | turn 6 candidate source; player then asks about an appointment |
| Runner cannot say whether an appointment is required or whether the captain would speak to a newcomer | none | no | turn 6 `last_answer` | not separately re-emitted; the next sentence is |
| Captain keeps watch near the roster board | none. Visible fact gives the roster board to the serjeant | no | turn 6 `last_answer` and a contextual lead | stored, not the shown sentence |
| Captain handles official talk and might give you an answer | none | no | turn 6 `last_answer` | shown as `Word is` on the same turn |
| Captain's mingling with common folk is uncertain | none | no | turn 7 `last_answer` | not the shown sentence |
| Captain tends to keep to himself and his duties | none | no | turn 7 `last_answer` and a contextual lead | stored |
| Best bet is the roster board | none | no | turn 7 `last_answer` | stored |
| Do not expect an easy ear without some introduction | none | no | turn 7 `last_answer` | shown. `final_emitted_source`: `structured_fact_candidate_emission` |
| Turn 4 "I do not know enough" spoken by a guard | catalog line, empty speaker | the ignorance line is a refusal template; the speaker is not an NPC | player-facing only. `last_answer` for that topic is a different quantity template | no id to continue. Next "you" does not bind a guard |

No claim above changed `npc_runtime` knowledge fields. Reuse is conversational memory and structured-fact selection, not a revealed topic.
