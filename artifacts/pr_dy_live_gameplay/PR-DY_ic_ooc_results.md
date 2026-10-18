# PR-DY IC/OOC results

## Explicit IC

Disabled-provider preflight, recorded in `preflight_http.json` before the disposable runtime was replaced for the live server:

- Text: "IC: I examine the notice board."
- Mode: IC
- Kind: `discover_clue`, action `notice_board`
- Turn 1 to 2, time_pressure 1 to 2
- Providers disabled, so this used the existing parser path rather than a live interpretation call

With live interpretation enabled, the unit test `test_pr_dy_explicit_ic_uses_validated_interpretation` forces the model payload to an OOC mode while still supplying an ASK component. Explicit IC rewrites the mode to `IN_WORLD_ACTION` and the validated ask still runs. A rejected component would still block.

## Automatic OOC

Browser text: "How does searching work at the table? I'm not doing anything in the scene."

- Mode: AUTO
- Model communication mode: `RULES_QUESTION`
- Disposition: `OUT_OF_CHARACTER`
- Status: blocked, reason `automatic_ooc`
- Player-visible text: "Understood. I'll treat that as out of character. No gameplay action is executed, no game time advances, and committed state is unchanged."
- `authoritative_mutation`: false
- Interpretation was sent (749 / 198 / 947). No narration request followed.
- Session turn stayed 3. time_pressure stayed 3.

The model did emit an ASK component with a null target. That component was not executed. The OOC disposition stopped the turn.

## Explicit OOC

Browser text: "OOC: please leave the scene exactly as it is."

- Mode: OOC
- Kind: `ooc_message`
- Player-visible text: "Understood. I will treat that as out-of-character. No gameplay action is executed, no game time advances, and committed state is unchanged."
- `authoritative_mutation`: false
- No new provider ledger row. Sent interpretations remained 3.
- Turn stayed 3. time_pressure stayed 3. Scene stayed `frontier_gate`. The discovered clue remained.

The same non-mutating explicit OOC result was already shown in the disabled-provider preflight (turn stayed 1). Explicit OOC does not depend on a live model call.

## Unresolved mode

A caller override that conflicts with a textual declaration remains the existing non-mutating conflict response. Ambiguous consequential AUTO results that come back as clarification do not execute; that path is covered by `test_pr_dy_clarification_does_not_mutate`. When interpretation is disabled, unmarked text still uses the pre-existing parser. That is the provider-off behavior, not a live classification.
