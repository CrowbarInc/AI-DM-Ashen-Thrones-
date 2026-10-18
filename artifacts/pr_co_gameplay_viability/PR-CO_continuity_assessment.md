# PR-CO Continuity Assessment

Scope: turns 1–5 only. Turns 6–8 were not played, so waiting, a spoken continuity check, and a second physical action were not observed.

## What held

- Scene stayed `frontier_gate` / Cinderwatch Gate District.
- Guard Captain remained the social addressee on turns 1–3. Turn 4 moved interaction to investigate/focused and cleared the active target, which matches an examination.
- NPC roster, topic text, hidden facts, visible facts, HP, and inventory were unchanged.
- Turn 3 stored the authored patrol sentence and marked `guard_captain.revealed_topics` as `patrol`. It also stored the actionable lead "Investigate the old milestone."
- Faction pressure and agenda progress rose by 1 on every faction on every completed turn. Turn 5 appended three `faction_operation_complete` event-log rows. That is the existing clock, and the narration did not stage a fight or a new arrival around it.
- Turn 5's fallback uses the authored townhouse and threadbare-watcher facts. It does not add a confrontation or an inscription.

## What broke

- Turn 1's spoken record is two banner sentences. The preference the model offered was discarded, so turn 2 had no preference to refer to. The follow-up quote is the banner text, including the word "frayed."
- Turn 2's final line talks about "the wear." That phrase is the engine wear-dimension label, selected because "frayed" is in the wear lexicon. It was not written into scene facts.
- Turn 3's stored world says the patrol fact is discovered. The spoken line says the captain cannot answer from what is settled. Those two channels disagree.
- The contextual lead saved from turn 3 is the refusal fragment `guard captain says, "i cannot answer that from what`, not the patrol sentence. Turn 5 added a second `active_event` lead whose subject is the broken fallback sentence. Neither lead is an "as you" subject. Both are poor continuity anchors.
- Turn 4 did not add the notice-board wording to player-facing memory. The visible fact was already on the scene and stayed there.

## Classification of new material

| Item | Class |
| --- | --- |
| Banner sentences repeated on turn 1 | A. Cosmetic narration variation of authored facts, used as a substitute answer |
| Model preference for a dry watch, rejected | B. Harmless NPC opinion, not emitted |
| Model color about the gate being the first line of defense, rejected | C. Non-authoritative contextual detail, not emitted |
| "East beyond the trading crossroads" and "they haven't returned," rejected | E. Unauthorized consequential claim, blocked before storage |
| Stored sentence "A patrol went missing near the old milestone." | D. Authorized state change from the captain's topic |
| Stored lead "Investigate the old milestone" | D. Authorized social lead derived from that topic |
| Spoken refusal on turn 3 | Player-facing contradiction of D. The refusal itself is not a new world fact |
| "The wear" on turn 2 | Player-facing dimension label. Not stored. Not an inscription |
| Notice-board paraphrase with "edicts" and "urgent," rejected | E. Treated by validation as unauthorized (`notice_roster_history`). Not stored |
| Faction pressure and operation-complete events | D. Authorized clock |
| Contextual leads copied from emitted sentences | C. Non-authoritative contextual detail |

No invented confrontation and no persisted invented inscription appeared in this session. The known residual about examination keeping an inscription was not reproduced here. The examination turn instead discarded a paraphrase and said nothing further was reliable.
