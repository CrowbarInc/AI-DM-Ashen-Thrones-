# Twelve-turn original HTTP comparison

All original requests/seed retained; provider requests and live calls zero, all twelve HTTP 200.

| Turn | Before | After |
|---|---|---|
| T01 | Provider calls are disabled for this run, so no live narration was generated. | Provider calls are disabled for this run, so no live narration was generated. |
| T02 | Guard Captain says, "I couldn't tell you." | Guard Captain says, "I couldn't tell you." |
| T03 | Guard Captain mutters, "Word is, a patrol went missing near the old milestone." | Guard Captain mutters, "Word is, a patrol went missing near the old milestone." |
| T04 | Notice board is here. Approaching or touching it is not a supported action, and you have not moved. | Notice board is here. Approaching or touching it is not a supported action, and you have not moved. |
| T05 | The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. |
| T06 | That part is not supported here. It was not carried out. | That part is not supported here. It was not carried out. |
| T07 | Provider calls are disabled for this run, so no live narration was generated. | Provider calls are disabled for this run, so no live narration was generated. |
| T08 | The action stands, and no further narration request was sent. | The action stands, and no further narration request was sent. |
| T09 | You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know. | You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know. |
| T10 | No nearby tavern is currently established in this scene. | No nearby tavern is currently established in this scene. |
| T11 | You arrive at Old Milestone. | You arrive at Old Milestone. |
| T12 | That part is not supported here. It was not carried out. | That part is not supported here. It was not carried out. |

Only T05 text changes. All turn intent kinds, routing fields, authorized discoveries, resolver state changes, scene results and refusal categories match. T04 stays local without completing touch; T06 refuses copying; T09 recalls the same clue; T11 genuinely travels. T06 retains the preceding successful publication, so its pointer inherits T05's corrected text; it still does not publish the refused action. No publication mismatch. Full conversation histories naturally contain the corrected T05 and momentum bookkeeping records the selected new information beat. Separate unchanged controls preserve explicit NPC repetition, genuine follow-up and hidden-information protection.

T01/T07 disabled narration; T02 unhelpful NPC answer; T04/T06 incomplete physical actions; T08 generic acknowledgment; T10 improvised trading; T12 operational refusal. Twenty baseline failures remain: twelve obsolete public-resolution assertions, one stew mismatch, four authority/refusal/publication failures including the portal exception, and three unrelated KeyErrors. No full suite, independent held-out generalization, live-provider or Gameplay Benchmark claim.

Machine comparison: twelve_turn_comparison.json. Full requests, state/log snapshots and publication traces: traced_before/twelve_turn and after_final/twelve_turn. No scenario edit manufactured the result.
