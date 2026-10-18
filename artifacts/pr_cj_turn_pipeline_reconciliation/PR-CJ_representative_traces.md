# PR-CJ Representative Traces

Live provider calls: 0. Providers were stubbed. Traces use the current dirty worktree.

## Trace 1 — "I investigate the desk." (cluster A)

Player input: `I investigate the desk.`

1. Routing: `construct_resolution_contract` returns `operation=ask`, `commitment=executed_now`, `resolution_subject=social`, `fast_path_abstained=false`.
2. Authoritative resolution: `select_ordinary_resolver` returns `social`. Exploration, world action, and passive wait are not permitted.
3. Selected response contract: social ask. `_INSPECT_RE` does not match `investigate`, so the terminal `OP_ASK` default applies.
4. Provider candidate: not reached for the engine clue. Chat falls through because `parse_exploration_intent` is never called, even when a test stubs it.
5. Validation / fallback: no discover-clue resolution is built.
6. Immutable sealing: not the first break.
7. Final response: chat `resolution` has no `kind`.
8. State: `discovered_clues` stays empty on the chat path.

Direct `/api/action` with an explicit investigate payload still returns `kind=discover_clue`, clue text "A map indicates patrol locations.", and searched targets `desk` and `inv-desk`.

First incorrect boundary: resolver selection, before the exploration parser.

HEAD comparison: at HEAD the clue is discovered and the failure is only `searched_targets` containing `desk` rather than `inv-desk`. The missing `kind` is new.

## Trace 2 — "I wait." (cluster A)

Player input: `I wait.`

1. Contract: `operation=ask`, `subject=social`, `resolver=social`.
2. `stage_permitted("passive_wait")` is false. The narrow passive-interruption patterns do not match a bare wait.
3. Scene-stall retry expects two provider calls. The run makes one.
4. Pressure tests do not find a concrete pressure phrase.
5. Atmosphere tests receive `No one here can answer that from what is settled here.`

First incorrect boundary: social selection. Safe nonresolution is the later replacement, and it is new relative to HEAD, where the atmosphere line was kept.

## Trace 3 — "Where is the missing patrol report?" (cluster B)

Player input: `Where is the missing patrol report?`

1. Contract: `operation=ask`, `subject=place_location`, `resolver=adjudication`, family `place_location`.
2. Provider calls: 0.
3. Final text: `No nearby that place is currently established in this scene.`
4. `resolution.kind` is `adjudication_query`.

First incorrect boundary: adjudication family selection, before narration retry. This is not the social-default path.

## Trace 4 — "Describe the gate." with validator voice (cluster C)

Player input: `Describe the gate.`

Contract probe: `ask` / `social`. The failing assertion is not the missing second call. The test reached the second provider call.

First candidate: `Based on what's established, we can determine very little here.`

Second prompt starts: `The previous attempt was rejected for: unauthorized_resolution_decision_fact.`

Expected prompt fragment: `Retry target: validator_voice.`

First incorrect boundary for the assertion: `regeneration_feedback` in `game/immutable_valid_response.py`. Social selection is true and is not what the assertion measures.

## Trace 5 — "hello there" (cluster D)

Player input: `hello there`.

Contract: `ask` / `social`. Parsers are stubbed to None. Provider is called once with the fake narration.

HTTP `resolution` is not null. Keys are metadata, prompt, and world tick events. `ordinary_contract_established` is true. `kind` is absent.

First incorrect boundary for the assertion: the chat function returns the preallocated resolution dict. Social selection is additional and does not by itself explain `resolution is None`.

## Trace 6 — parenthetical roll (cluster H)

Player input: `"Where can I find them?" (Does that require Sleight of Hand?)`

The test got past `resolution.kind == question` and past the social exchange class. `metadata.embedded_adjudication` is empty, so `category` is null.

First incorrect boundary: embedded adjudication is skipped once a resolution contract is owned. The social main lane itself held.
