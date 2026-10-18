"""Existing resolver inventory for PR-DO operation classes.

Classifications were taken from the current engine modules. No resolver was added.
"""

from __future__ import annotations

# The four-turn slice uses observe/investigate, question, and scene_transition.
# Each of those functions already exists. The mapping is safe only when an
# adapter checks entity kind before the call and never copies model sentences
# into the resolver. Naive use of combat.ensure_target is not part of the slice.
SLICE_MAPPING_SAFE = True
SLICE_UNSUPPORTED = False


INVENTORY = (
    {
        "operation_class": "MOVE",
        "classification": "PARTIALLY SUPPORTED",
        "resolver": "game.exploration.resolve_exploration_action",
        "existing_types": "scene_transition, travel",
        "input": "normalized_action.type plus targetSceneId, a scene graph, list_scene_ids, and load_scene_fn",
        "world_fields": "scene.exits, scene.id, session active scene",
        "target_validation": "The target must already be an authored exit. Intra-scene walking has no position field.",
        "dependencies": "Caller performs activate_scene after a resolved transition. The resolver itself has no side effects.",
        "output": "kind, resolved_transition, optional skill_check",
        "persistence": "Caller saves the disposable session after activate_scene. Production saves are not in this path.",
        "time": "The resolver does not advance clocks. game.clocks.advance_clock is a separate chat-path call.",
        "narration": "Structured resolution is handed to narration later. This experiment does not call narration.",
    },
    {
        "operation_class": "ATTACK",
        "classification": "SUPPORTED WITH ADAPTER",
        "resolver": "game.combat.resolve_attack",
        "existing_types": "attack",
        "input": "character, scene, attack_id, target_id, modifiers, conditions",
        "world_fields": "scene.scene.enemies[].id, enemies[].hp.current, character.attacks, conditions",
        "target_validation": "A safe adapter must require a living enemy id. combat.ensure_target falls back to the first living enemy when the id is missing, so a direct call is not safe.",
        "dependencies": "can_attack, attack bonus, AC, roll_die. The roll happens inside the resolver, not in the interpretation.",
        "output": "CombatEngineResult kind=attack with hit, damage_dealt, rolls, target_hp_remaining",
        "persistence": "Mutates enemy hp on the in-memory scene. The caller would save that scene. Not called in PR-DP.",
        "time": "The attack result sets turn_advanced false. advance_turn is separate.",
        "narration": "result.hint is the narration handoff. The model does not write the hint.",
    },
    {
        "operation_class": "INSPECT",
        "classification": "SUPPORTED WITH ADAPTER",
        "resolver": "game.exploration.resolve_exploration_action",
        "existing_types": "investigate, observe",
        "input": "normalized_action.type, interactable id, scene envelope, session, world",
        "world_fields": "scene.interactables, visible facts, optional skill_check",
        "target_validation": "The id must be an authored interactable in the active scene.",
        "dependencies": "Optional skill check rolls inside the exploration resolver when a check is configured.",
        "output": "kind observe or investigate, success when a check ran",
        "persistence": "api.mark_interactable_resolved can record a discovered clue on the session after the caller accepts the result.",
        "time": "Not advanced by the resolver.",
        "narration": "Structured resolution and visible interactable text. Hidden facts stay out of the handoff.",
    },
    {
        "operation_class": "ASK",
        "classification": "SUPPORTED WITH ADAPTER",
        "resolver": "game.social.resolve_social_action",
        "existing_types": "question",
        "input": "normalized_action.type=question, target_id, raw player utterance, scene, session, world",
        "world_fields": "NPC roster, scene addressability, session.npc_runtime",
        "target_validation": "resolve_authoritative_social_target must bind an addressable NPC. A guessed id is not accepted.",
        "dependencies": "NPC record and authored knowledge. Question content comes from the player utterance, not from player_intent.summary.",
        "output": "Social result with npc_id, hint, and optional topic disclosure",
        "persistence": "May update session.npc_runtime on the disposable session.",
        "time": "Not advanced by the resolver.",
        "narration": "Social hint is the handoff. Requested outcomes stay unadjudicated and are not copied in.",
    },
    {
        "operation_class": "SOCIAL_SIGNAL",
        "classification": "PARTIALLY SUPPORTED",
        "resolver": "none with equivalent semantics",
        "existing_types": "social_probe is a different check-based probe",
        "input": "No gesture or beckon payload exists",
        "world_fields": "NPC presence only",
        "target_validation": "An NPC id can be checked for addressability, but that does not perform the signal.",
        "dependencies": "Would require treating a gesture as social_probe, which is a different mechanic.",
        "output": "No equivalent result object",
        "persistence": "None",
        "time": "None",
        "narration": "No engine handoff for a gesture.",
    },
    {
        "operation_class": "PERCEIVE",
        "classification": "SUPPORTED WITH ADAPTER",
        "resolver": "game.exploration.resolve_exploration_action",
        "existing_types": "observe",
        "input": "normalized_action.type=observe and a visible target id",
        "world_fields": "scene.visible facts and interactables",
        "target_validation": "Target must be visible in the active scene.",
        "dependencies": "Optional perception skill check only when the scene configures one.",
        "output": "kind=observe",
        "persistence": "Usually none beyond the caller session log.",
        "time": "Not advanced by the resolver.",
        "narration": "Visible facts only.",
    },
    {
        "operation_class": "FOLLOW",
        "classification": "PARTIALLY SUPPORTED",
        "resolver": "game.exploration.apply_follow_lead_commitment_after_resolved_scene_transition",
        "existing_types": "follow-lead metadata on a scene transition",
        "input": "A resolved scene transition plus pursuit metadata from the intent parser",
        "world_fields": "lead subject, destination scene",
        "target_validation": "The lead must already be a discourse or scene lead. Following an arbitrary person is not the same operation.",
        "dependencies": "A prior scene_transition. It is not a standalone follow resolver.",
        "output": "Commitment stored after the transition",
        "persistence": "Session lead commitment when the caller applies it.",
        "time": "Inherits the transition caller. The helper itself is not a clock.",
        "narration": "Destination narration after the transition.",
    },
    {
        "operation_class": "USE_VISIBLE_OBJECT",
        "classification": "PARTIALLY SUPPORTED",
        "resolver": "game.exploration.resolve_exploration_action",
        "existing_types": "interact, custom",
        "input": "normalized_action.type=interact and an interactable id",
        "world_fields": "scene.interactables",
        "target_validation": "Authored interactable id. Free-form use, such as holding a lantern up, has no separate state transition.",
        "dependencies": "Optional skill check on the interactable.",
        "output": "kind=interact or custom",
        "persistence": "mark_interactable_resolved when a clue is consumed.",
        "time": "Not advanced by the resolver.",
        "narration": "Interactable result text.",
    },
)


UNSUPPORTED = (
    "HP_ASSIGNMENT",
    "DICE_OVERRIDE",
    "INVENTORY_GRANT",
    "CANON_DECLARATION",
    "NPC_COMMITMENT",
    "HIDDEN_INFORMATION_REQUEST",
    "RETCON",
    "UNSUPPORTED_MECHANIC",
    "TIME_CONTROL",
    "STEALTH_MODE_TOGGLE",
)


def inventory_markdown() -> str:
    lines = [
        "# PR-DP Engine Capability Inventory",
        "",
        "Inspection only. No resolver was added or called. Names that look alike were not treated as the same operation.",
        "",
        "`engine_submission` is still unconnected to these resolvers. `ELIGIBLE_FOR_VALIDATION` is not execution.",
        "",
        "## Allowlisted classes",
        "",
    ]
    for row in INVENTORY:
        lines += [
            f"### {row['operation_class']}",
            "",
            f"Classification: {row['classification']}",
            "",
            f"- Matching resolver: {row['resolver']}",
            f"- Existing types: {row['existing_types']}",
            f"- Required input: {row['input']}",
            f"- World-state fields: {row['world_fields']}",
            f"- Target validation: {row['target_validation']}",
            f"- Mechanical dependencies: {row['dependencies']}",
            f"- Output: {row['output']}",
            f"- Persistence: {row['persistence']}",
            f"- Time: {row['time']}",
            f"- Narration handoff: {row['narration']}",
            "",
        ]
    lines += [
        "## Unsupported classes",
        "",
        "These classes have no gameplay resolver. The PR-DO eligibility function already returns `UNSUPPORTED_OPERATION` and an empty submission when one of them is present. That refusal is the support.",
        "",
    ]
    for name in UNSUPPORTED:
        lines.append(f"- {name}: UNSUPPORTED")
    lines += [
        "",
        "## Slice mapping",
        "",
        "The designed sequence uses `PERCEIVE` or `INSPECT` (`observe`), `ASK` (`question`), `MOVE` only when the target id is an authored exit (`scene_transition`), and `INSPECT` (`investigate`) in the destination scene.",
        "",
        "That mapping is safe when the adapter checks entity kind, passes the player utterance rather than model prose, and does not call `combat.ensure_target`. `ATTACK` is available for a later slice, but its fallback-to-first-enemy behavior is excluded from this sequence.",
        "",
        f"SLICE_MAPPING_SAFE: {SLICE_MAPPING_SAFE}",
        "",
        f"SLICE_UNSUPPORTED: {SLICE_UNSUPPORTED}",
        "",
    ]
    return "\n".join(lines)


def vertical_slice_markdown() -> str:
    return """# PR-DP Vertical Slice Design

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
"""
