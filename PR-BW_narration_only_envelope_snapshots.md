# PR-BW Narration-Only Envelope Snapshots

## P1

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## P2

```text
NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: {"narration": "player-facing response"}. Do not include other fields. The application will normalize this internally.
```

## P3

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## G1

selected_envelope: `narration_only`

```text
NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: {"narration": "player-facing response"}. Do not include other fields. The application will normalize this internally.
```

## G2

selected_envelope: `narration_only`

```text
NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: {"narration": "player-facing response"}. Do not include other fields. The application will normalize this internally.
```

## G3

selected_envelope: `structured_realization`

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## G4

selected_envelope: `structured_realization`

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## G5

selected_envelope: `structured_realization`

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## G6

selected_envelope: `structured_realization`

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```

## consequential_control

selected_envelope: `structured_realization`

```text
Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
```
