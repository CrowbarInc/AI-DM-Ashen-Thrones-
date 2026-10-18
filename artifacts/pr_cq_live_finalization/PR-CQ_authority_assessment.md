# PR-CQ Authority Assessment

Decision input for the negative-authority audit. Final player text is not treated as sufficient by itself.

## Proposed unsupported facts

Turn 1's single candidate proposed a preference, a duty remark, a figurative line about the eastern gate, a soaked cloak, and a glance at the muddy crowd. Validation accepted it with no violation codes. The preference speech and the gaze were stored as `bounded_incidental` entries, not as world truth. No new visible fact, hidden fact, NPC, item, or clue was written.

Turn 2 attempt 1 proposed, and validation rejected:

- an assignment / order ("tasked with scouting")
- the old trading crossroads as the patrol's route
- "They simply didn't return"
- "no sign of them, no messages"
- a sodden hood and hardened eyes as part of the same rejected sentence

Those strings remain under `narration_temporal_provenance.rejected_consequential`. They are not clue text.

Turn 2 attempt 2 proposed, and validation rejected:

- a looser milestone paraphrase ("There's talk of a patrol missing near the old milestone")
- "I don't know the details myself"
- runner whispers picking up the warning

The notice-board warning and the tavern runner's rumor-shouting are authored visible facts. The attempt bundled them with ignorance and with a paraphrase the audit still marked `patrol_route_or_geography`. The bundle was discarded.

The discoverable scene line that already mentions "the old trading crossroads" is in `game.defaults.default_scene("frontier_gate")`. The probe did not promote it into visible facts or into the spoken answer.

## Authorized facts preserved

The player-facing patrol answer contains the authored proposition: a patrol went missing near the old milestone.

Clue knowledge `social_frontier_gate_guard_captain_patrol` is `discovered` / `explicit` with text "A patrol went missing near the old milestone."

`revealed_topics` for `guard_captain` is `["patrol"]` after turn 2 and was empty after turn 1.

## Unauthorized state mutation

Severe-mutation check: none. Production `data/` mtimes did not change.

Scene id stayed `frontier_gate`. Hidden facts and visible facts were unchanged. NPC topic strings were unchanged. Character sheet was unchanged (Galinor, HP 8/8, spellbook only).

Ordinary clock ticks did occur: each faction pressure and agenda progress increased by 1 on each turn (House Verevin and Ash Cowl pressure 2→4, Ordo Pyric 1→3, agenda 0→2). That is the existing passive clock, not a fact invented by the rejected drafts.

Trust on the captain moved from 0 to 1 when the patrol topic was revealed. The topic text itself was not rewritten.

A contextual-lead splitter stored the projected sentence with `position` equal to `near the old milestone."`, including the closing quote. The clue text and the spoken fact stay the authored sentence. The split is lead metadata, not a new place.

## Final narration versus authoritative state

Turn 1: no topic was revealed, and the spoken line is a preference, not a patrol fact.

Turn 2: the resolver marked the patrol topic revealed before narration, the clue store holds that sentence, and the spoken line is that sentence inside the social template. The player was not told that the captain cannot answer.

Provenance on the sealed turn 2 record is the label `safe_nonresolution`. The acceptance reason is `authored_answer_projection`, and the sealed text is the authored line. The label does not describe an ignorance fallback.

## Integrity judgment

No unauthorized consequential claim survived into the player-facing answer or into discovered clue text. The crossroads, the non-return, the negative evidence, and the ignorance denial were rejected.

The remaining authority-shaped gap is classification, not leakage: attempt 2's milestone paraphrase was still an unauthorized geography hit, so the authorized proposition reached the player only through projection.
