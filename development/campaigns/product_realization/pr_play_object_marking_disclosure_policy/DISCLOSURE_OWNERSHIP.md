# Disclosure Ownership

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

Decision **B**: add narrow shared game.object_observation, using existing identity and character-host authority. No owner already supplies observation of durable instance properties.

| Responsibility | Existing owner and reference |
|---|---|
| Scene/public entity visibility | game/narration_visibility.py: build_narration_visibility_contract; game/scene_state_anchoring.py: public read contract |
| Checks and perception success | game/skill_checks.py: resolve_skill_check; game/exploration.py: process_investigation_discovery |
| Hidden/authored inspection targets | game/referenced_surface.py: target binding/render_referenced_surface_inspection_line; exploration.resolve_interactable_hidden_fact_text |
| Resolved clue disclosure | game/authorized_information.py: revealed_information; only selected successful resolver output |
| Internal object inspection | game/object_marking.py: inspect_markings; full authoritative read, unsuitable for observer payloads |
| Provider evidence projection | game/narration_authorization.py: project_narration_payload |
| Player HTTP state | game/player_http_projection.py: source-specific allowlists; inventory ITEM has no markings |
| Immutable publication | game/immutable_valid_response.py: seal_delivery_contract/verify_delivery_record; game/publication_contract.py |
| State ownership | game/state_authority.py: WORLD_STATE authoritative and PLAYER_VISIBLE_STATE derived; storage character host |

Extending narrative visibility would couple durable instances to scene prose/entity matching. Extending authorized_information would couple generic property reads to completed clue resolution. Extending internal inspect_markings would change its intentionally private contract and couple observation to receipt history. The narrow projector consumes existing durable identities and established internal authority instead; it neither decides perception nor publishes. Existing modules, authority registry and endpoints remain unchanged. Approved architecture sources: development/campaigns/product_realization/pr_play_object_identity_architecture/{CORE_RULESET_BOUNDARY,OBJECT_INSTANCE_CONTRACT,MODIFICATION_CONTRACT,ACTION_RESOLUTION_CONTRACT,MUNDANE_AFFORDANCE_POLICY,IMPLEMENTATION_ROADMAP}.md. This cycle implements the read boundary only.
