# PR-CL test expectation audit

The two tests demand a player-facing interruption lexicon. They do not demand a clock change, a tick event, or a durable state transition.

| Requirement | Test 1 | Test 2 | Authorized by the current contract? |
| --- | --- | --- | --- |
| A. A specific phrase from the interruption list | Yes. This is the failing assertion. | Yes. This is the failing assertion. | No. Those phrases are the deleted pre-PR-AR templates. |
| B. A specific type of interruption | Yes. Quotes, an approach, a shoulder stop, or someone breaking silence. | Same list. | No. Tension and a visible-fact sentence do not authorize an approach or quoted speech. |
| C. A specific NPC action | The list includes runner, notice, and east-road wording. The fixture's runner sentence is prose. The world NPC is at another scene and has no move agenda. | The list is the same. The emitted line already names the guard in the visible fact, and that is still not enough. | No specific NPC action is scheduled. |
| D. Any authorized world development | No. Faction events already occur and would still fail the phrase list. | No. The grounded guard sentence and the `passive_scene_pressure` tag would still fail the phrase list. | The engine already produces authorized developments the tests do not accept. |
| E. A durable state transition | Not asserted. | Not asserted. Streak and faction rows already change. | Not what the tests measure. |
| F. Merely non-repetitive narration | No. Test 2's second line is already different from the atmosphere stub, and it still fails. | No. | Scene stall already replaces the repeated atmosphere. |

## Why this is expectation drift, not a missing beat

The phrase list matches `_render_passive_pressure_beat` as it existed in `dcbcefe`, before the PR-AR checkpoint removed it:

- lead figure: "cuts through the crowd and stops at your shoulder" and "Ask me now"
- pending lead: "If you're moving on this, move now"
- visible guard: "Take the east-road report"

Those sentences were assembled from a subject string. They were not loaded from an NPC agenda, a due event, or authored dialogue.

Current authorities reject that output:

- `render_grounded_perception_line` is the pressure beat.
- The model instruction forbids inventing a person or confrontation.
- Grounded-observation tests reject "stops at your shoulder".
- PR-CK seals a hard-valid unresolved line before pressure rewrite, and the sibling atmosphere tests were updated to expect that seal. These two tests were left on the old phrase list.

The second test's metadata assertions (`passive_scene_pressure:` and `streak=2`) already match the engine on the repeated-wait path. They are not the failure.

## What was not done

The tests were not edited. A phrase-list relaxation would hide the disagreement without a replacement assertion for clock, tick, and grounded narration. That edit is a test-contract change, and this cycle stops at documenting it.

Restoring the old templates would make the tests pass by inventing speech. That is the behavior the later contract removed.
