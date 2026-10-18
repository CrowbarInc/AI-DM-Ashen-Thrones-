# PR-DS Operation Semantics

INSPECT and PERCEIVE both call `game.exploration.resolve_exploration_action`. They enter different branches of that function, and the experimental adapter accepts different results from each branch.

## PERCEIVE

The connector maps PERCEIVE to engine type `observe`, and only when the active-scene catalog kind is `perceive_target`.

The observe branch returns kind `observe`. On the courtyard lantern it returns `success: null`, an empty clue list, no skill check, no world updates, and a scene-level observation hint. It does not read `reveals_clue`, does not mark an interactable resolved, and does not advance `time_pressure`.

The adapter accepts that result only when the kind is `observe`, success is null, and no die was rolled. For `courtyard_lantern` the deterministic response is the authored visible fact: "A soot-streaked lantern burns beside the courtyard gate."

A PERCEIVE aimed at `notice_board` stays refused. That entity's catalog kind is `inspect_target` because it has `reveals_clue`. The observe path is not used to open the notice.

## INSPECT

The connector maps INSPECT to engine type `investigate`.

For an interactable with `reveals_clue`, the investigate branch can return kind `discover_clue`, the clue text, and the interactable id. The adapter accepts that result only when the clue id matches the requested target and no die was rolled. Acceptance then marks the interactable resolved. The notice board follows this path after the gate transition. Its response is "The board names the north road past the waystation." The clock does not advance.

For the courtyard lantern, the same investigate branch does something else. The lantern interactable has type `examine`, a description, and no `reveals_clue`. The DR01 sentence, "Let me get a better look at the lantern hanging beside the gate.", is classified by `classify_referenced_surface` as an authored visible feature. The visible fact is the lantern description, which is already in the scene's `visible_facts`. The resolver returns:

- kind `investigate`
- success `true`
- authority `authored_visible_feature`
- visible fact equal to the lantern description
- empty clues, no clue id, no skill check, no world updates, empty state changes

That call does not mark the lantern resolved and does not advance the clock. The session gains an empty scene-runtime shell. That shell is bookkeeping.

An utterance that names the lantern label directly, such as "I inspect the courtyard lantern.", is classified as an authored interactable. The resolver still returns kind `investigate` with the same description and no clue.

## Is inspecting the courtyard lantern a supported gameplay action?

Yes. The authoritative exploration resolver already completes an inspection of this lantern. The result discloses the authored visible fact and leaves the scene, the clock, hit points, inventory, and clue state unchanged.

## Why the live DR01 inspection was rejected

The PR-DR connector required catalog kind `inspect_target` for every INSPECT. The lantern is catalogued as `perceive_target` because it has no `reveals_clue`. `connected_action` returned `operation_incompatible_with_entity_kind` and dropped the action before the resolver ran. The gameplay adapter then recorded `no_hand_authored_action`.

The stored model output remained INSPECT on `courtyard_lantern`. The rejection was the connector's kind gate. The exploration resolver was not asked, and it already had a result for this inspection.

## What still separates the two operations

PERCEIVE remains the observe branch. INSPECT remains the investigate branch. A visible-description inspection is accepted only when the investigate result carries that already-visible description and no clue. A clue-bearing inspect still requires `discover_clue`. PERCEIVE of the notice board is still refused, so the notice text is not opened through observation.
