# PR-PLAY-23 action pipeline

Relevant source anchors (function names are stable; line numbers are in packaged source):

| Stage | Production source / function |
| --- | --- |
| Entry / dispatch | game/api.py:_chat_turn (6644); stored/live interpretation branches around 6744–6870; resolve_social_action call in existing dispatch |
| Interpretation / parser | game/live_chat_interpretation.py:interpret_production_turn; request_interpretation; adapt_interpretation from the existing experiment contract; multi-component handoff around 550 |
| Decision / normalization | game/conversational_orchestration.py:decision_from_interpretation_record (2195); game/local_interaction.py:normalize_local_approach |
| Compound sequencing | game/conversational_orchestration.py:_compound_from_record_parts (1999), _compound_clarification (1681), _resume_pending_decision |
| Catalog / binding | game/player_interpretation_bridge.py:visible_catalog (36), normalized_action_from_interpretation (197) |
| Addressee grounding | game/ordinary_semantic_ownership.py:assess_addressee_grounding (651) |
| Authored addressability | game/interaction_context.py:is_actor_addressable_in_current_scene (757) |
| Social authority | game/social.py:resolve_social_action (3895); game/dialogue_authority.py knowledge/disclosure selection |
| Movement authority | game/exploration.py:resolve_exploration_action; existing reachability checks; game/scene_graph.py |
| Publication | game/api.py existing response/finalization path; game/immutable_valid_response.py; game/state_channels.py:deep_project_public_payload |
| Ordinary time effects | game/api.py normal turn dispatch → game/world.py:advance_world_tick (325) |

MOVE bridge means scene_transition and requires a visible exit, authored destination, and known destination scene. It does not implement free local relocation. The ordinary deterministic parser also has a custom local-physical-movement lane; it does not maintain a coordinate grid. This patch does not expand that lane.

ASK carries target_ref=tavern_runner and has sufficient information to attempt a question. visible_catalog derives NPCs from authoritative world.npcs.location matching the scene ID. An opening narration mention alone does not register an NPC. In the captured world the runner is a real authored NPC, available and friendly, with location=frontier_gate; scene.addressables explicitly marks it addressable=true. It is neither a temporary presentation invention nor a fabricated persistent record.

INSPECT binds authored interactables to investigate; visible surface inspection already falls back to the existing supported surface behavior. No examination capability is added. NPC and object operations retain their respective resolvers.

Answers to the ten investigation questions:

1. MOVE describes the provider's reasonable physical approach proposal.
2. The stored interpretation MOVE bridge is scene-transition-only; other parser-local movement exists separately.
3. The runner resolves through authoritative world location plus authored scene addressability.
4. ASK already has its target and question intent.
5. No independent relocation is needed to attempt this same-scene conversation.
6. A literal, same-target preamble can be normalized with authored eligibility and no access caveat.
7. Current-scene membership, explicit authored addressability, canonical addressability, actual interaction binding, and conservative caveat rejection protect the new rule. General spatial reachability is NOT implemented; uncertain cases stay compound/declined.
8. Unsupported first steps prevent later dependent execution. Multiple supported consequential steps still require confirmation.
9. Existing incidental THANK/posture handling exists; local approach previously remained consequential. The new rule is explicit and independently tested.
10. A successful ASK legitimately advances one normal gameplay turn, world tick, log and dialogue bookkeeping. No approach-specific position, travel, currency, inventory, quest or relationship effect is added.
