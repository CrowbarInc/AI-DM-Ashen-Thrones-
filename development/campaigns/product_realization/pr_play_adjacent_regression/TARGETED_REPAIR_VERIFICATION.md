# Targeted repair verification

Provider calls disabled. OpenAI construction blocked. No new campaign opening. The seven tests in `tests/test_pr_play_post_npc_handoff.py` passed: 7 tests, 0 failures, 0 errors. Junit: `artifacts/pr_play_adjacent_regression/handoff_junit.xml`.

A separate provider-free replay printed the sentences below. It is the same gate seed and the same chat route as those tests. It is not an additional holdout.

## T04 — notice-board approach

Utterance: "I walk over to the notice board and put a hand on the frame."

Visible: "Notice board is here. Approaching or touching it is not a supported action, and you have not moved."

Scene stays `frontier_gate`. The focused test also checks that the captain sentence and the northwest clue are absent, the clue set does not gain `notice_patrol_route`, the publication pointer stays on the captain line, and the turn is not completed gameplay.

The pre-handoff package, on the same utterance after the captain line, still says the notice board is not an established destination.

T04 remains an authorized limitation. The touch is not performed.

## T05 — notice inspection

Utterance: "Read me the missing-patrol notice, not the tax lines."

Visible: "The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long."

The clue is published. The captain's sentence is not. Scene stays `frontier_gate`. The stock jab sentence is still appended. The focused test requires the clue and forbids the captain line. It does not forbid the jab.

## T06 — sleeve copy

Utterance: "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."

Visible: "That part is not supported here. It was not carried out."

The focused test checks that the character JSON is unchanged, the scene stays, the captain line is absent, and the turn is not completed gameplay.

T06 remains an authorized limitation. Nothing is written onto the sleeve.

## T09 — notice recall

Utterance: "What did that notice say about where the patrol was last seen?"

Visible: "You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know."

The focused test checks that this is not an unaddressed-ask refusal, that the captain line is absent, and that the hidden notice strings are absent.

## Negative controls

All of these passed in `tests/test_pr_play_post_npc_handoff.py`.

- Explicit repetition immediately after the captain: "Could you repeat that?", "What did the captain just say?", and "Tell me the warning again." keep the captain sentence and do not reveal the clue.
- "Ask the captain about the notice." stays at the gate and is not an unknown destination.
- "I follow the missing patrol rumor toward the northwest track." arrives at Old Milestone. The printed replay says "You arrive at Old Milestone." and the scene is `old_milestone`.
- "I step back from the notice board." stays at Old Milestone, uses the unsupported sentence, and is not completed gameplay.
- "I walk to the glass observatory." is not an established destination and adds no clue. The printed replay says "You want to reach the glass observatory, but that is not an established destination from here. You stay where you are."
- "I examine the glass observatory." does not reveal the patrol clue.
- Hidden signal and cloak-color questions do not invent the hidden strings or the colors crimson, scarlet, azure, or emerald.
- "What do the notice board and the glass dial say?" does not collapse to the notice clue or the captain line.

## Out of sequence

After the notice recall, a further "Could you repeat that?" in the printed replay did not repeat the captain. The visible sentence talks about "They" and not being here. That utterance is not the explicit-repeat control. The control repeats immediately after the captain, and that test passed. The pre-handoff package, asked to repeat after its own different T06 sentence, also fails to produce a clean repeat. This audit does not treat the out-of-sequence line as a failed T04–T09 correction.

## Remaining gameplay limitations

- T05 still publishes the stock jab after the authorized clue.
- T04 and T06 decline. They do not complete the touch or the copy.
- The twelve adjacent HTTP failures remain, and they are preexisting.
- This rerun did not replay T01, T07, or T08. The previous cycle's finding that those turns are non-play sentences is unchanged and was not retested here.
- No Ashen Thrones Gameplay Benchmark was run. The seven tests were written with the repair. They are not an independent holdout.
