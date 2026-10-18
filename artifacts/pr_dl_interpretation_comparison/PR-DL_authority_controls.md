# PR-DL Authority Controls

Preparation and both live stages ran inside `ProductionSaveGuard`. The guard probe intercepted session, world, and log writes, then asserted the watched save fingerprint was unchanged. Stage checkpoint `save_guard_verified` is True. Provider tripwire hits during the live stage: [].

`ASHEN_DISABLE_LIVE_INTERPRETATION=1` was set before contract construction. `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` were patched to raise. The only provider path was the experiment client's `responses.create` call. Preparation recorded `live_provider_calls` 0. Recomputed contract traces showed no interpretation API calls.

Prompts contained player input, a short visible scene context, permitted entity ids and labels, the interpretation schema, clarification rules, and authority restrictions. Hidden-fact scan of prompts and stored outputs: none.

The experiment did not call resolvers, roll dice, or execute plans. Every adapter result records `executed=false` and `mutated_state=false`.

Model outputs that crossed authority bounds were retained and rejected for consumption:

- `declared_canon` is schema-valid and proposes updating world facts, including the tunnel being open. Authority score FAIL. It was not applied.
- `mechanical_dump` proposes setting the goblin's hit points to zero. The adapter rejected the payload (`ambiguous_referent`). Authority score FAIL. It was not applied.
- `control_combat` invents `quarterstaff`. The adapter rejected the unknown id. Authority score FAIL. It was not applied.

No output was repaired or retried. The experiment path has no authoritative state mutation.
