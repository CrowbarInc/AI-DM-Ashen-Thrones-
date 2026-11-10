# Twelve-turn comparison

The established provider-free run_sequence.py harness was copied with only cycle output redirection; all twelve utterances and initialization remain unchanged. Both runs completed HTTP 200 for all turns with no errors and zero provider requests. All twelve publication strings and scene outcomes match exactly. This preserves the existing experience; it does not make that experience playable.

| Turn | After publication | Before/after |
|---|---|---|
| T01 | Provider calls are disabled for this run, so no live narration was generated. | Identical |
| T02 | Guard Captain says, "I couldn't tell you." | Identical |
| T03 | Guard Captain mutters, "Word is, a patrol went missing near the old milestone." | Identical |
| T04 | Notice board is here. Approaching or touching it is not a supported action, and you have not moved. | Identical |
| T05 | The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. | Identical |
| T06 | That part is not supported here. It was not carried out. | Identical |
| T07 | Provider calls are disabled for this run, so no live narration was generated. | Identical |
| T08 | The action stands, and no further narration request was sent. | Identical |
| T09 | You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know. | Identical |
| T10 | No nearby tavern is currently established in this scene. | Identical |
| T11 | You arrive at Old Milestone. | Identical |
| T12 | That part is not supported here. It was not carried out. | Identical |

T04 remains local without movement, clue disclosure or actual touching completion. T05 still publishes the authorized northwest patrol clue and the unrelated stock jab. T06 declines unsupported copying, with inventory unchanged. T09 recalls previously disclosed clue content without an NPC addressee. T11 travels to Old Milestone; T12 remains an operational refusal. Seven separate unchanged HTTP controls preserve genuine repetition/follow-up, unknown destination and hidden protection.

T01/T07 disabled narration, T08 generic action wording, T02's unhelpful answer, trading and physical completion remain deficient. No broad NPC/world improvisation was added. Evidence: before/twelve_turn and after/twelve_turn, plus twelve_turn_comparison.json under artifacts/pr_play_preseal_authority/.
