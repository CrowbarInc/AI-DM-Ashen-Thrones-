# PR-DF Shared Authority Contract

A, B, and C use one world. The experiment harness holds a copy. The copy is loaded from the same constructors the PR-DE fixtures use. Production `data/*.json` is not the copy.

## Requirements and where the engine already meets them

| Requirement | Current satisfaction | Gap the experiment must not paper over |
|---|---|---|
| One authoritative world | Session, world, scene, and combat documents. `state_authority` domains. Mutation owner checks. | Post-narration gateway is observe-only and can still adopt shape-valid model updates. Harness omits that seam. |
| Deterministic mechanics where defined | Combat rolls, skill checks, noncombat classification, contract selector. | Dice are random unless the harness injects `roll_die`, as PR-DE does for B1 (`return_value=10`). All candidates share one injected stream. |
| Resource accounting | Attack writes enemy HP. Conditions modify attack and damage. `time_pressure` is an int clock. | No general inventory spend API was found. Item-spend requests are unsupported for every candidate. |
| Persistent consequences | Scene transition, clue knowledge, leads, world flags, NPC location on tick, improvisation ledger. | Consequences stick only after the mutator runs. Narration text is not itself a consequence. |
| NPC identity and continuity | Directed social entry, discourse focus, speaker contract, interaction context after the action. | Continuity can break on scene change. That rule is shared. A planner must not keep an off-scene NPC in the conversation by writing prose. |
| World clock and scheduled events | `advance_world_tick` plus `advance_clock` at the start of `chat`. Tick covers projects, faction pressure, and mobile NPC moves. | Tick is once per chat turn today, including turns that are only talk. The harness preserves that single call. Downtime is not a second scheduler. |
| Hidden-information restrictions | `narration_visibility`, hidden-fact prompt lines, improvisation reject codes, H1 kept off the reduced projector. | The restriction on A is partly instructional. B and C must enforce it in the tool and query results, not only in the prompt. |
| Validation before finalization | Policy enforcement, emission gate, monotonic contract check, then player-facing text. | Validators see model text. They do not roll back a mutation that already happened. The harness snapshot is the only undo, and it undoes by discarding the copy. |

## Single writer rule

Writers allowed on the harness copy:

- Existing resolvers and `_apply_authoritative_resolution_state_mutation`
- `advance_world_tick` and `advance_clock`, once
- Existing clue, lead, discourse, and bounded-improvisation functions when a resolver or the current narration finalizer already calls them
- The improvisation validator, which may append an accepted low-consequence ledger entry and must refuse consequential kinds

Writers forbidden:

- Planner JSON
- Tool-call arguments
- Narration prose
- A new "agent world" object
- Direct assignment to `data/session.json` or `data/world.json`

`state_authority._NON_AUTHORITATIVE_MUTATION_OWNERS` already lists `gpt`, `llm`, `model`, and `openai`. The harness passes `owner_module` as the engine module name, which is what the registry asks for.

## Commit boundary

One successful resolver invocation is a commit on the harness copy. The next step sees that copy. A failed invocation restores the copy to the snapshot taken immediately before that invocation.

This is weaker than a database transaction around a whole plan. It is the strongest boundary the current functions support without a new undo log. The experiment scores it as specified behavior, not as a hidden advantage for A.

## Shared outcome fields

Every scenario records the same tuple for A, B, and C:

- `scene_id` before and after
- known clue ids and player-visible clue texts
- combat public summary (in combat, target hp) when combat exists
- `time_pressure` and tick event types
- interlocutor id
- improvisation ledger ids and kinds
- whether a provider narration was requested
- prohibited-outcome flags from the scenario sheet

Narrative sentences are stored for the optional live arm. They are not world state.

## Unresolved authority gaps (shared, so they do not pick a winner)

1. Observe-only post-GM adoption on the production `chat` path.
2. Downtime recognized and unwired.
3. No inventory ledger.
4. No engine-level undo.
5. Visibility enforcement on Candidate A depends on validators after generation. A leak that validators miss is a residual risk for A. B and C can still leak in the narration call, because that call is shared. They should not leak in query results.
6. `chat` ticks before it knows whether the utterance was legal. The shared harness copies that order so A is not given a quieter clock than B or C.
