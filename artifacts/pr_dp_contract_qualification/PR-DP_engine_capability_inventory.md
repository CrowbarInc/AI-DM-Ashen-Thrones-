# PR-DP Engine Capability Inventory

Inspection only. No resolver was added or called. Names that look alike were not treated as the same operation.

`engine_submission` is still unconnected to these resolvers. `ELIGIBLE_FOR_VALIDATION` is not execution.

## Allowlisted classes

### MOVE

Classification: PARTIALLY SUPPORTED

- Matching resolver: game.exploration.resolve_exploration_action
- Existing types: scene_transition, travel
- Required input: normalized_action.type plus targetSceneId, a scene graph, list_scene_ids, and load_scene_fn
- World-state fields: scene.exits, scene.id, session active scene
- Target validation: The target must already be an authored exit. Intra-scene walking has no position field.
- Mechanical dependencies: Caller performs activate_scene after a resolved transition. The resolver itself has no side effects.
- Output: kind, resolved_transition, optional skill_check
- Persistence: Caller saves the disposable session after activate_scene. Production saves are not in this path.
- Time: The resolver does not advance clocks. game.clocks.advance_clock is a separate chat-path call.
- Narration handoff: Structured resolution is handed to narration later. This experiment does not call narration.

### ATTACK

Classification: SUPPORTED WITH ADAPTER

- Matching resolver: game.combat.resolve_attack
- Existing types: attack
- Required input: character, scene, attack_id, target_id, modifiers, conditions
- World-state fields: scene.scene.enemies[].id, enemies[].hp.current, character.attacks, conditions
- Target validation: A safe adapter must require a living enemy id. combat.ensure_target falls back to the first living enemy when the id is missing, so a direct call is not safe.
- Mechanical dependencies: can_attack, attack bonus, AC, roll_die. The roll happens inside the resolver, not in the interpretation.
- Output: CombatEngineResult kind=attack with hit, damage_dealt, rolls, target_hp_remaining
- Persistence: Mutates enemy hp on the in-memory scene. The caller would save that scene. Not called in PR-DP.
- Time: The attack result sets turn_advanced false. advance_turn is separate.
- Narration handoff: result.hint is the narration handoff. The model does not write the hint.

### INSPECT

Classification: SUPPORTED WITH ADAPTER

- Matching resolver: game.exploration.resolve_exploration_action
- Existing types: investigate, observe
- Required input: normalized_action.type, interactable id, scene envelope, session, world
- World-state fields: scene.interactables, visible facts, optional skill_check
- Target validation: The id must be an authored interactable in the active scene.
- Mechanical dependencies: Optional skill check rolls inside the exploration resolver when a check is configured.
- Output: kind observe or investigate, success when a check ran
- Persistence: api.mark_interactable_resolved can record a discovered clue on the session after the caller accepts the result.
- Time: Not advanced by the resolver.
- Narration handoff: Structured resolution and visible interactable text. Hidden facts stay out of the handoff.

### ASK

Classification: SUPPORTED WITH ADAPTER

- Matching resolver: game.social.resolve_social_action
- Existing types: question
- Required input: normalized_action.type=question, target_id, raw player utterance, scene, session, world
- World-state fields: NPC roster, scene addressability, session.npc_runtime
- Target validation: resolve_authoritative_social_target must bind an addressable NPC. A guessed id is not accepted.
- Mechanical dependencies: NPC record and authored knowledge. Question content comes from the player utterance, not from player_intent.summary.
- Output: Social result with npc_id, hint, and optional topic disclosure
- Persistence: May update session.npc_runtime on the disposable session.
- Time: Not advanced by the resolver.
- Narration handoff: Social hint is the handoff. Requested outcomes stay unadjudicated and are not copied in.

### SOCIAL_SIGNAL

Classification: PARTIALLY SUPPORTED

- Matching resolver: none with equivalent semantics
- Existing types: social_probe is a different check-based probe
- Required input: No gesture or beckon payload exists
- World-state fields: NPC presence only
- Target validation: An NPC id can be checked for addressability, but that does not perform the signal.
- Mechanical dependencies: Would require treating a gesture as social_probe, which is a different mechanic.
- Output: No equivalent result object
- Persistence: None
- Time: None
- Narration handoff: No engine handoff for a gesture.

### PERCEIVE

Classification: SUPPORTED WITH ADAPTER

- Matching resolver: game.exploration.resolve_exploration_action
- Existing types: observe
- Required input: normalized_action.type=observe and a visible target id
- World-state fields: scene.visible facts and interactables
- Target validation: Target must be visible in the active scene.
- Mechanical dependencies: Optional perception skill check only when the scene configures one.
- Output: kind=observe
- Persistence: Usually none beyond the caller session log.
- Time: Not advanced by the resolver.
- Narration handoff: Visible facts only.

### FOLLOW

Classification: PARTIALLY SUPPORTED

- Matching resolver: game.exploration.apply_follow_lead_commitment_after_resolved_scene_transition
- Existing types: follow-lead metadata on a scene transition
- Required input: A resolved scene transition plus pursuit metadata from the intent parser
- World-state fields: lead subject, destination scene
- Target validation: The lead must already be a discourse or scene lead. Following an arbitrary person is not the same operation.
- Mechanical dependencies: A prior scene_transition. It is not a standalone follow resolver.
- Output: Commitment stored after the transition
- Persistence: Session lead commitment when the caller applies it.
- Time: Inherits the transition caller. The helper itself is not a clock.
- Narration handoff: Destination narration after the transition.

### USE_VISIBLE_OBJECT

Classification: PARTIALLY SUPPORTED

- Matching resolver: game.exploration.resolve_exploration_action
- Existing types: interact, custom
- Required input: normalized_action.type=interact and an interactable id
- World-state fields: scene.interactables
- Target validation: Authored interactable id. Free-form use, such as holding a lantern up, has no separate state transition.
- Mechanical dependencies: Optional skill check on the interactable.
- Output: kind=interact or custom
- Persistence: mark_interactable_resolved when a clue is consumed.
- Time: Not advanced by the resolver.
- Narration handoff: Interactable result text.

## Unsupported classes

These classes have no gameplay resolver. The PR-DO eligibility function already returns `UNSUPPORTED_OPERATION` and an empty submission when one of them is present. That refusal is the support.

- HP_ASSIGNMENT: UNSUPPORTED
- DICE_OVERRIDE: UNSUPPORTED
- INVENTORY_GRANT: UNSUPPORTED
- CANON_DECLARATION: UNSUPPORTED
- NPC_COMMITMENT: UNSUPPORTED
- HIDDEN_INFORMATION_REQUEST: UNSUPPORTED
- RETCON: UNSUPPORTED
- UNSUPPORTED_MECHANIC: UNSUPPORTED
- TIME_CONTROL: UNSUPPORTED
- STEALTH_MODE_TOGGLE: UNSUPPORTED

## Slice mapping

The designed sequence uses `PERCEIVE` or `INSPECT` (`observe`), `ASK` (`question`), `MOVE` only when the target id is an authored exit (`scene_transition`), and `INSPECT` (`investigate`) in the destination scene.

That mapping is safe when the adapter checks entity kind, passes the player utterance rather than model prose, and does not call `combat.ensure_target`. `ATTACK` is available for a later slice, but its fallback-to-first-enemy behavior is excluded from this sequence.

SLICE_MAPPING_SAFE: True

SLICE_UNSUPPORTED: False
