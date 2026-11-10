# Twelve-turn comparison

The provider-free scenario and scene seed are unchanged. Before-text is the T05 cycle’s published after-text. After-text is this cycle’s replay. Only T04’s published text, kind, and publication pointer change.

| Turn | Before | After |
|---|---|---|
| T01 | Provider calls are disabled for this run, so no live narration was generated. | Same |
| T02 | Guard Captain says, "I couldn't tell you." | Same |
| T03 | Guard Captain mutters, "Word is, a patrol went missing near the old milestone." | Same |
| T04 | Notice board is here. Approaching or touching it is not a supported action, and you have not moved. | You walk over to the notice board and rest a hand on its frame. You remain in Cinderwatch Gate District. |
| T05 | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. | Same |
| T06 | That part is not supported here. It was not carried out. | Same |
| T07 | Provider calls are disabled for this run, so no live narration was generated. | Same |
| T08 | The action stands, and no further narration request was sent. | Same |
| T09 | You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know. | Same |
| T10 | No nearby tavern is currently established in this scene. | Same |
| T11 | You arrive at Old Milestone. | Same |
| T12 | That part is not supported here. It was not carried out. | Same |

T04’s kind changes from `conversational_decline` to `conversational_answer`, owner `local_interaction`, success true, scene still `frontier_gate`. Its pointer becomes the new narration. T05 then publishes the clue and replaces the pointer. T06 keeps T05’s clue pointer and does not publish the refused copy. T09 recalls the same clue. T11 still travels. T12 still refuses the step-back.

Elapsed for the twelve turns: 2616.811 ms. Network blocks: none. Provider calls: 0.

## Still unresolved

T01 and T07 missing narration. T02 unhelpful NPC reply. T06 persistent copying. T08 generic acknowledgment. T10 improvised trade. T12 operational refusal. Seventeen baseline failures remain. No full-suite, held-out, live-provider, or Gameplay Benchmark claim.
