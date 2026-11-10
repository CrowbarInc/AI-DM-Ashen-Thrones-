# Retreat routing

## Original defect

With interpretation off, expression off, and physical adjudication unset, “I step back from the notice board.” was already `retreat` in `physical_adjudication._operation`. `plan_physical` returned nothing because the experiment was off. The resolution contract stored `unresolved`. Conversational orchestration did not take the sentence. `narration_skip` and `deterministic_provider_skip_line` returned nothing, so primary narration was eligible. The historical live call was one `gm.call_gpt` primary turn. This cycle reproduced that eligibility with provider calls disabled, before the edit. See `artifacts/at_opt_02/baseline_routing.json`.

## Implementation boundary

`disabled_retreat_skip` in `game/physical_adjudication.py` is the decision. It returns the existing unsupported sentence only when physical adjudication is disabled and `clear_simple_retreat` matches. The pattern requires a first-person “step back”, “back away”, or “move back from”, and it rejects questions, quotations, “and” / “then” compounds, and “step back to …”. It still requires `_operation` to return `retreat`. No new operation keyword was added.

`_chat_turn` returns `_unadjudicated_retreat_response` before interpretation and before the turn increment. `deterministic_provider_skip_line` applies the same decision at its existing fall-through, after publication, clue, observation, and travel owners. An already stamped dialogue sentence is returned by `narration_skip` before that fall-through.

The refusal reason is `unresolved_retreat_without_adjudication`, failure stage `routing`. The publication contract on the server record is `UNSUPPORTED_ACTION`. `response_class` is `operational_refusal`, so the HTTP publication event is not written and `last_publication` does not advance.

## Before and after

| | Before | After |
|---|---|---|
| Primary narration eligible | yes | no |
| `call_gpt` entries on the HTTP turn | historical live call; this cycle’s pre-edit probe did not dispatch | 0 |
| Turn counter | would increment on the narration path | unchanged |
| Position | not moved by the unresolved path | not moved |
| Completed gameplay publication | historical result was a replaced fallback | no |

## Enabled path

When the physical experiment and its controlled-world gates are on, `disabled_retreat_skip` returns nothing. Approaching the milestone and then “I step back from the milestone.” still commits position kind `back`, contract `ADJUDICATION_RESULT`, and `skip_primary_narration` false. `plan_physical` for the F3 sentence still returns operation `retreat`. `plan_physical` still returns nothing when the flag is off.

## Negative controls

“I whistle at the clouds.” stays primary-eligible and enters the patched `call_gpt`. “What can I see?” stays on the conversational answer and does not enter it. “Hello, Gate Guard.” is not a retreat; with the dialogue experiment on, host speech still publishes `FINAL_ENGINE_RESPONSE`. Third person, a hypothetical, and “thinking about stepping back” do not take the retreat refusal and do not write position kind `back`. “I step back to the tavern runner.” and “I step back from the board and look around.” stay primary-eligible.

## Safeguards

The refusal sentence does not say the player moved. The early return does not save a new position or turn. `note_completed_publication` and `record_completed_publication` do not treat the operational refusal as completed gameplay.
