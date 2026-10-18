# PR-CL implementation report

No product code was changed.

## Why no repair was applied

The failing boundary is the phrase list in `_assert_concrete_pressure`, not a missed clock, a skipped tick, or a dropped authorized beat.

A single tense wait:

- advances `session.clocks.time_pressure`
- evaluates `advance_world_tick`
- stores faction threshold events
- seals the hard-valid provider line
- does not call the pressure rewriter

A second passive turn:

- advances the same clock again
- evaluates the tick again
- fires scene stall because momentum is due
- emits a grounded visible fact
- stamps `passive_scene_pressure:visible_figure:streak=2`

The tests still fail because that text is not one of the deleted interruption templates.

The bounded repairs that were considered and rejected:

| Candidate | Why it was not implemented |
| --- | --- |
| Restore the pre-PR-AR interruption sentences | Those sentences invent an approach and quoted speech from a subject string. Perception grounding, the passive-pressure prompt, and the grounded-observation tests forbid that. |
| Unseal hard-valid atmosphere so pressure can rewrite turn 1 | Contradicts the PR-CK seal and the sibling tests that require the atmosphere line to survive. The current beat is a grounded fact and still would not match the phrase list. |
| Splice `event_log` text into every wait | New narration policy. Tick text is off-screen. It would change non-wait chats. It would not satisfy the phrase list. |
| Force an encounter when tension words are present | Tension is not an authority source. No probability or scheduler change is allowed. |
| Edit the two tests to drop the phrase list | The disagreement is real, but weakening the tests inside this diagnostic was not authorized. A later test-contract edit should replace the phrases with clock, tick, seal, and grounded-beat assertions. |

The misparsed lead subject `as you` on the stall sentence was observed and left alone. Fixing lead extraction is not local to projecting an authorized pressure beat, and it is not what these tests assert.

## Stop conditions that applied

Repairing the tests' demanded behavior would reintroduce invented consequential events. Specifying a new rule that every tense wait must narrate a tick event, or must interrupt, would be a design change beyond the existing owners. PR-CL stops at the contract disagreement.
