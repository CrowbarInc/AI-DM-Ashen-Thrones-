# PR-DD Provider Request Trace

No production code was changed. No provider call was made. Production save mtimes were unchanged before and after measurement.

HEAD at audit start: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

The dirty worktree was left in place. Measurements call the current worktree functions.

## Pipeline

```
player input
  -> action interpretation
  -> deterministic resolution
  -> authority contracts
  -> narrative planning
  -> provider context construction
  -> message serialization
  -> provider request
  -> validation
  -> finalization
```

| Stage | Source | Provider-facing? |
|---|---|---|
| Player input | `game.api.chat`, `game.api.action` | The text is copied into `player_input`. |
| Directed social entry | `game.interaction_context.resolve_directed_social_entry` | No. |
| Freeform parse | `game.intent_parser.parse_freeform_to_action` | No. |
| Social parse | `game.social.parse_social_intent`, `game.interaction_routing._build_dialogue_first_action` | No. |
| Social resolution | `game.social.resolve_social_action` | Outcome later appears in `mechanical_resolution.social`. |
| Exploration resolution | `game.noncombat_resolution.resolve_noncombat_action` -> `game.exploration.resolve_exploration_action` | Outcome later appears as `resolved_exploration_action` when the kind is an exploration kind and action-outcome mode is off. |
| Combat resolution | `game.combat.resolve_attack` | Outcome later appears as `resolved_combat_action`. Authored scenes have no enemies, so this stage was measured only on the existing goblin test fixture. |
| Ordinary resolver label | `game.ordinary_semantic_ownership.select_ordinary_resolver` | Stored on resolution metadata. Harmless projection requires `selected_resolver == social`. |
| Resolution contract and obligation | `game.live_resolution.attach_interaction_obligation` | Compact contract is shipped as `resolution_contract`. |
| GM resolution decision | `game.gm_resolution_decision.attach_gm_resolution_decision`, `build_gm_resolution_decision` | Shipped as `gm_resolution_decision`. |
| Answer recipe | `game.gm_resolution_decision.build_decision_facing_answer_recipe` | Shipped as `decision_facing_answer_recipe`. The system text says it grants no new authority. |
| Speaker contract | `game.interaction_context.build_speaker_selection_contract` | Shipped as `speaker_selection`. |
| CTIR | `game.ctir_runtime.build_runtime_ctir_for_narration`, attached from `game.api._build_gpt_narration_from_authoritative_state` | Not a raw prompt section. It selects the plan bundle. |
| Narrative plan | `game.narration_plan_bundle.build_narration_plan_bundle`, `ensure_narration_plan_bundle_for_turn` | Rendered as `narrative_plan`. `prompt_context` does not replan. |
| Narration context arguments | `game.gm.collect_narration_context_call_kwargs` | Prepares scene layers, intent, recent log slice `recent_log[-8:]`, world-state view, and mode instruction. |
| Structured context | `game.prompt_context.build_narration_context` | User-message JSON. |
| Response policy | `game.planner_ctir_projection.build_response_policy`, then contract attachments inside `build_narration_context` | `response_policy`. |
| System instructions | `game.gm.SYSTEM_PROMPT`, `game.gm.NARRATION_ONLY_SYSTEM_PROMPT`, header from `RESPONSE_RULE_PRIORITY` | Message 0. |
| Envelope choice | `game.gm_resolution_decision.select_provider_response_envelope` via `game.gm._provider_response_contract_from_payload` | Chooses narration-only or structured realization. |
| Exact instruction dedupe | `game.gm._dedupe_provider_payload_instructions` | Drops instruction lines that are exact substrings of the selected system prompt. |
| Harmless projection | `game.gm._project_harmless_social_provider_context` | Drops opening and transition scaffolding and compacts turn packet, mechanical resolution, and narrative plan when every listed predicate passes. |
| Serialization | `game.gm.build_messages` | Two messages. User content is `json.dumps(..., ensure_ascii=False)`. |
| API rewrite | `game.api._build_gpt_narration_from_authoritative_state` | After `build_messages`, the API may attach `response_type_contract` and rewrite the user message with `ensure_ascii=True`. This audit's hashes are the `build_messages` bytes. |
| Provider call | `game.gm.call_gpt` | Not invoked. |
| Retry text | `game.gm_retry.build_retry_prompt_for_failure` | Appended by the API as another user message. First-pass requests measured here do not include it. |
| Validation and preserve | `game.immutable_valid_response.run_preserve_if_valid` and the surrounding checks in `_build_gpt_narration_from_authoritative_state` | Reads the candidate narration plus resolution, scene, and policy. It does not need a second copy of those objects inside the prompt. |
| Finalization | post-GM adoption in `game.api` | Reads authoritative resolution and the accepted narration. |

## Section owners

| Request part | Function |
|---|---|
| System instructions | `game.gm._SYSTEM_PROMPT_HEADER`, `SYSTEM_PROMPT`, `NARRATION_ONLY_SYSTEM_PROMPT` |
| Response policy | `game.planner_ctir_projection.build_response_policy`; nested contracts assigned in `game.prompt_context.build_narration_context` |
| Scene context | `game.gm._scene_layers`; `scene` object in `build_narration_context` |
| World context | `game.prompt_context._compress_world`; world-state view inside `collect_narration_context_call_kwargs` |
| NPC context | `dialogue_social_plan` projection in `build_messages`; `speaker_selection`; `active_interlocutor` |
| Mechanical resolution | `game.prompt_context._provider_mechanical_resolution`; harmless compaction in `game.gm._compact_social_mechanical_resolution` |
| GM resolution decision | `game.gm_resolution_decision.attach_gm_resolution_decision` |
| Narrative plan | `game.narration_plan_bundle.build_narration_plan_bundle` |
| Answer recipe | `game.gm_resolution_decision.build_decision_facing_answer_recipe` |
| Conversation history | `collect_narration_context_call_kwargs` log slice; `game.prompt_context` memory-window functions; snippet cap `MAX_LOG_ENTRY_SNIPPET = 200` |
| Response envelope | `select_provider_response_envelope` |
| Retry context | `game.gm_retry.build_retry_prompt_for_failure` |

## Measurement boundary

Representative payloads were built with `build_messages` after the same CTIR and narration-plan seam the API uses. They were not passed through the API's later `ensure_ascii=True` rewrite. Hashes below are reproducible at the `build_messages` boundary. They are not claimed as the final HTTP body.
