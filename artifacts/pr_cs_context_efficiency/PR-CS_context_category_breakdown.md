# PR-CS Context Category Breakdown

See `PR-CS_token_accounting.csv` for per-request estimates. Across exact captured initial generation requests, the main categories are:

- System instructions: mandatory, but repeated by payload instructions; narration-only requests still carry a large universal rule hierarchy.
- Narration and authority policies: mandatory in principle, but currently sent as a broad aggregate instead of resolver-specific compact rules.
- Mechanical resolution data: mandatory for consequential/action turns, oversized for harmless subjective dialogue because full `gm_resolution_decision.realization_claims` and `decision_facing_answer_recipe.required_content` duplicate scene facts.
- Scene/world state: current scene is required, but visible/opening/journal seed facts and lead/world pressure slices repeat semantically.
- Conversation history: bounded and comparatively small in early turns; not the primary cause of 31k-35k prompts.
- Retry feedback: absent on initial requests; large only on regeneration. PR-CR removes the eligible authored retry path.
