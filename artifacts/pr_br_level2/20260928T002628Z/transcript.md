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

Contract: `{"contract_id": "rc_d86535730220", "turn_index": 2, "request_kind": "inquiry", "operation": "perceive", "target_ref": {"type": "object", "id_or_text": "This close, what does it smell like?", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "This close, what does it smell like?", "dimension": "smell", "dimensions": ["smell"], "expected_resolution": "answer", "epistemic_mode": "bounded_incidental", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "This close, what does it smell like?"}`

Obligation: `{"kind": "inspection", "target": "This close, what does it smell like?", "interlocutor_id": null, "subject": "This close, what does it smell like", "requested_outcome": "resolve the inspection from authoritative or bounded incidental detail", "claim_id": null, "resolution_mode": "bounded_improvisable_request", "turn_index": 2, "resolution_contract_id": "rc_d86535730220"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "This close, what does it smell like?", "label": "This close, what does it smell like?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 2, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 2, "last_committed_contract_id": "rc_d86535730220"}`

Authority: `{"mode": "bounded_improvisable_request", "requested_dimension": "smell", "contract_id": "rc_d86535730220", "reason_codes": ["incidental_description_gap", "contract_dimension:smell"], "proposal_created": true}`

Emission: `{"status": "satisfied", "reasons": ["covered:smell"], "contract_id": "rc_d86535730220"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_d86535730220", "dimension": "smell", "dimensions": ["smell"], "operation": "perceive", "referent_provenance": "explicit_player", "assessment_status": "satisfied", "assessment_reasons": ["covered:smell"]}}`

## perception_wear_referent

Player: Is the wear on it from the weather, or does it look recently handled?

GM: No reliable source here can verify Is the wear on it from the weather, or does it look recently handled; another source is needed.

Semantic: `PASS`

Contract: `{"contract_id": "rc_6503cc18e4dc", "turn_index": 3, "request_kind": "inquiry", "operation": "perceive", "target_ref": {"type": "object", "id_or_text": "Is the wear on it from the weather, or does it look recently handled?", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "Is the wear on it from the weather, or does it look recently handled?", "dimension": "wear", "dimensions": ["wear"], "expected_resolution": "answer", "epistemic_mode": "bounded_incidental", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "Is the wear on it from the weather, or does it look recently handled?"}`

Obligation: `{"kind": "question", "target": "Is the wear on it from the weather, or does it look recently handled?", "interlocutor_id": null, "subject": "Is the wear on it from the weather, or does it look recently handled", "requested_outcome": "answer, admit uncertainty, refuse, or redirect the question", "claim_id": null, "resolution_mode": "grounded_information_request", "turn_index": 3, "resolution_contract_id": "rc_6503cc18e4dc"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "Is the wear on it from the weather, or does it look recently handled?", "label": "Is the wear on it from the weather, or does it look recently handled?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 3, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 3, "last_committed_contract_id": "rc_6503cc18e4dc"}`

Authority: `{"mode": "grounded_information_request", "requested_dimension": "wear", "contract_id": "rc_6503cc18e4dc", "reason_codes": ["default_existing_resolution", "contract_dimension:wear"], "proposal_created": false}`

Emission: `{"status": "satisfied", "reasons": ["covered:wear"], "contract_id": "rc_6503cc18e4dc"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_6503cc18e4dc", "dimension": "wear", "dimensions": ["wear"], "operation": "perceive", "referent_provenance": "explicit_player", "assessment_status": "satisfied", "assessment_reasons": ["covered:wear"]}}`

## establish_claim

Player: I catch the stew-seller's attention and ask what rumor he has been repeating tonight.

GM: Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."

Semantic: `PASS`

Contract: `{"contract_id": "rc_53ac763498a4", "turn_index": 4, "request_kind": "inquiry", "operation": "ask", "target_ref": {"type": "object", "id_or_text": "what rumor he has been repeating tonight", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "what rumor he has been repeating tonight", "dimension": null, "dimensions": [], "expected_resolution": "answer", "epistemic_mode": "npc_claim", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "I catch the stew-seller's attention and ask what rumor he has been repeating tonight."}`

Obligation: `{"kind": "question", "target": "what rumor he has been repeating tonight", "interlocutor_id": null, "subject": "what rumor he has been repeating tonight", "requested_outcome": "answer, admit uncertainty, refuse, or redirect the question", "claim_id": null, "resolution_mode": "npc_claim_response", "turn_index": 4, "resolution_contract_id": "rc_53ac763498a4"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": null, "active_actionable_lead": null, "active_inspected": {"id": "Is the wear on it from the weather, or does it look recently handled?", "label": "Is the wear on it from the weather, or does it look recently handled?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 3, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 4, "last_committed_contract_id": "rc_53ac763498a4"}`

Authority: `{"mode": "npc_claim_response", "requested_dimension": null, "contract_id": "rc_53ac763498a4", "reason_codes": ["npc_claim_or_epistemic_question"], "proposal_created": true}`

Emission: `{"status": "unchecked", "reasons": ["no_dimension"], "contract_id": "rc_53ac763498a4"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_53ac763498a4", "dimension": null, "dimensions": [], "operation": "ask", "referent_provenance": "explicit_player", "assessment_status": "unchecked", "assessment_reasons": ["no_dimension"]}}`

## claim_source

Player: Where did you hear that?

GM: No reliable source can verify who began the earlier claim or how certain it is.

Semantic: `PASS`

Contract: `{"contract_id": "rc_38cd3b07eb90", "turn_index": 5, "request_kind": "inquiry", "operation": "ask", "target_ref": {"type": "object", "id_or_text": "Where did you hear that?", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "Where did you hear that?", "dimension": "location", "dimensions": ["location", "source", "sound"], "expected_resolution": "answer", "epistemic_mode": "bounded_incidental", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "Where did you hear that?"}`

Obligation: `{"kind": "follow_up", "target": "Where did you hear that?", "interlocutor_id": null, "subject": "The guard says, \"I do not know enough to answer that.\"", "requested_outcome": "answer, qualify, refuse, or redirect the follow-up about the established claim", "claim_id": "bi_668df3fd5e26", "resolution_mode": "npc_claim_response", "turn_index": 5, "resolution_contract_id": "rc_38cd3b07eb90"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": {"id": null, "label": "Where did you hear that?", "kind": "claim", "scene_id": "frontier_gate", "turn_index": 5, "source": "resolution_contract"}, "active_actionable_lead": null, "active_inspected": {"id": "Is the wear on it from the weather, or does it look recently handled?", "label": "Is the wear on it from the weather, or does it look recently handled?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 3, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 5, "last_committed_contract_id": "rc_38cd3b07eb90"}`

Authority: `{"mode": "npc_claim_response", "requested_dimension": "location", "contract_id": "rc_38cd3b07eb90", "reason_codes": ["npc_claim_or_epistemic_question", "contract_dimension:location"], "proposal_created": true}`

Emission: `{"status": "partial", "reasons": ["covered:sound", "missing:location", "missing:source"], "contract_id": "rc_38cd3b07eb90"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_38cd3b07eb90", "dimension": "location", "dimensions": ["location", "source", "sound"], "operation": "ask", "referent_provenance": "explicit_player", "assessment_status": "partial", "assessment_reasons": ["covered:source", "missing:location", "missing:sound"]}}`

## claim_confidence

Player: How sure are you, honestly?

GM: No reliable source here can verify How sure are you, honestly; another source is needed.

Semantic: `PASS`

Contract: `{"contract_id": "rc_355092ece732", "turn_index": 6, "request_kind": "inquiry", "operation": "ask", "target_ref": {"type": "object", "id_or_text": "How sure are you, honestly?", "source": "explicit_player"}, "interlocutor_id": null, "conversational_subject": "How sure are you, honestly?", "dimension": "confidence", "dimensions": ["confidence"], "expected_resolution": "answer", "epistemic_mode": "npc_claim", "discourse_ref": null, "referent_provenance": "explicit_player", "ambiguous": false, "raw_input": "How sure are you, honestly?"}`

Obligation: `{"kind": "question", "target": "How sure are you, honestly?", "interlocutor_id": null, "subject": "How sure are you, honestly", "requested_outcome": "answer, admit uncertainty, refuse, or redirect the question", "claim_id": "bi_4bf69a208915", "resolution_mode": "grounded_information_request", "turn_index": 6, "resolution_contract_id": "rc_355092ece732"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": {"id": null, "label": "How sure are you, honestly?", "kind": "claim", "scene_id": "frontier_gate", "turn_index": 6, "source": "resolution_contract"}, "active_actionable_lead": null, "active_inspected": {"id": "Is the wear on it from the weather, or does it look recently handled?", "label": "Is the wear on it from the weather, or does it look recently handled?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 3, "source": "resolution_contract"}, "last_attempted_action": null, "last_committed_turn": 6, "last_committed_contract_id": "rc_355092ece732"}`

Authority: `{"mode": "grounded_information_request", "requested_dimension": "confidence", "contract_id": "rc_355092ece732", "reason_codes": ["default_existing_resolution", "contract_dimension:confidence"], "proposal_created": false}`

Emission: `{"status": "satisfied", "reasons": ["covered:confidence"], "contract_id": "rc_355092ece732"}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_355092ece732", "dimension": "confidence", "dimensions": ["confidence"], "operation": "ask", "referent_provenance": "explicit_player", "assessment_status": "satisfied", "assessment_reasons": ["covered:confidence"]}}`

## follow_lead

Player: All right. I follow that lead.

GM: The requested action cannot be completed here; another route is needed.

Semantic: `PASS`

Contract: `{"contract_id": "rc_a4faf5579192", "turn_index": 7, "request_kind": "clarification", "operation": "follow", "target_ref": {"type": "lead", "id_or_text": "that lead", "source": "unresolved"}, "interlocutor_id": null, "conversational_subject": "that lead", "dimension": null, "dimensions": [], "expected_resolution": "clarification", "epistemic_mode": "authoritative", "discourse_ref": null, "referent_provenance": "unresolved", "ambiguous": false, "raw_input": "All right. I follow that lead."}`

Obligation: `{"kind": "action_request", "target": "All right. I follow that lead.", "interlocutor_id": null, "subject": "All right. I follow that lead.", "requested_outcome": "resolve the attempted action, obstruction, or consequence", "claim_id": "bi_4bf69a208915", "resolution_mode": "grounded_information_request", "turn_index": 7, "resolution_contract_id": "rc_a4faf5579192"}`

Discourse: `{"version": 1, "scene_id": "frontier_gate", "active_interlocutor": null, "active_claim": {"id": null, "label": "How sure are you, honestly?", "kind": "claim", "scene_id": "frontier_gate", "turn_index": 6, "source": "resolution_contract"}, "active_actionable_lead": {"id": null, "label": "that lead", "kind": "lead", "scene_id": "frontier_gate", "turn_index": 7, "source": "resolution_contract"}, "active_inspected": {"id": "Is the wear on it from the weather, or does it look recently handled?", "label": "Is the wear on it from the weather, or does it look recently handled?", "kind": "object", "scene_id": "frontier_gate", "turn_index": 3, "source": "resolution_contract"}, "last_attempted_action": {"id": "rc_a4faf5579192", "label": "All right. I follow that lead.", "kind": "follow", "scene_id": "frontier_gate", "turn_index": 7, "source": "resolution_contract"}, "last_committed_turn": 7, "last_committed_contract_id": "rc_a4faf5579192"}`

Authority: `{"mode": "grounded_information_request", "requested_dimension": null, "contract_id": "rc_a4faf5579192", "reason_codes": ["default_existing_resolution"], "proposal_created": false}`

Emission: `{"status": "legitimate_nonresolution", "reasons": ["clarification_or_inability"], "contract_id": "rc_a4faf5579192", "replaced": true, "replaced_preview": "You act on that move, and the situation answers that move right away."}`

Evaluator: `{"status": "PASS", "reason_codes": [], "resolution_contract": {"contract_id": "rc_a4faf5579192", "dimension": null, "dimensions": [], "operation": "follow", "referent_provenance": "unresolved", "assessment_status": "legitimate_nonresolution", "assessment_reasons": ["clarification_or_inability"]}}`
