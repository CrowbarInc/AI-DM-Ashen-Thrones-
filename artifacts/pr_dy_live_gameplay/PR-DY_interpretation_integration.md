# PR-DY interpretation integration

The production connector uses the existing contract. It does not add a phrase table and it does not add another interpreter.

## Call

`interpret_production_turn` sends one structured completion:

- model pin `gpt-4.1-mini` (returned snapshot `gpt-4.1-mini-2025-04-14`)
- schema name `pr_dr_interpretation`
- temperature 0
- max output tokens 320
- no retry

The prompt is `build_messages_for_catalog`. Recent visible player turns are included so a follow-up can refer to something already said. `build_messages` still calls that helper with no recent turns, so older prompt snapshots stay the same.

Importing the experiment packages sets `ASHEN_DISABLE_LIVE_INTERPRETATION=1`. The connector saves and restores that variable around the import. Without that restore, the first production import would disable the feature it just enabled.

## Decisions

| Disposition | Production result |
| --- | --- |
| ELIGIBLE_FOR_VALIDATION, one connected component, bridge accepts | Locked gameplay action |
| OUT_OF_CHARACTER on AUTO | Non-mutating acknowledgement |
| NEEDS_CLARIFICATION or SAFE_ABSTENTION | Clarification text, no mutation |
| UNSUPPORTED_OPERATION or any other non-eligible disposition | Blocked, no mutation |
| More than one component | Asks which single action, no mutation |
| Malformed JSON or provider/budget failure | Blocked, no mutation |
| Bridge rejects the target or operation | Blocked, no fall-through |

Explicit IC overwrites the model's communication mode to `IN_WORLD_ACTION` before adaptation. It does not skip eligibility or the bridge. Explicit OOC never reaches this function.

Rejected and blocked results return before the turn counter increments. They do not continue into the phrase parser.

## Catalog

Rows come from the existing visible catalog: interactables, exits that have ids, and world NPCs in the current scene. On the disposable frontier gate that catalog contained `notice_board`, `guard_captain`, and `tavern_runner`. Frontier-gate exits have no ids, so MOVE cannot bind there. That is existing scene data, not a new movement system.

## Double interpretation

After an accepted or blocked production call, `live_chat_interpretation_consumed` is set. `interpret_for_contract` and `establish_ordinary_gameplay_contract` then skip the older semantic interpreter for that turn.

## What was not built

No new operation classes, no combat, no world simulation, no parallel chat pipeline, and no special-case sentence list as the AUTO classifier.
