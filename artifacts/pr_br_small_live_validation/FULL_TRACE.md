# Complete attempted live transcript

Stopped after A2; A3/B1/B2/B3 were not run.

## A1

Player: I examine the cracked loom beam and bent iron brace closely. What does this damage suggest?

### Raw attempt 1

```json
{
  "declared_claims": [
    {
      "declaration_id": "rc_9deeeafa5043",
      "declaration_mode": "realize",
      "source_claim_id": null,
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact",
      "epistemic_status": "established",
      "modality": "established",
      "realization_role": "MUST_STATE",
      "relation_kind": "ordinary_predicate",
      "text": "The wooden loom beam is cracked."
    },
    {
      "declaration_id": "rc_49829b26c2ee",
      "declaration_mode": "realize",
      "source_claim_id": null,
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact",
      "epistemic_status": "established",
      "modality": "established",
      "realization_role": "MUST_STATE",
      "relation_kind": "ordinary_predicate",
      "text": "The loom's iron brace is bent."
    }
  ],
  "narration": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety. The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
  "player_facing_text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety. The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
  "tags": ["scene_momentum:new_information"],
  "improvisation_proposals": [
    {
      "kind": "incidental_fact",
      "category": "environmental_elaboration",
      "content": "Dust motes drift slowly through the workshop light, settling on the cracked beam and bent brace, highlighting how long the damage may have gone unrepaired.",
      "scope": "turn",
      "consequence_level": "incidental",
      "source": "dm_improvisation",
      "speaker_id": null,
      "epistemic_status": "grounded"
    }
  ],
  "scene_update": null,
  "activate_scene_id": null,
  "new_scene_draft": null,
  "world_updates": null,
  "suggested_action": null,
  "debug_notes": "Authoritative visible facts about the damage are realized with detail about likely causes and consequences, adding sensory texture and advancing the investigation momentum."
}
```

### Raw attempt 2

```json
{
  "declared_claims": [],
  "narration": "The wooden loom beam is cracked. Its iron brace is bent, both indicating wear and damage but without clear signs of how or when these occurred.",
  "player_facing_text": "The wooden loom beam is cracked. Its iron brace is bent, both indicating wear and damage but without clear signs of how or when these occurred.",
  "tags": [],
  "improvisation_proposals": null,
  "scene_update": null,
  "activate_scene_id": null,
  "new_scene_draft": null,
  "world_updates": null,
  "suggested_action": null,
  "debug_notes": "Narration complied with authorized facts only without asserting unseen causes or consequences."
}
```

### Exact sealed / emitted

The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.

### Full validation and temporal evidence

```json
{
  "turn": "A1",
  "attempt_1": {
    "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety. The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
    "reasons": [
      "unauthorized_resolution_decision_fact"
    ],
    "gm_resolution_decision_audit": {
      "decision_id": "rc_32e1dbe0f1e0",
      "hard_valid": false,
      "declaration_validation": {
        "schema_version": 1,
        "structured_contract_present": true,
        "hard_valid": true,
        "accepted_claims": [
          {
            "text": "The wooden loom beam is cracked.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.0",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The loom's iron brace is bent.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.1",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          }
        ],
        "rejected_claims": [],
        "violations": []
      },
      "narration_validation": {
        "decision_id": "rc_32e1dbe0f1e0",
        "hard_valid": false,
        "violations": [
          {
            "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
            "provenance": "generated_proposal",
            "consequence": "consequential",
            "authorized": false,
            "reason_codes": [
              "unsupported_narrator_lead"
            ],
            "authority": "unauthorized",
            "persistence": "do_not_persist",
            "source_ref": "",
            "outcome_classification": "consequentially_unresolved",
            "semantic_identity": {}
          }
        ],
        "proposed_facts": [
          {
            "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
            "provenance": "generated_proposal",
            "consequence": "consequential",
            "authorized": false,
            "reason_codes": [
              "unsupported_narrator_lead"
            ],
            "authority": "unauthorized",
            "persistence": "do_not_persist",
            "source_ref": "",
            "outcome_classification": "consequentially_unresolved",
            "semantic_identity": {}
          }
        ],
        "claim_results": [
          {
            "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
            "semantic_identity": {},
            "provenance": "generated_proposal",
            "authority": "unauthorized",
            "epistemic_status": "unresolved",
            "relation_kind": "gameplay_lead",
            "persistence": "do_not_persist",
            "authorized": false,
            "source_ref": "",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "unsupported_narrator_lead"
            ]
          }
        ]
      },
      "violations": [
        {
          "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
          "provenance": "generated_proposal",
          "consequence": "consequential",
          "authorized": false,
          "reason_codes": [
            "unsupported_narrator_lead"
          ],
          "authority": "unauthorized",
          "persistence": "do_not_persist",
          "source_ref": "",
          "outcome_classification": "consequentially_unresolved",
          "semantic_identity": {}
        },
        {
          "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
          "semantic_identity": {},
          "provenance": "generated_proposal",
          "authority": "unauthorized",
          "epistemic_status": "unresolved",
          "relation_kind": "ordinary_predicate",
          "persistence": "do_not_persist",
          "authorized": false,
          "source_ref": "",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "undeclared_causal_agent",
            "undeclared_consequential_claim"
          ]
        }
      ],
      "proposed_facts": [
        {
          "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
          "provenance": "generated_proposal",
          "consequence": "consequential",
          "authorized": false,
          "reason_codes": [
            "unsupported_narrator_lead"
          ],
          "authority": "unauthorized",
          "persistence": "do_not_persist",
          "source_ref": "",
          "outcome_classification": "consequentially_unresolved",
          "semantic_identity": {}
        }
      ],
      "claim_results": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The loom's iron brace is bent.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.1",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
          "semantic_identity": {},
          "provenance": "generated_proposal",
          "authority": "unauthorized",
          "epistemic_status": "unresolved",
          "relation_kind": "gameplay_lead",
          "persistence": "do_not_persist",
          "authorized": false,
          "source_ref": "",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "unsupported_narrator_lead"
          ]
        },
        {
          "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
          "semantic_identity": {},
          "provenance": "generated_proposal",
          "authority": "unauthorized",
          "epistemic_status": "unresolved",
          "relation_kind": "ordinary_predicate",
          "persistence": "do_not_persist",
          "authorized": false,
          "source_ref": "",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "undeclared_causal_agent",
            "undeclared_consequential_claim"
          ]
        }
      ],
      "accepted_realized_claims": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The loom's iron brace is bent.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.1",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        }
      ]
    }
  },
  "attempt_2": {
    "text": "The wooden loom beam is cracked. Its iron brace is bent, both indicating wear and damage but without clear signs of how or when these occurred.",
    "reasons": [
      "unauthorized_resolution_decision_fact"
    ],
    "gm_resolution_decision_audit": {
      "decision_id": "rc_32e1dbe0f1e0",
      "hard_valid": false,
      "declaration_validation": {
        "schema_version": 1,
        "structured_contract_present": true,
        "hard_valid": true,
        "accepted_claims": [],
        "rejected_claims": [],
        "violations": []
      },
      "narration_validation": {
        "decision_id": "rc_32e1dbe0f1e0",
        "hard_valid": true,
        "violations": [],
        "proposed_facts": [
          {
            "text": "The wooden loom beam is cracked.",
            "provenance": "authored_world_fact",
            "consequence": "consequential",
            "authorized": true,
            "reason_codes": [
              "authored_state_source"
            ],
            "authority": "world_truth",
            "persistence": "world_truth",
            "source_ref": "scene.visible_facts.0",
            "outcome_classification": "established_or_retrieved",
            "semantic_identity": {}
          }
        ],
        "claim_results": [
          {
            "text": "The wooden loom beam is cracked.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.0",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "authored_state_source"
            ]
          }
        ]
      },
      "violations": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "unauthorized",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": false,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "undeclared_consequential_claim"
          ]
        }
      ],
      "proposed_facts": [
        {
          "text": "The wooden loom beam is cracked.",
          "provenance": "authored_world_fact",
          "consequence": "consequential",
          "authorized": true,
          "reason_codes": [
            "authored_state_source"
          ],
          "authority": "world_truth",
          "persistence": "world_truth",
          "source_ref": "scene.visible_facts.0",
          "outcome_classification": "established_or_retrieved",
          "semantic_identity": {}
        }
      ],
      "claim_results": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "authored_state_source"
          ]
        },
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "unauthorized",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": false,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "undeclared_consequential_claim"
          ]
        }
      ],
      "accepted_realized_claims": []
    }
  },
  "accepted": {
    "immutable": true,
    "text": "The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
    "provenance": "initial_generation",
    "attempt": 1,
    "player_input": "I examine the cracked loom beam and bent iron brace closely",
    "turn_identity": "rc_32e1dbe0f1e0",
    "speaker": "",
    "addressee": "",
    "target": "wooden loom",
    "operation": "inspect",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [],
      "gm_resolution_decision_audit": {
        "decision_id": "rc_32e1dbe0f1e0",
        "hard_valid": true,
        "violations": [],
        "proposed_facts": [],
        "claim_results": []
      },
      "decision_acceptance_why": "bounded_sentence_preservation"
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_32e1dbe0f1e0",
      "operation": "inspect",
      "interlocutor_id": "",
      "expected_resolution": "answer"
    },
    "resolution_kind": "investigate",
    "generation_attempts": 1,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_repeated_description_guard",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ]
  },
  "retry_context": "The previous attempt was rejected for: unauthorized_resolution_decision_fact. It narrated consequential world facts that were not authorized by the pre-narration GM resolution decision. Answer again as the same structured envelope with declared_claims plus narration. Do not repeat rejected declarations or their prose realization. Answer again using only established facts, bounded incidental detail, or explicitly qualified NPC belief/hearsay. Do not invent routes, orders, command authorities, physical evidence, rosters, notice history, or movement as world truth. Keep every sentence that already matches the GM resolution decision. Repair only the rejected sentence. AUTHORITATIVE RETRY CONTEXT {\"resolution_contract\": {\"request_kind\": \"inquiry\", \"operation\": \"inspect\", \"target\": \"wooden loom\", \"interlocutor\": null, \"subject\": \"wooden loom\", \"dimension\": null, \"dimensions\": [], \"expected_resolution\": \"answer\", \"authority\": \"unknown_allowed\", \"constraint\": \"Resolve inspect for wooden loom (inspect). The reply must be an answer, a real inability, a refusal, a condition, or a clarification. Do not replace that request with an unrelated scene description. That target is available. Do not deny that it is present.\"}, \"gm_resolution_decision\": {\"contract_id\": \"rc_32e1dbe0f1e0\", \"outcome_classification\": \"established_or_retrieved\", \"proposed_facts\": [{\"text\": \"The wooden loom beam is cracked.\", \"authorized\": true, \"authority\": \"world_truth\", \"provenance\": \"authored_world_fact\", \"epistemic_status\": null, \"relation_kind\": null, \"semantic_identity\": {}}, {\"text\": \"The loom's iron brace is bent.\", \"authorized\": true, \"authority\": \"world_truth\", \"provenance\": \"authored_world_fact\", \"epistemic_status\": null, \"relation_kind\": null, \"semantic_identity\": {}}], \"realization_claims\": [{\"claim_id\": \"rc_9deeeafa5043\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.0\", \"text\": \"The wooden loom beam is cracked.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_49829b26c2ee\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.1\", \"text\": \"The loom's iron brace is bent.\", \"relation_kind\": \"ordinary_predicate\"}], \"narration_constraints\": [\"Narration may not establish consequential world facts absent this decision.\", \"Generated proposals are not world truth unless already grounded or explicitly permitted.\", \"NPC claims remain claims; belief/hearsay/uncertainty does not promote them.\", \"Inference must not be narrated as physical evidence.\", \"Do not narrate authoritative travel/location change unless a location mutation is permitted.\"], \"unresolved_qualifiers\": [], \"answer_relations\": [], \"epistemic_acts\": [{\"act\": \"establish\", \"source_ref\": \"scene.visible_facts.0\", \"authority\": \"world_truth\", \"semantic_identity\": {}}, {\"act\": \"establish\", \"source_ref\": \"scene.visible_facts.1\", \"authority\": \"world_truth\", \"semantic_identity\": {}}], \"permitted_state_mutations\": [], \"executable_obligations\": {\"primary\": null, \"mutation_owner\": null, \"sequence\": [], \"supporting\": []}}, \"accepted_realization_claims\": [{\"claim_id\": \"rc_9deeeafa5043\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.0\", \"text\": \"The wooden loom beam is cracked.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_49829b26c2ee\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.1\", \"text\": \"The loom's iron brace is bent.\", \"relation_kind\": \"ordinary_predicate\"}], \"rejected_declarations\": [], \"validation_failure\": {\"reasons\": [\"unauthorized_resolution_decision_fact\"], \"violations\": [{\"reason_codes\": [\"unsupported_narrator_lead\"], \"text\": \"The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.\"}, {\"reason_codes\": [\"undeclared_causal_agent\", \"undeclared_consequential_claim\"], \"text\": \"The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.\"}]}, \"structured_envelope_schema\": {\"declared_claims\": [{\"declaration_mode\": \"realize|propose\", \"source_claim_id\": \"claim_id_from_gm_resolution_decision or null\", \"text\": \"short internal claim\", \"relation_kind\": \"observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead\", \"modality\": \"established|possible|hypothetical|unresolved\"}], \"narration\": \"player-facing sentence\"}}",
  "temporal_commit": {
    "sealed_text": "The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
    "accepted_claim_count": 0,
    "rejected_discarded_claim_count": 3,
    "bucket_counts": {
      "gm_inferences": 0,
      "player_hypotheses": 0,
      "accepted_incidentals": 0,
      "rejected_consequential": 2
    }
  },
  "before_temporal": null,
  "after_temporal": {
    "version": 1,
    "gm_inferences": [],
    "player_hypotheses": [],
    "accepted_incidentals": [],
    "rejected_consequential": [
      {
        "semantic_identity": {},
        "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
        "authority": "unauthorized",
        "provenance": "generated_proposal",
        "epistemic_status": "unresolved",
        "relation_kind": "gameplay_lead",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "unsupported_narrator_lead"
        ]
      },
      {
        "semantic_identity": {},
        "text": "The wooden loom beam is cracked.",
        "authority": "unauthorized",
        "provenance": "authored_world_fact",
        "epistemic_status": "established",
        "relation_kind": "ordinary_predicate",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "undeclared_consequential_claim"
        ]
      }
    ]
  },
  "before_active_claim": null,
  "after_active_claim": null,
  "exact_sealed": "The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.",
  "exact_emitted": "The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired."
}
```

## A2

Player: So if prolonged strain under heavy stress is what happened to the loom, what would have caused that strain?

### Raw attempt 1

```json
{
  "declared_claims": [
    {
      "declaration_id": "claim_cause_of_loom_strain",
      "declaration_mode": "realize",
      "source_claim_id": null,
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact",
      "epistemic_status": "unresolved",
      "modality": "unresolved",
      "realization_role": "MUST_PRESERVE_UNCERTAINTY",
      "relation_kind": "epistemic_status",
      "text": "The precise cause of the prolonged strain on the wooden loom is unknown"
    },
    {
      "declaration_id": "claim_inspect_loom_for_cause",
      "declaration_mode": "propose",
      "source_claim_id": null,
      "semantic_identity": {},
      "provenance_requested": "npc_claim",
      "epistemic_status": "possible",
      "modality": "possible",
      "realization_role": "MAY_INFER",
      "relation_kind": "gameplay_lead",
      "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain"
    }
  ],
  "narration": "The cracked wooden loom beam and bent iron brace indicate significant structural stress, but the exact cause of this prolonged strain remains unclear. It could stem from repeated heavy use, flawed craftsmanship, or external forces applied over time. To uncover more, you might examine the cracked beam more thoroughly—there could be subtle signs others have missed that hint at what broke the loom's support.",
  "player_facing_text": "The cracked wooden loom beam and bent iron brace indicate significant structural stress, but the exact cause of this prolonged strain remains unclear. It could stem from repeated heavy use, flawed craftsmanship, or external forces applied over time. To uncover more, you might examine the cracked beam more thoroughly—there could be subtle signs others have missed that hint at what broke the loom's support.",
  "tags": ["scene_momentum:new_information"],
  "improvisation_proposals": [
    {
      "kind": "incidental_fact",
      "category": "sensory_detail",
      "content": "The cracked beam emits a faint woody scent mixed with faint dust and old oil, hinting at long-term use and neglect.",
      "scope": "turn",
      "consequence_level": "incidental",
      "source": "dm_improvisation",
      "speaker_id": null,
      "epistemic_status": "known"
    }
  ],
  "scene_update": null,
  "activate_scene_id": null,
  "new_scene_draft": null,
  "world_updates": null,
  "suggested_action": null,
  "debug_notes": "Bounded partial answer maintaining uncertainty about cause, suggesting next investigative lead at the cracked beam."
}
```

### Raw attempt 2

```json
{
  "declared_claims": [
    {
      "declaration_mode": "realize",
      "source_claim_id": "rc_9deeeafa5043",
      "text": "The wooden loom beam is cracked.",
      "relation_kind": "ordinary_predicate",
      "modality": "established"
    },
    {
      "declaration_mode": "realize",
      "source_claim_id": "rc_49829b26c2ee",
      "text": "The loom's iron brace is bent.",
      "relation_kind": "ordinary_predicate",
      "modality": "established"
    },
    {
      "declaration_mode": "realize",
      "source_claim_id": "rc_5aaab7e06e33",
      "text": "The cause of the prolonged strain on the loom remains unresolved.",
      "relation_kind": "epistemic_status",
      "modality": "unresolved"
    }
  ],
  "narration": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
  "player_facing_text": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
  "tags": ["scene_momentum:new_information"],
  "improvisation_proposals": null,
  "scene_update": null,
  "activate_scene_id": null,
  "new_scene_draft": null,
  "world_updates": null,
  "suggested_action": null,
  "debug_notes": "Repaired narration to remove unauthorized inference about cause; maintained all established facts and unresolved status."
}
```

### Exact sealed / emitted

The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.

### Full validation and temporal evidence

```json
{
  "turn": "A2",
  "attempt_1": {
    "text": "The cracked wooden loom beam and bent iron brace indicate significant structural stress, but the exact cause of this prolonged strain remains unclear. It could stem from repeated heavy use, flawed craftsmanship, or external forces applied over time. To uncover more, you might examine the cracked beam more thoroughly—there could be subtle signs others have missed that hint at what broke the loom's support.",
    "reasons": [
      "unauthorized_resolution_decision_fact"
    ],
    "gm_resolution_decision_audit": {
      "decision_id": "rc_6376c3cf69a6",
      "hard_valid": false,
      "declaration_validation": {
        "schema_version": 1,
        "structured_contract_present": true,
        "hard_valid": false,
        "accepted_claims": [],
        "rejected_claims": [
          {
            "declaration_id": "claim_cause_of_loom_strain",
            "declaration_mode": "realize",
            "semantic_identity": {},
            "provenance_requested": "authored_world_fact",
            "epistemic_status": "unresolved",
            "modality": "unresolved",
            "realization_role": "MUST_PRESERVE_UNCERTAINTY",
            "relation_kind": "epistemic_status",
            "source_claim_id": "",
            "text": "The precise cause of the prolonged strain on the wooden loom is unknown",
            "authorized": false,
            "authority": "unauthorized",
            "reason_codes": [
              "unauthorized_declared_claim"
            ]
          },
          {
            "declaration_id": "claim_inspect_loom_for_cause",
            "declaration_mode": "propose",
            "semantic_identity": {},
            "provenance_requested": "npc_claim",
            "epistemic_status": "possible",
            "modality": "possible",
            "realization_role": "MAY_INFER",
            "relation_kind": "gameplay_lead",
            "source_claim_id": "",
            "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain",
            "authorized": false,
            "authority": "unauthorized",
            "reason_codes": [
              "proposal_inference_not_permitted"
            ]
          }
        ],
        "violations": [
          {
            "declaration_id": "claim_cause_of_loom_strain",
            "declaration_mode": "realize",
            "semantic_identity": {},
            "provenance_requested": "authored_world_fact",
            "epistemic_status": "unresolved",
            "modality": "unresolved",
            "realization_role": "MUST_PRESERVE_UNCERTAINTY",
            "relation_kind": "epistemic_status",
            "source_claim_id": "",
            "text": "The precise cause of the prolonged strain on the wooden loom is unknown",
            "authorized": false,
            "authority": "unauthorized",
            "reason_codes": [
              "unauthorized_declared_claim"
            ]
          },
          {
            "declaration_id": "claim_inspect_loom_for_cause",
            "declaration_mode": "propose",
            "semantic_identity": {},
            "provenance_requested": "npc_claim",
            "epistemic_status": "possible",
            "modality": "possible",
            "realization_role": "MAY_INFER",
            "relation_kind": "gameplay_lead",
            "source_claim_id": "",
            "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain",
            "authorized": false,
            "authority": "unauthorized",
            "reason_codes": [
              "proposal_inference_not_permitted"
            ]
          }
        ]
      },
      "narration_validation": null,
      "violations": [
        {
          "declaration_id": "claim_cause_of_loom_strain",
          "declaration_mode": "realize",
          "semantic_identity": {},
          "provenance_requested": "authored_world_fact",
          "epistemic_status": "unresolved",
          "modality": "unresolved",
          "realization_role": "MUST_PRESERVE_UNCERTAINTY",
          "relation_kind": "epistemic_status",
          "source_claim_id": "",
          "text": "The precise cause of the prolonged strain on the wooden loom is unknown",
          "authorized": false,
          "authority": "unauthorized",
          "reason_codes": [
            "unauthorized_declared_claim"
          ]
        },
        {
          "declaration_id": "claim_inspect_loom_for_cause",
          "declaration_mode": "propose",
          "semantic_identity": {},
          "provenance_requested": "npc_claim",
          "epistemic_status": "possible",
          "modality": "possible",
          "realization_role": "MAY_INFER",
          "relation_kind": "gameplay_lead",
          "source_claim_id": "",
          "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain",
          "authorized": false,
          "authority": "unauthorized",
          "reason_codes": [
            "proposal_inference_not_permitted"
          ]
        }
      ],
      "claim_results": [
        {
          "declaration_id": "claim_cause_of_loom_strain",
          "declaration_mode": "realize",
          "semantic_identity": {},
          "provenance_requested": "authored_world_fact",
          "epistemic_status": "unresolved",
          "modality": "unresolved",
          "realization_role": "MUST_PRESERVE_UNCERTAINTY",
          "relation_kind": "epistemic_status",
          "source_claim_id": "",
          "text": "The precise cause of the prolonged strain on the wooden loom is unknown",
          "authorized": false,
          "authority": "unauthorized",
          "reason_codes": [
            "unauthorized_declared_claim"
          ]
        },
        {
          "declaration_id": "claim_inspect_loom_for_cause",
          "declaration_mode": "propose",
          "semantic_identity": {},
          "provenance_requested": "npc_claim",
          "epistemic_status": "possible",
          "modality": "possible",
          "realization_role": "MAY_INFER",
          "relation_kind": "gameplay_lead",
          "source_claim_id": "",
          "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain",
          "authorized": false,
          "authority": "unauthorized",
          "reason_codes": [
            "proposal_inference_not_permitted"
          ]
        }
      ],
      "accepted_realized_claims": []
    }
  },
  "attempt_2": {
    "text": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
    "reasons": [],
    "gm_resolution_decision_audit": {
      "decision_id": "rc_6376c3cf69a6",
      "hard_valid": true,
      "declaration_validation": {
        "schema_version": 1,
        "structured_contract_present": true,
        "hard_valid": true,
        "accepted_claims": [
          {
            "text": "The wooden loom beam is cracked.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.0",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The loom's iron brace is bent.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.1",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The cause of the prolonged strain on the loom remains unresolved.",
            "semantic_identity": {
              "relation_kind": "epistemic_status",
              "epistemic_status": "unresolved",
              "unresolved_qualifiers": [
                "cause"
              ],
              "scope": "unresolved_qualifiers"
            },
            "provenance": "speculation",
            "authority": "observation",
            "epistemic_status": "unresolved",
            "relation_kind": "epistemic_status",
            "persistence": "do_not_persist",
            "authorized": true,
            "source_ref": "decision.epistemic_acts",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          }
        ],
        "rejected_claims": [],
        "violations": []
      },
      "narration_validation": {
        "decision_id": "rc_6376c3cf69a6",
        "hard_valid": true,
        "violations": [],
        "proposed_facts": [],
        "claim_results": []
      },
      "violations": [],
      "proposed_facts": [],
      "claim_results": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The loom's iron brace is bent.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.1",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The cause of the prolonged strain on the loom remains unresolved.",
          "semantic_identity": {
            "relation_kind": "epistemic_status",
            "epistemic_status": "unresolved",
            "unresolved_qualifiers": [
              "cause"
            ],
            "scope": "unresolved_qualifiers"
          },
          "provenance": "speculation",
          "authority": "observation",
          "epistemic_status": "unresolved",
          "relation_kind": "epistemic_status",
          "persistence": "do_not_persist",
          "authorized": true,
          "source_ref": "decision.epistemic_acts",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        }
      ],
      "accepted_realized_claims": [
        {
          "text": "The wooden loom beam is cracked.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.0",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The loom's iron brace is bent.",
          "semantic_identity": {},
          "provenance": "authored_world_fact",
          "authority": "world_truth",
          "epistemic_status": "established",
          "relation_kind": "ordinary_predicate",
          "persistence": "world_truth",
          "authorized": true,
          "source_ref": "scene.visible_facts.1",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        },
        {
          "text": "The cause of the prolonged strain on the loom remains unresolved.",
          "semantic_identity": {
            "relation_kind": "epistemic_status",
            "epistemic_status": "unresolved",
            "unresolved_qualifiers": [
              "cause"
            ],
            "scope": "unresolved_qualifiers"
          },
          "provenance": "speculation",
          "authority": "observation",
          "epistemic_status": "unresolved",
          "relation_kind": "epistemic_status",
          "persistence": "do_not_persist",
          "authorized": true,
          "source_ref": "decision.epistemic_acts",
          "source_turn": null,
          "source_scene": "",
          "reason_codes": [
            "accepted_declared_realization"
          ]
        }
      ]
    }
  },
  "accepted": {
    "immutable": true,
    "text": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
    "provenance": "regeneration",
    "attempt": 2,
    "player_input": "So if prolonged strain under heavy stress is what happened to the loom, what would have caused that strain?",
    "turn_identity": "rc_6376c3cf69a6",
    "speaker": "",
    "addressee": "",
    "target": "wooden loom",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [],
      "gm_resolution_decision_audit": {
        "decision_id": "rc_6376c3cf69a6",
        "hard_valid": true,
        "declaration_validation": {
          "schema_version": 1,
          "structured_contract_present": true,
          "hard_valid": true,
          "accepted_claims": [
            {
              "text": "The wooden loom beam is cracked.",
              "semantic_identity": {},
              "provenance": "authored_world_fact",
              "authority": "world_truth",
              "epistemic_status": "established",
              "relation_kind": "ordinary_predicate",
              "persistence": "world_truth",
              "authorized": true,
              "source_ref": "scene.visible_facts.0",
              "source_turn": null,
              "source_scene": "",
              "reason_codes": [
                "accepted_declared_realization"
              ]
            },
            {
              "text": "The loom's iron brace is bent.",
              "semantic_identity": {},
              "provenance": "authored_world_fact",
              "authority": "world_truth",
              "epistemic_status": "established",
              "relation_kind": "ordinary_predicate",
              "persistence": "world_truth",
              "authorized": true,
              "source_ref": "scene.visible_facts.1",
              "source_turn": null,
              "source_scene": "",
              "reason_codes": [
                "accepted_declared_realization"
              ]
            },
            {
              "text": "The cause of the prolonged strain on the loom remains unresolved.",
              "semantic_identity": {
                "relation_kind": "epistemic_status",
                "epistemic_status": "unresolved",
                "unresolved_qualifiers": [
                  "cause"
                ],
                "scope": "unresolved_qualifiers"
              },
              "provenance": "speculation",
              "authority": "observation",
              "epistemic_status": "unresolved",
              "relation_kind": "epistemic_status",
              "persistence": "do_not_persist",
              "authorized": true,
              "source_ref": "decision.epistemic_acts",
              "source_turn": null,
              "source_scene": "",
              "reason_codes": [
                "accepted_declared_realization"
              ]
            }
          ],
          "rejected_claims": [],
          "violations": []
        },
        "narration_validation": {
          "decision_id": "rc_6376c3cf69a6",
          "hard_valid": true,
          "violations": [],
          "proposed_facts": [],
          "claim_results": []
        },
        "violations": [],
        "proposed_facts": [],
        "claim_results": [
          {
            "text": "The wooden loom beam is cracked.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.0",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The loom's iron brace is bent.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.1",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The cause of the prolonged strain on the loom remains unresolved.",
            "semantic_identity": {
              "relation_kind": "epistemic_status",
              "epistemic_status": "unresolved",
              "unresolved_qualifiers": [
                "cause"
              ],
              "scope": "unresolved_qualifiers"
            },
            "provenance": "speculation",
            "authority": "observation",
            "epistemic_status": "unresolved",
            "relation_kind": "epistemic_status",
            "persistence": "do_not_persist",
            "authorized": true,
            "source_ref": "decision.epistemic_acts",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          }
        ],
        "accepted_realized_claims": [
          {
            "text": "The wooden loom beam is cracked.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.0",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The loom's iron brace is bent.",
            "semantic_identity": {},
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "persistence": "world_truth",
            "authorized": true,
            "source_ref": "scene.visible_facts.1",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          },
          {
            "text": "The cause of the prolonged strain on the loom remains unresolved.",
            "semantic_identity": {
              "relation_kind": "epistemic_status",
              "epistemic_status": "unresolved",
              "unresolved_qualifiers": [
                "cause"
              ],
              "scope": "unresolved_qualifiers"
            },
            "provenance": "speculation",
            "authority": "observation",
            "epistemic_status": "unresolved",
            "relation_kind": "epistemic_status",
            "persistence": "do_not_persist",
            "authorized": true,
            "source_ref": "decision.epistemic_acts",
            "source_turn": null,
            "source_scene": "",
            "reason_codes": [
              "accepted_declared_realization"
            ]
          }
        ]
      },
      "decision_acceptance_why": "regeneration_hard_valid"
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_6376c3cf69a6",
      "operation": "ask",
      "interlocutor_id": "",
      "expected_resolution": "answer"
    },
    "resolution_kind": "",
    "generation_attempts": 2,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_repeated_description_guard",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ]
  },
  "retry_context": "The previous attempt was rejected for: unauthorized_resolution_decision_fact. It narrated consequential world facts that were not authorized by the pre-narration GM resolution decision. Answer again as the same structured envelope with declared_claims plus narration. Do not repeat rejected declarations or their prose realization. Answer again using only established facts, bounded incidental detail, or explicitly qualified NPC belief/hearsay. Do not invent routes, orders, command authorities, physical evidence, rosters, notice history, or movement as world truth. Keep every sentence that already matches the GM resolution decision. Repair only the rejected sentence. AUTHORITATIVE RETRY CONTEXT {\"resolution_contract\": {\"request_kind\": \"inquiry\", \"operation\": \"ask\", \"target\": \"wooden loom\", \"interlocutor\": null, \"subject\": \"wooden loom\", \"dimension\": null, \"dimensions\": [], \"expected_resolution\": \"answer\", \"authority\": \"unknown_allowed\", \"constraint\": \"Resolve ask for wooden loom (ask). The reply must be an answer, a real inability, a refusal, a condition, or a clarification. Do not replace that request with an unrelated scene description. That target is available. Do not deny that it is present.\"}, \"gm_resolution_decision\": {\"contract_id\": \"rc_6376c3cf69a6\", \"outcome_classification\": \"established_or_retrieved\", \"proposed_facts\": [{\"text\": \"The wooden loom beam is cracked.\", \"authorized\": true, \"authority\": \"world_truth\", \"provenance\": \"authored_world_fact\", \"epistemic_status\": null, \"relation_kind\": null, \"semantic_identity\": {}}, {\"text\": \"The loom's iron brace is bent.\", \"authorized\": true, \"authority\": \"world_truth\", \"provenance\": \"authored_world_fact\", \"epistemic_status\": null, \"relation_kind\": null, \"semantic_identity\": {}}], \"realization_claims\": [{\"claim_id\": \"rc_9deeeafa5043\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.0\", \"text\": \"The wooden loom beam is cracked.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_49829b26c2ee\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.1\", \"text\": \"The loom's iron brace is bent.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_5aaab7e06e33\", \"semantic_identity\": {\"relation_kind\": \"epistemic_status\", \"epistemic_status\": \"unresolved\", \"unresolved_qualifiers\": [\"cause\"], \"scope\": \"unresolved_qualifiers\"}, \"provenance\": \"speculation\", \"authority\": \"observation\", \"epistemic_status\": \"unresolved\", \"modality\": \"unresolved\", \"realization_role\": \"MUST_PRESERVE_UNCERTAINTY\", \"persistence\": \"do_not_persist\", \"source_ref\": \"decision.epistemic_acts\", \"text\": \"Unresolved consequential slot\", \"relation_kind\": \"epistemic_status\"}], \"narration_constraints\": [\"Narration may not establish consequential world facts absent this decision.\", \"Generated proposals are not world truth unless already grounded or explicitly permitted.\", \"NPC claims remain claims; belief/hearsay/uncertainty does not promote them.\", \"Inference must not be narrated as physical evidence.\", \"Do not narrate authoritative travel/location change unless a location mutation is permitted.\", \"Cause, actor, and time may be called unknown. That does not deny an established condition.\"], \"unresolved_qualifiers\": [\"cause\"], \"answer_relations\": [], \"epistemic_acts\": [{\"act\": \"establish\", \"source_ref\": \"scene.visible_facts.0\", \"authority\": \"world_truth\", \"semantic_identity\": {}}, {\"act\": \"establish\", \"source_ref\": \"scene.visible_facts.1\", \"authority\": \"world_truth\", \"semantic_identity\": {}}, {\"act\": \"leave_unresolved\", \"authority\": \"observation\", \"semantic_identity\": {\"relation_kind\": \"epistemic_status\", \"epistemic_status\": \"unresolved\", \"unresolved_qualifiers\": [\"cause\"], \"scope\": \"unresolved_qualifiers\"}}], \"permitted_state_mutations\": [], \"executable_obligations\": {\"primary\": null, \"mutation_owner\": null, \"sequence\": [], \"supporting\": []}}, \"accepted_realization_claims\": [{\"claim_id\": \"rc_9deeeafa5043\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.0\", \"text\": \"The wooden loom beam is cracked.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_49829b26c2ee\", \"semantic_identity\": {}, \"provenance\": \"authored_world_fact\", \"authority\": \"world_truth\", \"epistemic_status\": \"established\", \"modality\": \"\", \"realization_role\": \"MUST_STATE\", \"persistence\": \"world_truth\", \"source_ref\": \"scene.visible_facts.1\", \"text\": \"The loom's iron brace is bent.\", \"relation_kind\": \"ordinary_predicate\"}, {\"claim_id\": \"rc_5aaab7e06e33\", \"semantic_identity\": {\"relation_kind\": \"epistemic_status\", \"epistemic_status\": \"unresolved\", \"unresolved_qualifiers\": [\"cause\"], \"scope\": \"unresolved_qualifiers\"}, \"provenance\": \"speculation\", \"authority\": \"observation\", \"epistemic_status\": \"unresolved\", \"modality\": \"unresolved\", \"realization_role\": \"MUST_PRESERVE_UNCERTAINTY\", \"persistence\": \"do_not_persist\", \"source_ref\": \"decision.epistemic_acts\", \"text\": \"Unresolved consequential slot\", \"relation_kind\": \"epistemic_status\"}], \"rejected_declarations\": [{\"text\": \"The precise cause of the prolonged strain on the wooden loom is unknown\", \"reason_codes\": [\"unauthorized_declared_claim\"], \"declaration_mode\": \"realize\"}, {\"text\": \"Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain\", \"reason_codes\": [\"proposal_inference_not_permitted\"], \"declaration_mode\": \"propose\"}], \"validation_failure\": {\"reasons\": [\"unauthorized_resolution_decision_fact\"], \"violations\": [{\"reason_codes\": [\"unauthorized_declared_claim\"], \"text\": \"The precise cause of the prolonged strain on the wooden loom is unknown\"}, {\"reason_codes\": [\"proposal_inference_not_permitted\"], \"text\": \"Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain\"}]}, \"structured_envelope_schema\": {\"declared_claims\": [{\"declaration_mode\": \"realize|propose\", \"source_claim_id\": \"claim_id_from_gm_resolution_decision or null\", \"text\": \"short internal claim\", \"relation_kind\": \"observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead\", \"modality\": \"established|possible|hypothetical|unresolved\"}], \"narration\": \"player-facing sentence\"}}",
  "temporal_commit": {
    "sealed_text": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
    "accepted_claim_count": 4,
    "rejected_discarded_claim_count": 2,
    "bucket_counts": {
      "gm_inferences": 0,
      "player_hypotheses": 1,
      "accepted_incidentals": 0,
      "rejected_consequential": 4
    }
  },
  "before_temporal": {
    "version": 1,
    "gm_inferences": [],
    "player_hypotheses": [],
    "accepted_incidentals": [],
    "rejected_consequential": [
      {
        "semantic_identity": {},
        "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
        "authority": "unauthorized",
        "provenance": "generated_proposal",
        "epistemic_status": "unresolved",
        "relation_kind": "gameplay_lead",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "unsupported_narrator_lead"
        ]
      },
      {
        "semantic_identity": {},
        "text": "The wooden loom beam is cracked.",
        "authority": "unauthorized",
        "provenance": "authored_world_fact",
        "epistemic_status": "established",
        "relation_kind": "ordinary_predicate",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "undeclared_consequential_claim"
        ]
      }
    ]
  },
  "after_temporal": {
    "version": 1,
    "gm_inferences": [],
    "player_hypotheses": [
      {
        "semantic_identity": {
          "relation_kind": "epistemic_status",
          "epistemic_status": "hypothesis"
        },
        "text": "So if prolonged strain under heavy stress is what happened to the loom, what would have caused that strain?",
        "authority": "observation",
        "provenance": "player_hypothesis",
        "epistemic_status": "hypothesis",
        "relation_kind": "epistemic_status",
        "scene_id": "loom_workshop",
        "source_turn": 3
      }
    ],
    "accepted_incidentals": [],
    "rejected_consequential": [
      {
        "semantic_identity": {},
        "text": "The wooden beam of the loom is deeply cracked, a clear sign of structural weakness that could compromise the loom's function or safety.",
        "authority": "unauthorized",
        "provenance": "generated_proposal",
        "epistemic_status": "unresolved",
        "relation_kind": "gameplay_lead",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "unsupported_narrator_lead"
        ]
      },
      {
        "semantic_identity": {},
        "text": "The wooden loom beam is cracked.",
        "authority": "unauthorized",
        "provenance": "authored_world_fact",
        "epistemic_status": "established",
        "relation_kind": "ordinary_predicate",
        "scene_id": "loom_workshop",
        "source_turn": 2,
        "reason_codes": [
          "undeclared_consequential_claim"
        ]
      },
      {
        "semantic_identity": {},
        "text": "The precise cause of the prolonged strain on the wooden loom is unknown",
        "authority": "unauthorized",
        "provenance": "",
        "epistemic_status": "unresolved",
        "relation_kind": "epistemic_status",
        "scene_id": "loom_workshop",
        "source_turn": 3,
        "reason_codes": [
          "unauthorized_declared_claim"
        ]
      },
      {
        "semantic_identity": {},
        "text": "Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain",
        "authority": "unauthorized",
        "provenance": "",
        "epistemic_status": "possible",
        "relation_kind": "gameplay_lead",
        "scene_id": "loom_workshop",
        "source_turn": 3,
        "reason_codes": [
          "proposal_inference_not_permitted"
        ]
      }
    ]
  },
  "before_active_claim": null,
  "after_active_claim": {
    "id": "claim_8e06a38c88",
    "label": "So if prolonged strain under heavy stress is what happened to the loom, what would have caused that strain?",
    "kind": "claim",
    "scene_id": "loom_workshop",
    "turn_index": 3,
    "source": "player_hypothesis",
    "epistemic_status": "hypothesis"
  },
  "exact_sealed": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.",
  "exact_emitted": "The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here."
}
```
