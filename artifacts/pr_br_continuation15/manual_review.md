# Continuation 15 manual review

Session `20261001T094739Z`. Manual transcript and candidate-history review. Telemetry is compared after the fact and is not treated as the verdict.

## Turn 1 — ordinary control

Player: "I stop at the gate and read the notice board from top to bottom."

Contract: inspect, target Notice board, dimension none. Correct.

Generated and final are the same line. It reads the board: new taxes, curfew rules, and a warning that the missing patrol was last seen on the northwest mud track past the crates.

Initial manual PASS. Final manual PASS. Requested-dimension coverage is not applicable. Clarification not applicable. No degradation. Best candidate emitted. Evaluator PASS.

## Turn 2 — ambiguous follow-up

Player: "When did that happen?"

Contract: ask, dimension time, target Notice board. Fast path abstained for insufficient discourse context. The interpreter set time and bound the notice board. Ambiguous is false. Correct for the discourse that existed: one inspected object, and the previous narration had already singled out the patrol warning as the thing that catches the eye.

Generated and final are the same line. The board does not specify when the patrol went missing. The last known sighting is the northwest mud track. That is a time-specific inability about a clear salient event, plus the sighting the board does give. It is not a generic "I cannot say how recently that was" replacing a clarification. No clarification was generated, and none was required.

Initial manual PASS. Final manual PASS. Time coverage yes. Clarification necessary: NO. No degradation. Best candidate emitted. Evaluator PASS.

## Turn 3 — content inquiry

Player: "I ask the gate guard what the travelers have been telling people as they arrive."

Contract: ask, dimension content, interlocutor gate guard. Target label remained Notice board by discourse inheritance. Dimension and interlocutor are correct.

Generated and final are the same line. The guard says he has not heard what the travelers have been saying, and that most of what comes through is chatter he cannot vouch for. That is a content-specific inability. It does not substitute Captain Thoran or another related fact.

Initial manual PASS. Final manual PASS. Content coverage yes. No degradation. Best candidate emitted. Evaluator PASS.

## Turn 4 — additive dimension

Player: "What do people come to that board for?"

Contract: ask, dimension use, target Notice board, interlocutor gate guard. Correct.

Generated and final are the same line. The guard says most folks come to catch up on the latest rules and warnings, and that the board lists taxes, curfews, and the missing patrol. That answers use and adds the posted content. Manual requested-dimension coverage: YES. The scorer did not recognize "folks come … to catch up on the latest rules" as use and marked `generic_scene_replaced_dimension`. No best candidate was stored because of that score. The emitted line is still the generated line.

Initial manual PASS. Final manual PASS. No manual degradation. Telemetry degradation no. Evaluator FAIL. This is a false FAIL. It was not repaired after the run.

## Totals

- Correct contracts: 4/4
- Initial manual PASS: 4/4
- Final manual PASS: 4/4
- Manual semantic degradations: 0
- Telemetry semantic degradations: 0
- Disagreements: 0
- best_safe emission mismatches: 0
- Content correct/applicable: 1/1
- Clarification preserved/applicable: 0/0
- Additive correct/applicable: 1/1 on the player-visible answer
- Evaluator PASS: 3/4
- Evaluator false PASS: 0
- Evaluator false FAIL: 1
