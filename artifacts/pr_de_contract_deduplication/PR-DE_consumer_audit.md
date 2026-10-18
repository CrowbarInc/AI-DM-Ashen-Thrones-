# PR-DE Consumer Audit

Consumers were classified against the serialized provider payload, not against the in-memory narration context.

| Field | Provider prompt | Resolution | Validation | Finalization | Retry | Diagnostics | Tests |
|---|---|---|---|---|---|---|---|
| `anti_railroading_contract` | duplicate of `response_policy.anti_railroading` | built in `prompt_context` | reads policy or GM contract | unchanged | `gm_retry` already accepts the policy child | emission debug is copied before serialization | context tests read `build_narration_context` |
| `context_separation_contract` | same | same | gate reads policy or GM contract | unchanged | retry already checks both names | `build_messages` copies a summary into resolution metadata before omission | same |
| `player_facing_narration_purity_contract` | same | same | GM/policy resolvers | unchanged | not dependent on the serialized top-level key | same | same |
| `social_response_structure_contract` | same | same | policy resolvers | unchanged | same | same | same |
| `interaction_continuity_contract` | same | same | policy child | unchanged | same | same | compact prompts already omit this key |
| `fallback_behavior` | same | same | `response_policy_enforcement` reads `policy.fallback_behavior` | repair metadata is separate from the provider object | retry reads the policy child | same | compact prompts already omit this key |
| `conversational_memory_window` | same | selector output is stored on the policy | inspection falls back to `response_policy.conversational_memory_window` | `api.py` copies the window onto the GM result | not a retry-construction input | `build_messages` copies the window into emission debug before omission | latency tests still see the snapshot `interaction_continuity` |

## Engine-side read of the serialized payload

`api.py` parses the user message after `build_messages` and copies `conversational_memory_window` onto the GM object. That was the only engine consumer of one of the seven top-level locations. It now uses the policy child when the top-level key is absent. The value is JSON-equal, so inspection still receives the window.

No consumer required the top-level provider location itself. Resolution, validation, and finalization keep using the policy object and the in-memory contracts. Retry construction was not edited.

The distinct `interaction_continuity` snapshot remains serialized because it is not equal to the policy child. Compact-prompt tests still require that snapshot.
