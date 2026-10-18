# PR-DK Failure Reconstruction

## C1

Raw input: Does rain make it easier to assassinate the captain?

Parsed components:

- operation: ask
- resolver: social
- dimension(s): []
- entity binding: {'status': 'bound_canonical', 'entity_class': 'canonical_established', 'proposed_interlocutor': None, 'proposed_span': None, 'bound_interlocutor_id': 'guard_captain', 'entity_id': None, 'label': 'Guard Captain', 'explicit_new_interlocutor': False, 'authority_reasons': ['identity:discourse'], 'claim_binding': 'none'}
- secondary operations: []
- executable obligations: {'primary': None, 'mutation_owner': None, 'sequence': [], 'supporting': []}

Construction output:

- proposal source: discourse_inheritance
- validation: validated / {'status': 'validated', 'reason': None, 'failed_fields': [], 'clarification_required': False, 'model_interpretation_appropriate': False, 'canonical_target_id': 'guard_captain', 'canonical_target_label': 'Guard Captain', 'canonical_target_type': 'interlocutor', 'canonical_basis': 'discourse', 'authoritative_operation': 'ask', 'discourse_commit_allowed': True, 'compatibility_bridge': None}
- referent reason: unambiguous_discourse_referent
- resolution subject: social

Escalation signals:

- existing: {'explicit_abstention': False, 'unsupported_resolver_outcome': False, 'missing_required_entity': False, 'unresolved_pronoun': False, 'multiple_possible_referents': False, 'compound_action': False, 'resolver_disagreement': False, 'unsupported_mechanic': False, 'attempted_direct_state_override': False, 'attempted_world_canon_declaration': False}
- independent: {'multiple_independent_action_clauses': False, 'unresolved_personal_pronoun': False, 'multiple_plausible_referents': False, 'input_action_contract_mismatch': False, 'omitted_action_components': False, 'missing_required_participants': False, 'unsupported_secondary_actions': False, 'consequential_social_interpretation': True}

Information loss:

The ask is resolved as ordinary social dialogue against the inherited guard captain. The consequential feasibility content, assassinating the captain in the rain, is not represented as a protected consequence or unsupported request.


## compound

Raw input: I walk closer to the notice board and pry it off the post.

Parsed components:

- operation: act
- resolver: travel
- dimension(s): []
- entity binding: {'status': 'unresolved', 'entity_class': 'ambiguous_unresolved', 'proposed_interlocutor': None, 'proposed_span': None, 'bound_interlocutor_id': None, 'entity_id': None, 'label': None, 'explicit_new_interlocutor': False, 'authority_reasons': [], 'claim_binding': 'none'}
- secondary operations: []
- executable obligations: {'primary': None, 'mutation_owner': None, 'sequence': [], 'supporting': []}

Construction output:

- proposal source: deterministic_fast_path
- validation: abstained / {'status': 'abstained', 'reason': 'insufficient_discourse_context', 'failed_fields': ['raw_target_text'], 'clarification_required': True, 'model_interpretation_appropriate': True, 'canonical_target_id': None, 'canonical_target_label': None, 'canonical_target_type': None, 'canonical_basis': None, 'authoritative_operation': 'unresolved', 'discourse_commit_allowed': False, 'compatibility_bridge': None}
- referent reason: no_referent
- resolution subject: travel

Escalation signals:

- existing: {'explicit_abstention': False, 'unsupported_resolver_outcome': False, 'missing_required_entity': False, 'unresolved_pronoun': False, 'multiple_possible_referents': False, 'compound_action': False, 'resolver_disagreement': False, 'unsupported_mechanic': False, 'attempted_direct_state_override': False, 'attempted_world_canon_declaration': False}
- independent: {'multiple_independent_action_clauses': True, 'unresolved_personal_pronoun': False, 'multiple_plausible_referents': False, 'input_action_contract_mismatch': True, 'omitted_action_components': True, 'missing_required_participants': False, 'unsupported_secondary_actions': True, 'consequential_social_interpretation': False}

Information loss:

The raw text contains approach plus pry, but construction records no secondary operation or executable sequence. The selected resolver is travel, so the pry component is discarded before existing routing sees it.


## ambiguous

Raw input: Ask him whether we should trust the other one.

Parsed components:

- operation: ask
- resolver: social
- dimension(s): confidence
- entity binding: {'status': 'unresolved', 'entity_class': 'ambiguous_unresolved', 'proposed_interlocutor': None, 'proposed_span': None, 'bound_interlocutor_id': None, 'entity_id': None, 'label': None, 'explicit_new_interlocutor': False, 'authority_reasons': [], 'claim_binding': 'unresolved'}
- secondary operations: []
- executable obligations: {'primary': None, 'mutation_owner': None, 'sequence': [], 'supporting': []}

Construction output:

- proposal source: deterministic_fast_path
- validation: validated / {'status': 'validated', 'reason': None, 'failed_fields': [], 'clarification_required': False, 'model_interpretation_appropriate': False, 'canonical_target_id': None, 'canonical_target_label': None, 'canonical_target_type': None, 'canonical_basis': None, 'authoritative_operation': 'ask', 'discourse_commit_allowed': True, 'compatibility_bridge': None}
- referent reason: claim_unresolved
- resolution subject: social

Escalation signals:

- existing: {'explicit_abstention': False, 'unsupported_resolver_outcome': False, 'missing_required_entity': False, 'unresolved_pronoun': False, 'multiple_possible_referents': False, 'compound_action': False, 'resolver_disagreement': False, 'unsupported_mechanic': False, 'attempted_direct_state_override': False, 'attempted_world_canon_declaration': False}
- independent: {'multiple_independent_action_clauses': False, 'unresolved_personal_pronoun': True, 'multiple_plausible_referents': True, 'input_action_contract_mismatch': False, 'omitted_action_components': False, 'missing_required_participants': True, 'unsupported_secondary_actions': False, 'consequential_social_interpretation': False}

Information loss:

The fast path validates an ask with confidence dimension while leaving `him` and `the other one` unresolved. Because `ambiguous` remains false, pronoun and multiple-referent signals do not fire.
