# PR-BR Level 2 probes

## establish_inspected

Player: I step under the frayed banner and look at the cloth itself, not the crowd.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Contract: `{"contract_id": "rc_ac1cd45c2d47", "turn_index": 1, "request_kind": "inquiry", "operation": "inspect", "target_ref": {"type": "object", "id_or_text": "cloth itself", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "cloth itself", "dimension": null, "dimensions": [], "expected_resolution": "answer", "epistemic_mode": "unknown_allowed", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "I step under the frayed banner and look at the cloth itself, not the crowd."}`

Obligation: `{"kind": "inspection", "target": "cloth itself, not the crowd", "interlocutor_id": null, "subject": "cloth itself, not the crowd", "requested_outcome": "resolve the inspection from authoritative or bounded incidental detail", "claim_id": null, "resolution_mode": "grounded_information_request", "turn_index": 1, "resolution_contract_id": "rc_ac1cd45c2d47"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "cloth itself", "label": "cloth itself", "kind": "object", "scene_id": "frontier_gate", "turn_index": 1, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 1, "last_committed_contract_id": "rc_ac1cd45c2d47"}`

Authority: `{"mode": "grounded_information_request", "requested_dimension": null, "contract_id": "rc_ac1cd45c2d47", "reason_codes": ["default_existing_resolution"], "proposal_created": false}`

Emission: `{"status": "unchecked", "reasons": ["no_dimension"], "contract_id": "rc_ac1cd45c2d47"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_ac1cd45c2d47", "dimension": null, "dimensions": [], "operation": "inspect", "referent_provenance": "explicit_player", "assessment_status": "unchecked", "assessment_reasons": ["no_dimension"]}}`

## perception_smell_referent

Player: This close, what does it smell like?

GM: No distinct sound or smell can be established beyond the current scene's general activity.

Semantic: `PASS`

Contract: `{"contract_id": "rc_d86535730220", "turn_index": 2, "request_kind": "inquiry", "operation": "perceive", "target_ref": {"type": "object", "id_or_text": "cloth itself", "source": "inherited_discourse"}, "interlocutor_id": null, "conversational_subject": "cloth itself", "dimension": "smell", "dimensions": ["smell"], "expected_resolution": "answer", "epistemic_mode": "bounded_incidental", "discourse_ref": {"type": "object", "id": "cloth itself", "label": "cloth itself", "source_turn": 1}, "referent_provenance": "inherited_discourse", "ambiguous": false, "raw_input": "This close, what does it smell like?"}`

Obligation: `{"kind": "inspection", "target": "This close, what does it smell like?", "interlocutor_id": null, "subject": "This close, what does it smell like", "requested_outcome": "resolve the inspection from authoritative or bounded incidental detail", "claim_id": null, "resolution_mode": "bounded_improvisable_request", "turn_index": 2, "resolution_contract_id": "rc_d86535730220"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "cloth itself", "label": "cloth itself", "kind": "object", "scene_id": "frontier_gate", "turn_index": 2, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 2, "last_committed_contract_id": "rc_d86535730220"}`

Authority: `{"mode": "bounded_improvisable_request", "requested_dimension": "smell", "contract_id": "rc_d86535730220", "reason_codes": ["incidental_description_gap", "contract_dimension:smell"], "proposal_created": true}`

Emission: `{"status": "satisfied", "reasons": ["covered:smell"], "contract_id": "rc_d86535730220"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_d86535730220", "dimension": "smell", "dimensions": ["smell"], "operation": "perceive", "referent_provenance": "inherited_discourse", "assessment_status": "satisfied", "assessment_reasons": ["covered:smell"]}}`

## claim_source_in_utterance

Player: I ask the stew-seller where he heard the rumor he has been repeating.

GM: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

Semantic: `PASS`

Contract: `{"contract_id": "rc_66ab1109e3b8", "turn_index": 3, "request_kind": "inquiry", "operation": "ask", "target_ref": null, "interlocutor_id": null, "conversational_subject": "I ask the stew-seller where he heard the rumor he has been repeating.", "dimension": null, "dimensions": [], "expected_resolution": "answer", "epistemic_mode": "npc_claim", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "I ask the stew-seller where he heard the rumor he has been repeating."}`

Obligation: `{"kind": "question", "target": "stew-seller where he heard the rumor he has been r", "interlocutor_id": null, "subject": "where he heard the rumor he has been repeating", "requested_outcome": "answer, admit uncertainty, refuse, or redirect the question", "claim_id": null, "resolution_mode": "npc_claim_response", "turn_index": 3, "resolution_contract_id": "rc_66ab1109e3b8"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "cloth itself", "label": "cloth itself", "kind": "object", "scene_id": "frontier_gate", "turn_index": 2, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 3, "last_committed_contract_id": "rc_66ab1109e3b8"}`

Authority: `{"mode": "npc_claim_response", "requested_dimension": null, "contract_id": "rc_66ab1109e3b8", "reason_codes": ["npc_claim_or_epistemic_question"], "proposal_created": true}`

Emission: `{"status": "unchecked", "reasons": ["no_dimension"], "contract_id": "rc_66ab1109e3b8"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_66ab1109e3b8", "dimension": null, "dimensions": [], "operation": "ask", "referent_provenance": "explicit_player", "assessment_status": "unchecked", "assessment_reasons": ["no_dimension"]}}`
