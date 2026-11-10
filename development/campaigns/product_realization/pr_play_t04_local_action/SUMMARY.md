# PR-PLAY T04 Local Physical-Action Completion

**Cycle verdict: A/PASS.** Milestone `pr_play_t04_local_action`. Branch `feature/product-realization`; HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Dirty work preserved. No commits or pushes. Live provider calls: **0**.

## Root cause

The original request, “I walk over to the notice board and put a hand on the frame,” already resolved the notice board as the unique current-scene object. `_local_presence_decision` then declined it as `local_object_not_a_destination` / `decline_unadjudicated_contact` before any physical outcome existed. The HTTP path published that decline and did not move the character.

## Implementation

The existing local-interaction owner now authorizes a narrow transient outcome for one approach, one simple contact, or that bounded pair, when the target is uniquely in the visible catalog and `classify_referenced_surface` reports an authored interactable with existence, visibility, and inspectability. The outcome records no scene transition and no persistent mutation. The existing conversational seal publishes it only when the sealed text still equals that authorized narration.

Production files: `game/local_interaction.py`, `game/conversational_orchestration.py`, `game/api.py`.

## T04 outcome

Published text is now: “You walk over to the notice board and rest a hand on its frame. You remain in Cinderwatch Gate District.”

Owner `local_interaction`. Target `notice_board`. Both local movement and physical contact are completed. Scene stays `frontier_gate`. Accepted text is immutable and hard-valid. The publication pointer matches that narration. No inventory or world mutation, and the patrol-route clue is not disclosed by the touch.

## Regression

Predecessor combined selection on this same pre-edit tree: **393 passed / 20 failed** of 413. This cycle’s selection adds 12 local-action tests and records **408 passed / 17 failed** of 425. The 17 failures are a subset of the prior 20. No new failure identity, collection error, or skip. Three greeting/refusal tests that previously failed were not reproduced under a clean temporary directory; the local-action resolver does not match their phrase, and this cycle does not claim to have repaired operational-refusal classification.

Twelve-turn published text changes only at T04. T05’s clue stays clean. T06, T09, travel, and the other published turns stay as they were.

## Remaining limitations

T01 and T07 still have no live narration. T02’s NPC answer stays unhelpful. T06 copying onto clothing stays unsupported. T08 stays a generic acknowledgment. T10 trading stays unestablished. T12’s step-back stays an operational refusal. The seventeen remaining baseline failures stay unresolved. This is not a physics engine, not persistent gesture tracking, and not broad playability acceptance.
