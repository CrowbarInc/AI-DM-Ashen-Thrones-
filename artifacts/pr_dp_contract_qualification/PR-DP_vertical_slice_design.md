# PR-DP Vertical Slice Design

Design only. This sequence was not implemented and was not executed.

The world is disposable. It is not `data/world.json`, `data/session.json`, or `data/combat.json`.

## Disposable world

- Scene `waystation_courtyard`: Sergeant Mara is an addressable NPC. A lit lantern is an interactable. The courtyard gate is an exit to `waystation_street`.
- Scene `waystation_street`: a notice board interactable that does not exist in the courtyard.
- Session and world are in-memory copies. Saves, if a later implementation writes them, go to a temporary directory.

One operation is submitted per turn. `compound_transaction` stays false. Model sentences stay out of `engine_submission`.

## Turn 1 — ordinary action

1. Player input: `I look at the lantern by the gate.`
2. Interpretation route: PR-DO adapter. Expected class `PERCEIVE` or `INSPECT`, target `courtyard_lantern`, disposition `ELIGIBLE_FOR_VALIDATION`, `execution_authorized` false.
3. Validated action: `{type: "observe", target id: courtyard_lantern}` after the engine confirms the id is a visible interactable. The player utterance is passed as raw text. `player_intent.summary` is not passed.
4. Resolver: `game.exploration.resolve_exploration_action`.
5. Expected state transition: no scene change and no HP change. If the lantern has no skill check, `success` stays unset.
6. Persistence checkpoint: disposable session turn counter may increment. World facts do not change.
7. Narration handoff: the resolver result kind and visible lantern text. No narration model is called by this design.
8. Player-visible result: a description of the lantern that is already in the scene.
9. Failure and recovery: unknown target yields a blocked exploration result and no save of new facts. The next player input can name the lantern again.

## Turn 2 — social interaction

1. Player input: `I ask Sergeant Mara whether the street is beyond the gate.`
2. Interpretation route: PR-DO adapter. Expected class `ASK`, target `sergeant_mara`.
3. Validated action: `{type: "question", target_id: "sergeant_mara"}` after `resolve_authoritative_social_target` binds that NPC. The question text is the player utterance.
4. Resolver: `game.social.resolve_social_action`.
5. Expected state transition: `session.npc_runtime` may record the exchange. Mara does not gain a new obligation from the player's sentence.
6. Persistence checkpoint: disposable session, including `npc_runtime`.
7. Narration handoff: the social result hint. Requested outcomes remain `UNADJUDICATED` and are absent from `engine_submission`.
8. Player-visible result: Mara answers from authored knowledge, or the existing uncertainty path says she does not know.
9. Failure and recovery: if Mara is not addressable, the social resolver does not select a fallback speaker. No `npc_runtime` disclosure is written. The turn ends in clarification.

## Turn 3 — state-changing action

1. Player input: `I go through the courtyard gate.`
2. Interpretation route: PR-DO adapter. Expected class `MOVE`, target `courtyard_gate`.
3. Validated action: `{type: "scene_transition", targetSceneId: "waystation_street"}` only after the scene graph says the gate exits to that scene. A MOVE toward the well does not take this branch.
4. Resolver: `game.exploration.resolve_exploration_action`, then the existing `activate_scene` on the disposable session.
5. Expected state transition: active scene becomes `waystation_street`.
6. Persistence checkpoint: disposable session scene pointer and world scene id. This is the checkpoint turn 4 reads.
7. Narration handoff: transition result with destination id. Clock advancement is not inside the resolver. A later harness may call the existing `advance_clock(session, "time_pressure", 1)` once on the disposable session, matching the chat path's separate clock step.
8. Player-visible result: the player is in the street scene.
9. Failure and recovery: if the gate is not an exit, the transition is blocked, the scene id stays `waystation_courtyard`, and the checkpoint is not updated.

## Turn 4 — action that depends on the changed state

1. Player input: `I read the notice board.`
2. Interpretation route: PR-DO adapter. Expected class `INSPECT`, target `notice_board`.
3. Validated action: `{type: "investigate", interactable id: notice_board}` only when the active scene is `waystation_street` and that interactable is authored there.
4. Resolver: `game.exploration.resolve_exploration_action`.
5. Expected state transition: the board can be marked resolved on the disposable session when it exposes a one-time clue. If the active scene were still the courtyard, validation fails and nothing is marked.
6. Persistence checkpoint: disposable session discovered-interactable set, written only after validation succeeds.
7. Narration handoff: the investigate result and the board's visible text.
8. Player-visible result: the board's authored text, available because turn 3 changed the scene.
9. Failure and recovery: a courtyard active scene returns blocked, does not invent a board, and leaves the turn-3 checkpoint unchanged. The player can still take the gate on a later turn.

## What this slice does not do

- It does not call production `game.api` chat.
- It does not connect `engine_submission` until a later implementation adds the entity-kind adapter.
- It does not roll dice unless an authored skill check on the lantern or board already requires the existing exploration check.
- It does not implement compound transactions, new mechanics, or a planner.
