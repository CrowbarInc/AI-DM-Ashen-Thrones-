# PR-CS Prompt Construction Graph

```text
HTTP turn / probe
  -> game.api turn orchestration
    -> deterministic resolver / CTIR attachment
      -> resolution_contract
      -> gm_resolution_decision
      -> response_type_contract
      -> narration_plan_bundle
    -> game.gm.collect_narration_context_call_kwargs
    -> game.gm.build_messages
      -> game.prompt_context.build_narration_context
        -> response_policy builders
        -> narration_visibility builder
        -> narrative_authority builder
        -> scene_state_anchor builder
        -> context_separation / anti_railroading / purity / authenticity contracts
        -> conversational_memory_window selector
        -> world_progression and lead projections
        -> speaker_selection / dialogue_social_plan / NPC knowledge gates
        -> public_narrative_plan_projection_for_prompt
      -> social-authority dialogue plan key pruning
      -> passive / known-answer / exploration / combat overlays
      -> provider contract selection
      -> system prompt selection
      -> provider_input = [system, user JSON payload]
    -> OpenAI Responses API call
    -> hard parse / validation / retry gate
    -> immutable valid response finalizer
```

Duplication enters through independent paths: `SYSTEM_PROMPT`/`NARRATION_ONLY_SYSTEM_PROMPT`, `payload.instructions`, `response_policy`, `narration_visibility`, `gm_resolution_decision.realization_claims`, `decision_facing_answer_recipe.required_content`, and scene seed/visible/journal fact projections.

Intentional redundancy protects authority and diegetic voice. Accidental duplication is visible where identical or near-identical scene facts and rule prose are repeated three or more times in the same user payload.
