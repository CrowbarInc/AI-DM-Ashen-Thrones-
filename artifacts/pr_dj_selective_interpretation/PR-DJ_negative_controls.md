# PR-DJ Negative Controls

- negative_direct_hp_assignment: passed=True errors=['unknown fields are not allowed: hit_points']
- negative_world_flags: passed=True errors=['unknown fields are not allowed: world_flags']
- negative_unauthorized_npc_commitment: passed=True errors=['unknown fields are not allowed: npc_commitments']
- negative_hidden_information: passed=True errors=['unknown fields are not allowed: hidden_facts']
- negative_fabricated_dice: passed=True errors=['unknown fields are not allowed: dice_result']
- negative_invented_entity_id: passed=True errors=['referenced_entities[0].id is not canonical: invented_guard']
- negative_unsupported_resolver: passed=True errors=['unknown fields are not allowed: resolver']
- negative_execution_request: passed=True errors=['unknown fields are not allowed: execute_action']
- negative_silent_ambiguous_guess: passed=True errors=['ambiguous references may not be silently resolved']
- negative_malformed_output: passed=True errors=['payload must be an object']
