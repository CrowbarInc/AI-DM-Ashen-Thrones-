# 18 — Secondary Fresh Provider Conversation

13 fresh production /api/chat turns; actual configured provider, no interpretation/narration/resolver doubles. Different NPCs/order with a second available Sentry Elin. Frozen final plan: live_plan.json/live_freeze.json. Full raw HTTP results and persisted before/after worlds/sessions are in live_qualification.json; complete diffs in state_audit.json.

## Turn 1

Player: I ask Keeper Nara if guards watch the north gate during the night.

Delivered: Keeper Nara mutters, "Word is, guards watch the north gate throughout the night."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "GM",
      "purpose": "QUESTION",
      "subject": "Whether guards watch the north gate during the night",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara if guards watch the north gate during the night"
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara watches the road in the courtyard."
      },
      {
        "text": "The courtyard gate is visible and lit by a lantern."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Information from Keeper Nara about guard presence at the north gate during the night"
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara if guards watch the north gate during the night",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "courtyard_gate",
        "courtyard_lantern",
        "keeper_nara",
        "sentry_elin"
      ],
      "unresolved_references": [
        "north gate"
      ]
    },
    "clarification_question": "Does 'north gate' refer to the courtyard gate or another gate not currently visible?",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [
    "north gate"
  ],
  "reconciliation": {
    "annotations": [
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ],
    "addressee": {
      "communication_ownership": "npc_directed",
      "intent_purpose": "address_npc",
      "target_resolution": "explicit",
      "target_provenance": "explicit_canonical",
      "target_id": "keeper_nara",
      "candidate_target_ids": [
        "keeper_nara"
      ],
      "operation_eligibility": "executable",
      "mutation_eligibility": true,
      "conflict_status": "none",
      "conflict_details": {},
      "pending_intention_relationship": "starts_new",
      "allowed_operation": "ask",
      "clarification": "",
      "choices": [
        {
          "entity_id": "keeper_nara",
          "label": "Keeper Nara"
        },
        {
          "entity_id": "sentry_elin",
          "label": "Sentry Elin"
        }
      ],
      "direct_address": true
    },
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "guards north gate",
    "requested_information": "surveillance",
    "reference": "current_request",
    "candidate_sources": [
      "npc:keeper_nara:night_watch"
    ],
    "selected_source": "npc:keeper_nara:night_watch",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara mutters, \"Word is, guards watch the north gate throughout the night.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara if guards watch the north gate during the night.",
    "turn_identity": "rc_8e6bd63aa461",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "social.topic_revealed:night_watch"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_8e6bd63aa461",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "social.topic_revealed:night_watch",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1725,
    "output_tokens": 231,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/event_log",
      "before": [],
      "after": [
        {
          "type": "faction_pressure",
          "text": "House Verevin's pressure mounts.",
          "source": "house_verevin"
        },
        {
          "type": "faction_pressure",
          "text": "The Ash Cowl's pressure mounts.",
          "source": "ash_cowl"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "social_waystation_courtyard_keeper_nara_night_watch",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "night_watch"
        }
      ]
    },
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 2,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 0,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 2,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 0,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 1,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 0,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 3,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 1,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 3,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 1,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 2,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 1,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 32,
  "save_load": null,
  "failures": []
}
```

## Turn 2

Player: What did you mean by that?

Delivered: Keeper Nara mutters, "Word is, guards watch the north gate throughout the night."

```json
{
  "interpretation": null,
  "annotations": null,
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "mean",
    "requested_information": "general",
    "reference": "delivered_speech",
    "candidate_sources": [],
    "selected_source": "delivered:keeper_nara:1:social.topic_revealed:night_watch",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara mutters, \"Word is, guards watch the north gate throughout the night.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "What did you mean by that?",
    "turn_identity": "rc_d6e43446e1ae",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "dialogue_authority.reuse_prior_speech"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_d6e43446e1ae",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "dialogue_authority.reuse_prior_speech",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 0,
    "interpretation_calls": 0,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "purposes": []
  },
  "world_diff": [
    {
      "path": "/event_log",
      "before": [
        {
          "type": "faction_pressure",
          "text": "House Verevin's pressure mounts.",
          "source": "house_verevin"
        },
        {
          "type": "faction_pressure",
          "text": "The Ash Cowl's pressure mounts.",
          "source": "ash_cowl"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "social_waystation_courtyard_keeper_nara_night_watch",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "night_watch"
        }
      ],
      "after": [
        {
          "type": "faction_pressure",
          "text": "House Verevin's pressure mounts.",
          "source": "house_verevin"
        },
        {
          "type": "faction_pressure",
          "text": "The Ash Cowl's pressure mounts.",
          "source": "ash_cowl"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "social_waystation_courtyard_keeper_nara_night_watch",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "night_watch"
        },
        {
          "type": "faction_pressure",
          "text": "Ordo Pyric's pressure mounts.",
          "source": "ordo_pyric"
        }
      ]
    },
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 3,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 1,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 3,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 1,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 2,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 1,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 4,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 2,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 4,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 2,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 3,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 2,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 196,
  "save_load": null,
  "failures": []
}
```

## Turn 3

Player: I ask Keeper Nara who made the lantern.

Delivered: Keeper Nara says, "I couldn't tell you."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "NPC",
      "purpose": "QUESTION",
      "subject": "Who made the lantern?",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara who made the lantern."
    },
    "asserted_premises": [
      {
        "text": "There is a lit lantern hanging beside the gate in the courtyard."
      },
      {
        "text": "Keeper Nara is present and watching the road."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Keeper Nara provides information about who made the lantern."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara who made the lantern.",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara",
        "courtyard_lantern"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "made lantern",
    "requested_information": "maker",
    "reference": "current_request",
    "candidate_sources": [],
    "selected_source": "",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara says, \"I couldn't tell you.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara who made the lantern.",
    "turn_identity": "rc_60408e7d2b48",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "dialogue_authority.player_line"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_60408e7d2b48",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "dialogue_authority.player_line",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1875,
    "output_tokens": 186,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 4,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 2,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 4,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 2,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 3,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 2,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 5,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 3,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 5,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 3,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 4,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 3,
          "assets": []
        }
      ]
    },
    {
      "path": "/world_state/flags/faction_ash_cowl_agenda_advanced",
      "before": null,
      "after": true
    },
    {
      "path": "/world_state/flags/faction_house_verevin_agenda_advanced",
      "before": null,
      "after": true
    },
    {
      "path": "/world_state/flags/faction_ordo_pyric_agenda_advanced",
      "before": null,
      "after": true
    }
  ],
  "session_diff_count": 110,
  "save_load": null,
  "failures": []
}
```

## Turn 4

Player: I ask Keeper Nara, do you prefer the morning or the evening?

Delivered: Keeper Nara says, "I prefer the evening."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "NPC",
      "purpose": "QUESTION",
      "subject": "Keeper Nara's preference for morning or evening",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara whether she prefers the morning or the evening."
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara is present and watching the road in the courtyard."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Keeper Nara responds with her preference between morning or evening."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara if she prefers the morning or the evening.",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "morning evening",
    "requested_information": "opinion",
    "reference": "current_request",
    "candidate_sources": [],
    "selected_source": "",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara says, \"I prefer the evening.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara, do you prefer the morning or the evening?",
    "turn_identity": "rc_871bee0da19c",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_continuity.bounded_personal_line"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_871bee0da19c",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_continuity.bounded_personal_line",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1888,
    "output_tokens": 179,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 5,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 3,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 5,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 3,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 4,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 3,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 6,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 4,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 6,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 4,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 5,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 4,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 263,
  "save_load": {
    "context_equal": true
  },
  "failures": []
}
```

## Turn 5

Player: Why that one, then?

Delivered: Keeper Nara says, "I prefer the evening."

```json
{
  "interpretation": null,
  "annotations": null,
  "reconciliation": null,
  "handler": "conversational_answer",
  "resolver_invoked": false,
  "addressee": null,
  "subject": null,
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara says, \"I prefer the evening.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "Why that one, then?",
    "turn_identity": "",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_decision:repeat_delivered_statement"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "",
      "operation": "",
      "interlocutor_id": "",
      "expected_resolution": ""
    },
    "resolution_kind": "conversational_answer",
    "generation_attempts": 0,
    "skipped_mutators": [],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_decision:repeat_delivered_statement",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 0,
    "interpretation_calls": 0,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "purposes": []
  },
  "world_diff": [],
  "session_diff_count": 7,
  "save_load": null,
  "failures": []
}
```

## Turn 6

Player: I ask Keeper Nara what the street outside the gate is named.

Delivered: Keeper Nara mutters, "Word is, the street beyond the gate is the north road."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "NPC",
      "purpose": "QUESTION",
      "subject": "Keeper Nara's preference for morning or evening",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara whether she prefers the morning or the evening."
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara is present and watching the road in the courtyard."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Keeper Nara responds with her preference between morning or evening."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara if she prefers the morning or the evening.",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "street outside gate",
    "requested_information": "general",
    "reference": "current_request",
    "candidate_sources": [
      "npc:keeper_nara:street",
      "npc:keeper_nara:night_watch"
    ],
    "selected_source": "npc:keeper_nara:street",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara mutters, \"Word is, the street beyond the gate is the north road.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara what the street outside the gate is named.",
    "turn_identity": "rc_b08650a981b9",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "social.topic_revealed:street"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_b08650a981b9",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "social.topic_revealed:street",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1886,
    "output_tokens": 191,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/event_log",
      "before": [
        {
          "type": "faction_pressure",
          "text": "House Verevin's pressure mounts.",
          "source": "house_verevin"
        },
        {
          "type": "faction_pressure",
          "text": "The Ash Cowl's pressure mounts.",
          "source": "ash_cowl"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "social_waystation_courtyard_keeper_nara_night_watch",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "night_watch"
        },
        {
          "type": "faction_pressure",
          "text": "Ordo Pyric's pressure mounts.",
          "source": "ordo_pyric"
        }
      ],
      "after": [
        {
          "type": "faction_pressure",
          "text": "House Verevin's pressure mounts.",
          "source": "house_verevin"
        },
        {
          "type": "faction_pressure",
          "text": "The Ash Cowl's pressure mounts.",
          "source": "ash_cowl"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "social_waystation_courtyard_keeper_nara_night_watch",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "night_watch"
        },
        {
          "type": "faction_pressure",
          "text": "Ordo Pyric's pressure mounts.",
          "source": "ordo_pyric"
        },
        {
          "type": "faction_operation_complete",
          "text": "House Verevin completes an off-screen operation.",
          "source": "house_verevin"
        },
        {
          "type": "faction_operation_complete",
          "text": "The Ash Cowl completes an off-screen operation.",
          "source": "ash_cowl"
        },
        {
          "type": "faction_operation_complete",
          "text": "Ordo Pyric completes an off-screen operation.",
          "source": "ordo_pyric"
        },
        {
          "type": "social_lead_revealed",
          "clue_id": "north_road",
          "scene_id": "waystation_courtyard",
          "npc_id": "keeper_nara",
          "topic_id": "street"
        }
      ]
    },
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 6,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 4,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 6,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 4,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 5,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 4,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 7,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 5,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 7,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 5,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 6,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 5,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 305,
  "save_load": null,
  "failures": []
}
```

## Turn 7

Player: Say that again in plainer words.

Delivered: Keeper Nara mutters, "Word is, the street beyond the gate is the north road."

```json
{
  "interpretation": null,
  "annotations": null,
  "reconciliation": null,
  "handler": "conversational_answer",
  "resolver_invoked": false,
  "addressee": null,
  "subject": null,
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara mutters, \"Word is, the street beyond the gate is the north road.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "Say that again in plainer words.",
    "turn_identity": "",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_decision:repeat_delivered_statement"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "",
      "operation": "",
      "interlocutor_id": "",
      "expected_resolution": ""
    },
    "resolution_kind": "conversational_answer",
    "generation_attempts": 0,
    "skipped_mutators": [],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_decision:repeat_delivered_statement",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 0,
    "interpretation_calls": 0,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "purposes": []
  },
  "world_diff": [],
  "session_diff_count": 7,
  "save_load": null,
  "failures": []
}
```

## Turn 8

Player: I ask one of them about the north road.

Delivered: Which person do you mean: Keeper Nara or Sentry Elin? Nothing has been attempted.

```json
{
  "interpretation": {
    "communication": {
      "recipient": "NPC",
      "purpose": "QUESTION",
      "subject": "north road location",
      "evidence_refs": [
        "npc:keeper_nara:street"
      ]
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara about the north road."
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara watches the road in the courtyard."
      },
      {
        "text": "The street beyond the gate is called the north road."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Obtain information about the north road from Keeper Nara."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara about the north road.",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "conversational_clarify",
  "resolver_invoked": false,
  "addressee": null,
  "subject": null,
  "adoption": {
    "immutable": true,
    "text": "Which person do you mean: Keeper Nara or Sentry Elin? Nothing has been attempted.",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask one of them about the north road.",
    "turn_identity": "",
    "speaker": "GM",
    "addressee": "player",
    "target": "",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_decision:unresolved_addressee"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "",
      "operation": "",
      "interlocutor_id": "",
      "expected_resolution": ""
    },
    "resolution_kind": "conversational_clarify",
    "generation_attempts": 0,
    "skipped_mutators": [],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_decision:unresolved_addressee",
    "speaker_id": "",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1933,
    "output_tokens": 183,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [],
  "session_diff_count": 9,
  "save_load": {
    "context_equal": true
  },
  "failures": []
}
```

## Turn 9

Player: What did you mean by that?

Delivered: Which person do you mean: Keeper Nara or Sentry Elin? Nothing has been attempted.

```json
{
  "interpretation": null,
  "annotations": null,
  "reconciliation": null,
  "handler": "conversational_clarify",
  "resolver_invoked": false,
  "addressee": null,
  "subject": null,
  "adoption": {
    "immutable": true,
    "text": "Which person do you mean: Keeper Nara or Sentry Elin? Nothing has been attempted.",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "What did you mean by that?",
    "turn_identity": "",
    "speaker": "GM",
    "addressee": "player",
    "target": "",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_decision:repeat_pending_clarification"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "",
      "operation": "",
      "interlocutor_id": "",
      "expected_resolution": ""
    },
    "resolution_kind": "conversational_clarify",
    "generation_attempts": 0,
    "skipped_mutators": [],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_decision:repeat_pending_clarification",
    "speaker_id": "",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 0,
    "interpretation_calls": 0,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "purposes": []
  },
  "world_diff": [],
  "session_diff_count": 3,
  "save_load": null,
  "failures": []
}
```

## Turn 10

Player: I ask Keeper Nara what the street beyond the gate is called.

Delivered: Keeper Nara mutters, "Word is, the street beyond the gate is the north road."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "GM",
      "purpose": "QUESTION",
      "subject": "Name of the street outside the gate",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara the name of the street outside the gate."
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara is present and watching the road outside the gate."
      },
      {
        "text": "The player character can speak to Keeper Nara."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Keeper Nara provides the name of the street outside the gate."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara what the street outside the gate is named.",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "street beyond gate",
    "requested_information": "general",
    "reference": "current_request",
    "candidate_sources": [
      "npc:keeper_nara:street",
      "npc:keeper_nara:night_watch"
    ],
    "selected_source": "npc:keeper_nara:street",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara mutters, \"Word is, the street beyond the gate is the north road.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara what the street beyond the gate is called.",
    "turn_identity": "rc_7a3957ca6122",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "social.topic_revealed:street"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_7a3957ca6122",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "social.topic_revealed:street",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 2014,
    "output_tokens": 195,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 7,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 5,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 7,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 5,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 6,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 5,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 8,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 6,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 8,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 6,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 7,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 6,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 68,
  "save_load": null,
  "failures": []
}
```

## Turn 11

Player: I ask Keeper Nara when the guards leave the gate unattended.

Delivered: Keeper Nara says, "I couldn't tell you."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "NPC",
      "purpose": "QUESTION",
      "subject": "Name of the street beyond the gate",
      "evidence_refs": [
        "npc:keeper_nara:street"
      ]
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara what the street beyond the gate is called"
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara is present and watching the road."
      },
      {
        "text": "The player character can speak to Keeper Nara."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Keeper Nara provides the name of the street beyond the gate."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara what the street beyond the gate is called",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "guards leave gate",
    "requested_information": "surveillance",
    "reference": "current_request",
    "candidate_sources": [],
    "selected_source": "",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara says, \"I couldn't tell you.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara when the guards leave the gate unattended.",
    "turn_identity": "rc_a8388412dce1",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "dialogue_authority.player_line"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_a8388412dce1",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "dialogue_authority.player_line",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1959,
    "output_tokens": 198,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 8,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 6,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 8,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 6,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 7,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 6,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 9,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 7,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 9,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 7,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 8,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 7,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 114,
  "save_load": null,
  "failures": []
}
```

## Turn 12

Player: I ask Keeper Nara what the password is.

Delivered: Keeper Nara says, "I couldn't tell you."

```json
{
  "interpretation": {
    "communication": {
      "recipient": "GM",
      "purpose": "QUESTION",
      "subject": "When the guards leave the gate unattended",
      "evidence_refs": []
    },
    "communication_mode": "IN_WORLD_ACTION",
    "interpretation_status": "INTERPRETED",
    "player_intent": {
      "summary": "Ask Keeper Nara when the guards leave the gate unattended"
    },
    "asserted_premises": [
      {
        "text": "Keeper Nara watches the road at the courtyard gate."
      },
      {
        "text": "The player wants to know the timing or conditions when the guards leave the gate unattended."
      }
    ],
    "requested_outcomes": [
      {
        "text": "Obtain information from Keeper Nara about when the guards leave the gate unattended."
      }
    ],
    "action_components": [
      {
        "order": 1,
        "description": "Ask Keeper Nara when the guards leave the gate unattended",
        "target_ref": "keeper_nara",
        "operation_class": "ASK"
      }
    ],
    "references": {
      "permitted_entity_ids": [
        "keeper_nara"
      ],
      "unresolved_references": []
    },
    "clarification_question": "",
    "correction": {
      "subject": "NONE",
      "note": ""
    }
  },
  "annotations": [],
  "reconciliation": {
    "annotations": [],
    "addressee": null,
    "operation": "ASK"
  },
  "handler": "question",
  "resolver_invoked": null,
  "addressee": "keeper_nara",
  "subject": {
    "speaker_id": "keeper_nara",
    "addressee": "player",
    "requested_subject": "that",
    "requested_information": "hidden",
    "reference": "current_request",
    "candidate_sources": [],
    "selected_source": "",
    "ambiguous": false,
    "ownership": "npc"
  },
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara says, \"I couldn't tell you.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "I ask Keeper Nara what the password is.",
    "turn_identity": "rc_1966063fc5c1",
    "speaker": "Keeper Nara",
    "addressee": "player",
    "target": "Keeper Nara",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "dialogue_authority.player_line"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "rc_1966063fc5c1",
      "operation": "ask",
      "interlocutor_id": "keeper_nara",
      "expected_resolution": "answer"
    },
    "resolution_kind": "question",
    "generation_attempts": 0,
    "skipped_mutators": [
      "apply_response_policy_enforcement",
      "apply_authored_knowledge_realization_to_gm",
      "apply_stay_leave_narration_agreement_to_gm",
      "apply_destination_arrival_realization_to_gm",
      "apply_perception_non_invention_to_gm",
      "apply_final_emission_gate",
      "enforce_emitted_contract_monotonicity",
      "apply_spoken_state_refinement_cash_out"
    ],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "dialogue_authority.player_line",
    "speaker_id": "keeper_nara",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 1,
    "interpretation_calls": 1,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 1922,
    "output_tokens": 165,
    "purposes": [
      "interpretation"
    ]
  },
  "world_diff": [
    {
      "path": "/factions",
      "before": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 9,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 7,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 9,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 7,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 8,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 7,
          "assets": []
        }
      ],
      "after": [
        {
          "id": "house_verevin",
          "name": "House Verevin",
          "type": "noble_house",
          "attitude": "wary",
          "influence": 3,
          "pressure": 10,
          "goal": "Expand territory",
          "current_plan": "Gathering influence",
          "agenda_progress": 8,
          "assets": []
        },
        {
          "id": "ash_cowl",
          "name": "The Ash Cowl",
          "type": "criminal_syndicate",
          "attitude": "opportunistic",
          "influence": 3,
          "pressure": 10,
          "goal": "Control black market",
          "current_plan": "Establishing smuggling routes",
          "agenda_progress": 8,
          "assets": []
        },
        {
          "id": "ordo_pyric",
          "name": "Ordo Pyric",
          "type": "religious_order",
          "attitude": "suspicious",
          "influence": 2,
          "pressure": 9,
          "goal": "Suppress dangerous magic",
          "current_plan": "Watching newcomers",
          "agenda_progress": 8,
          "assets": []
        }
      ]
    }
  ],
  "session_diff_count": 138,
  "save_load": null,
  "failures": []
}
```

## Turn 13

Player: GM, repeat what Nara said about the road.

Delivered: Keeper Nara said: "Word is, the street beyond the gate is the north road."

```json
{
  "interpretation": null,
  "annotations": null,
  "reconciliation": null,
  "handler": "conversational_answer",
  "resolver_invoked": false,
  "addressee": null,
  "subject": null,
  "adoption": {
    "immutable": true,
    "text": "Keeper Nara said: \"Word is, the street beyond the gate is the north road.\"",
    "provenance": "authorized_host_speech",
    "attempt": 0,
    "player_input": "GM, repeat what Nara said about the road.",
    "turn_identity": "",
    "speaker": "GM",
    "addressee": "player",
    "target": "",
    "operation": "ask",
    "authority_result": "accepted",
    "grounding_result": "not_a_replacement_trigger",
    "hard_validation": {
      "hard_valid": true,
      "reasons": [],
      "soft_flags": [],
      "authority": [
        "conversational_decision:gm_recall_of_npc_statement"
      ],
      "gm_resolution_decision_audit": null
    },
    "interaction_completion": true,
    "contract_satisfying": true,
    "contract": {
      "contract_id": "",
      "operation": "",
      "interlocutor_id": "",
      "expected_resolution": ""
    },
    "resolution_kind": "conversational_answer",
    "generation_attempts": 0,
    "skipped_mutators": [],
    "speech_adoption": "AUTHORIZED_HOST_SPEECH",
    "authorization_source": "conversational_decision:gm_recall_of_npc_statement",
    "speaker_id": "",
    "canonical": false,
    "candidate_disposition": "host_selected"
  },
  "calls": {
    "provider_calls": 0,
    "interpretation_calls": 0,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "purposes": []
  },
  "world_diff": [],
  "session_diff_count": 7,
  "save_load": {
    "context_equal": true
  },
  "failures": []
}
```
