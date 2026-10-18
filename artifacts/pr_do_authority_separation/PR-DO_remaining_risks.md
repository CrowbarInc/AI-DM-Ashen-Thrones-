# PR-DO Remaining Risks

- Stored PR-DN outputs cannot be split into premises, outcomes, mode, and operation class without assumptions. Faithful copies are `NOT_REPRESENTABLE` and are not submitted.
- The model chooses `operation_class`. A mechanical override mislabeled as `ATTACK` can be eligible for validation. The override sentence is not the command, and this package does not execute the attack. A later trial has to measure class accuracy before any submission is connected.
- Unmarked corrections and rules questions are not detected by the existing router. DN12 has no `OOC:` prefix. If a new-schema payload labels it `IN_WORLD_ACTION` / `ASK`, it is eligible for validation and still not executed.
- An explicit `OOC:` prefix is overridden even when the model says the turn is in-world. Other phrasings are not guessed.
- `ELIGIBLE_FOR_VALIDATION` will be unsafe if a later integrator treats it as permission to apply `player_intent.summary` or `requested_outcomes`. The only handoff this contract defines is `engine_submission`, and that object excludes model text.
- The PR-DM consumption guard still accepts the original DN05, DN07, DN08, DN09, and DN10 payloads. Those payloads are not consumed by PR-DO.
- No live model has filled this schema. Field compliance is unmeasured.
