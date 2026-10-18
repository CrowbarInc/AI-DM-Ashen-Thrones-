# 03 — Implemented Architecture

One module, `game/unified_semantic_planning.py`, owns the migrated family when the gate is on.

1. `deterministic_conversational_decision` asks `planning_decision` before legacy continuity.
2. A compact provider call proposes a plan. Tests can substitute `plan_proposer`.
3. `authorize_information_turn` validates the proposal and binds a host response: direct, partial, unknown, refusal, or clarification.
4. An accepted question is an `ASK` execution whose record carries the locked plan. Social resolution consumes that plan and does not call `_next_topic_to_reveal`.
5. Clarification and rejection return a sealed non-mutating decision. The locked plan is copied onto the delivered exchange through `decision.authorization`, because that path reloads the session before recording.
6. `select_host_speech` speaks the locked host line. Bounded expression may reword it. `seal_host_speech` remains the only delivery seal.
7. `continuity_directive` abstains on a migrated turn so a correction is not replayed as a request to repeat the previous line.

Combat, movement, inventory, bargaining, and unnamed small talk stay on the existing pipeline.
