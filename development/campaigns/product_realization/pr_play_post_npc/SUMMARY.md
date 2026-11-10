# PR-PLAY post-NPC conversational handoff

**Verdict: A/PASS for the targeted orchestration repair.** The game is not playable. PR-PLAY-80 was not opened. Milestone identifier: `pr_play_post_npc`. Live provider calls: 0.

## Original defect

After the Guard Captain answered, the next player utterance stayed inside that conversation.

- T04 treated the visible notice board as an unestablished travel destination.
- T05 and T06 replayed the captain's sentence.
- T09 asked the previous NPC and then refused the turn as an unaddressed provider target.

## Root cause

The four failures are not one predicate. They share a short-circuit that runs before the current utterance's owner.

- T04: movement resolution ignored a catalog hit that already identified the notice board as a current-scene inspect target, then refused it as an unknown destination.
- T05 and T06: keyword overlap with the last NPC sentence selected `repeat_delivered_statement` before inspection or physical action.
- T09: a deictic question was forced onto the previous speaker, and the addressee bridge then refused an unaddressed ask.

## Changes

Current intent and target now win when they name an established scene object or an unbound physical attempt.

- A unique current-scene catalog hit on a movement destination declines as local contact. It does not travel, reveal the clue, or move the scene.
- Overlap replay abstains when the utterance is not a question or names a scene object. Explicit repeat requests still replay, including a GM-owned delivered row when the player names the speaker.
- A past-tense question about what an established object said becomes an inspect of that object.
- An unbound physical attempt with adjudication off declines with the existing unsupported sentence and does not change inventory.

## Twelve-turn replay

Same utterances, same seed, provider calls disabled. T04 is local contact. T05 publishes the patrol-route clue. T06 declines the sleeve copy. T09 recalls the already disclosed clue. T11 still arrives at Old Milestone. T12 is still the unsupported retreat. T01, T07, and T08 still publish non-play sentences. T05 also appends the existing stock line about someone jabbing at the board.

## Remaining limitations

- T04 and T06 are authorized limitations, not completed physical actions.
- T05's clue is followed by an invented-sounding stock sentence.
- T01, T07, and T08 are still not meaningful play. T07 changed from a mashed incidental to the disabled-narration sentence.
- Twelve adjacent HTTP assertions failed. A pre-edit rerun was not obtained, because checking out HEAD of the orchestration file removed `authored_travel_admission` and broke collection. Those failures are not claimed as new identities and are not claimed as baseline.

## Recommended next step

Repair the stock diegetic sentence that is appended after an authorized clue publication. Do not start that repair from this handoff. Do not open PR-PLAY-80. Do not start AT-OPT-07. Do not launch live play from this result.
