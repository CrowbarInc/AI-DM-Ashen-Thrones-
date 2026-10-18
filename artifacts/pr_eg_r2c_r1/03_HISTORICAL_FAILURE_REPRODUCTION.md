# 03 — Historical Failure Reproduction

Evidence classes: CONTROLLED/DETERMINISTIC owner seams and FROZEN BASELINE. Before production edits, A/B/C/E/G failed and H passed; short D/F fixtures passed. The preserved R2C fresh transcripts contain the historical D/F failures. A later long-history probe against frozen pre-edit source reproduces D/F failures after ten competing statements; final source passes. This timing distinction is explicit: all eight failures were not reproduced in the initial short pre-edit probe.

Before: ```json
[
  {
    "id": "A",
    "text": "Sergeant Mara says, \"I couldn't tell you.\"",
    "pass_": false,
    "authority": {
      "requested_information": "general",
      "subject": "can repeat",
      "knowledge_posture": "unknown",
      "answer_relation": "none",
      "improvisation_permitted": false,
      "improvisation_scope": "none",
      "narration_determined": false,
      "player_line": "",
      "canonical": false,
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "npc_role": "",
      "npc_disposition": "",
      "prohibited_claims": [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
        "invented_answer"
      ],
      "prior_commitments": [],
      "reconciled_plan": "",
      "reuse_prior_speech": false
    }
  },
  {
    "id": "B",
    "text": "Sergeant Mara says, \"I couldn't tell you.\"",
    "pass_": false,
    "authority": {
      "requested_information": "general",
      "subject": "can repeat simpler",
      "knowledge_posture": "unknown",
      "answer_relation": "none",
      "improvisation_permitted": false,
      "improvisation_scope": "none",
      "narration_determined": false,
      "player_line": "",
      "canonical": false,
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "npc_role": "",
      "npc_disposition": "",
      "prohibited_claims": [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
        "invented_answer"
      ],
      "prior_commitments": [],
      "reconciled_plan": "",
      "reuse_prior_speech": false
    }
  },
  {
    "id": "C",
    "selected": {
      "id": "watch",
      "text": "Guards watch the north gate throughout the night.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": false
  },
  {
    "id": "D",
    "directive": {
      "action": "answer",
      "owner": "gm",
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "line": "Sergeant Mara said: \"The street beyond the gate is the north road.\"",
      "reason": "gm_recall_of_npc_statement"
    },
    "pass_": true
  },
  {
    "id": "F",
    "directive": {
      "action": "answer",
      "owner": "gm",
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "line": "Sergeant Mara said: \"The street beyond the gate is the north road.\"",
      "reason": "gm_recall_of_npc_statement"
    },
    "pass_": true
  },
  {
    "id": "E",
    "selected": {
      "id": "road",
      "text": "The street beyond the gate is the north road.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": false
  },
  {
    "id": "G",
    "selected": {
      "id": "road",
      "text": "The street beyond the gate is the north road.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": false
  },
  {
    "id": "H",
    "text": "Sergeant Mara says, \"I prefer the evening.\"",
    "pass_": true,
    "adoption": {
      "immutable": true,
      "text": "Sergeant Mara says, \"I prefer the evening.\"",
      "provenance": "authorized_host_speech",
      "attempt": 0,
      "player_input": "What do you personally enjoy about the evening?",
      "turn_identity": "r2c",
      "speaker": "Sergeant Mara",
      "addressee": "player",
      "target": "sergeant mara",
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
        "contract_id": "r2c",
        "operation": "ask",
        "interlocutor_id": "sergeant_mara",
        "expected_resolution": ""
      },
      "resolution_kind": "social_exchange",
      "generation_attempts": 0,
      "skipped_mutators": [],
      "speech_adoption": "AUTHORIZED_HOST_SPEECH",
      "authorization_source": "conversational_continuity.bounded_personal_line",
      "speaker_id": "sergeant_mara",
      "canonical": false,
      "candidate_disposition": "UNAUTHORIZED_GENERATED_CANDIDATE"
    }
  }
]
```

Final: ```json
[
  {
    "id": "A",
    "text": "Sergeant Mara says, \"The street beyond the gate is the north road.\"",
    "pass_": true,
    "authority": {
      "topic_grounding": {
        "speaker_id": "sergeant_mara",
        "addressee": "player",
        "requested_subject": "can repeat",
        "requested_information": "general",
        "reference": "delivered_speech",
        "candidate_sources": [],
        "selected_source": "delivered:sergeant_mara:0:statement",
        "ambiguous": false,
        "ownership": "npc"
      },
      "requested_information": "general",
      "subject": "can repeat",
      "knowledge_posture": "unknown",
      "answer_relation": "none",
      "improvisation_permitted": false,
      "improvisation_scope": "none",
      "narration_determined": true,
      "player_line": "Sergeant Mara says, \"The street beyond the gate is the north road.\"",
      "canonical": false,
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "npc_role": "",
      "npc_disposition": "",
      "prohibited_claims": [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
        "invented_answer"
      ],
      "prior_commitments": [],
      "reconciled_plan": "",
      "reuse_prior_speech": true
    }
  },
  {
    "id": "B",
    "text": "Sergeant Mara says, \"The street beyond the gate is the north road.\"",
    "pass_": true,
    "authority": {
      "topic_grounding": {
        "speaker_id": "sergeant_mara",
        "addressee": "player",
        "requested_subject": "can repeat simpler",
        "requested_information": "general",
        "reference": "delivered_speech",
        "candidate_sources": [],
        "selected_source": "delivered:sergeant_mara:0:statement",
        "ambiguous": false,
        "ownership": "npc"
      },
      "requested_information": "general",
      "subject": "can repeat simpler",
      "knowledge_posture": "unknown",
      "answer_relation": "none",
      "improvisation_permitted": false,
      "improvisation_scope": "none",
      "narration_determined": true,
      "player_line": "Sergeant Mara says, \"The street beyond the gate is the north road.\"",
      "canonical": false,
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "npc_role": "",
      "npc_disposition": "",
      "prohibited_claims": [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
        "invented_answer"
      ],
      "prior_commitments": [],
      "reconciled_plan": "",
      "reuse_prior_speech": true
    }
  },
  {
    "id": "C",
    "selected": {
      "id": "road",
      "text": "The street beyond the gate is the north road.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": true
  },
  {
    "id": "D",
    "directive": {
      "action": "answer",
      "owner": "gm",
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "line": "Sergeant Mara said: \"The street beyond the gate is the north road.\"",
      "reason": "gm_recall_of_npc_statement",
      "topic_grounding": {
        "speaker_id": "sergeant_mara",
        "ownership": "gm",
        "reference": "delivered_speech",
        "topic_id": "",
        "selected_source": null,
        "delivered_turn": 0,
        "canonical": false
      }
    },
    "pass_": true
  },
  {
    "id": "F",
    "directive": {
      "action": "answer",
      "owner": "gm",
      "npc_id": "sergeant_mara",
      "npc_name": "Sergeant Mara",
      "line": "Sergeant Mara said: \"The street beyond the gate is the north road.\"",
      "reason": "gm_recall_of_npc_statement",
      "topic_grounding": {
        "speaker_id": "sergeant_mara",
        "ownership": "gm",
        "reference": "delivered_speech",
        "topic_id": "",
        "selected_source": null,
        "delivered_turn": 0,
        "canonical": false
      }
    },
    "pass_": true
  },
  {
    "id": "E",
    "selected": {
      "id": "watch",
      "text": "Guards watch the north gate throughout the night.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": true
  },
  {
    "id": "G",
    "selected": {
      "id": "watch",
      "text": "Guards watch the north gate throughout the night.",
      "clue_id": null,
      "clue_text": null
    },
    "pass_": true
  },
  {
    "id": "H",
    "text": "Sergeant Mara says, \"I prefer the evening.\"",
    "pass_": true,
    "adoption": {
      "immutable": true,
      "text": "Sergeant Mara says, \"I prefer the evening.\"",
      "provenance": "authorized_host_speech",
      "attempt": 0,
      "player_input": "What do you personally enjoy about the evening?",
      "turn_identity": "r2c",
      "speaker": "Sergeant Mara",
      "addressee": "player",
      "target": "sergeant mara",
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
        "contract_id": "r2c",
        "operation": "ask",
        "interlocutor_id": "sergeant_mara",
        "expected_resolution": ""
      },
      "resolution_kind": "social_exchange",
      "generation_attempts": 0,
      "skipped_mutators": [],
      "speech_adoption": "AUTHORIZED_HOST_SPEECH",
      "authorization_source": "conversational_continuity.bounded_personal_line",
      "speaker_id": "sergeant_mara",
      "canonical": false,
      "candidate_disposition": "UNAUTHORIZED_GENERATED_CANDIDATE"
    }
  }
]
```

Extended D/F evidence: extended_historical_reproduction.json. Root causes: the eight-row history cap evicts early road speech; zero-score lookup falls back to the latest remark; speaker filters can fall back to another speaker; repeat recognition misses ordinary repeat requests; subject overlap admits the first location-related topic; plain `watch` was not classified consistently; revealed facts are usually excluded; a second evidence-ref recall path bypasses current-question sufficiency. These are repaired at continuity, dialogue authority and the existing social selector.
