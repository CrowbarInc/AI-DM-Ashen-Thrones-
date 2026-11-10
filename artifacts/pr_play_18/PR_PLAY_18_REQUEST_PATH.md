# PR-PLAY-18 request path

The following stages trace actual code. Nested calls are described by inputs/outputs, not implied to be a single flat stack. build_messages calls build_narration_context; prepare_opening_renderer calls catalog construction and schema construction; renderer calls parsing/validation before response conversion. The next caller/consumer follows the output named in each row. request_path_trace.json preserves machine-readable locations.

| Source / function | Inputs | Outputs / downstream consumer | Configuration and contract |
| --- | --- | --- | --- |
| `game/api.py:5246` / `new_campaign` | New Campaign request; isolated fixture storage | reset unstarted campaign | No provider call; engine authority |
| `game/api.py:6346` / `start_campaign` | Start Campaign request; readiness/admission | opening scope | ASHEN_OPENING_RENDERER evaluated later |
| `game/api.py:6386` / `_start_campaign_after_admission` | campaign, character, session, world, combat, scene | bootstrap resolution and provisional turn | synchronize addressability before opening_scope.track; provisional tick rolls back on rejection |
| `game/api.py:4711` / `_opening_scene_normalized_action_and_resolution` | internal_bootstrap=True; scene | scene-opening normalized action/resolution | scene_opening intent |
| `game/api.py:4418` / `_run_resolved_turn_pipeline` | authoritative game documents; normalized action | validated GM response and response contract | deterministic pipeline |
| `game/api.py:3163` / `_build_gpt_narration_from_authoritative_state` | narration bundle, scene and authority state | provider messages and validated candidate | response_type_contract scene_opening; bounded call_gpt |
| `game/gm.py:4590` / `build_messages` | narration context call kwargs and game state | legacy system + JSON user payload | shared construction remains unchanged |
| `game/prompt_context.py:1527` / `build_narration_context` | public scene, authority bundle, opening facts | narration payload including realization claims | opening public facts/curation supplied here |
| `game/gm.py:5182` / `call_gpt` | assembled messages; route; response type | rendered structured GM response or contract failure | only scene_opening reads renderer flag; enabled selects preparation before dispatch |
| `game/opening_presentation_renderer.py:264` / `prepare_opening_renderer` | original messages | local catalog; public selection messages; strict text format | dedicated opening contract replaces legacy provider input |
| `game/opening_presentation_renderer.py:137` / `build_opening_public_catalog` | original JSON payload | entries/by_id/required_ids or fail closed | public-only claims, curated coverage; authority stays local |
| `game/opening_presentation_renderer.py:287` / `opening_plan_text_format` | public catalog | strict Responses API text.format | selected_entries required; per-ID variants; no additional properties |
| `game/provider_budget.py:312` / `dispatch` | SDK method plus model/input/text/max_output_tokens | SDK response | admission and exactly-one dispatch; kwargs forwarded unchanged |
| `game/opening_presentation_renderer.py:422` / `realize_opening_provider_text` | extracted SDK text; local catalog | render result or reason | JSON parser then renderer validator; no legacy fallback |
| `game/opening_presentation_renderer.py:330` / `validate_presentation_plan` | plan + local catalog | approved choices or rejection | IDs, variants, unknown fields, required coverage, order, duplicates and bound |
| `game/opening_presentation_renderer.py:378` / `render_opening` | validated choices | engine-authored text, declarations and trace | no model prose published |
| `game/opening_presentation_renderer.py:429` / `gm_response_from_render` | successful render | structured response with immutable rendered metadata | engine declarations; null state proposals |
| `game/api.py:5893` / `_complete_opening_turn_persistence_like_chat` | validated result and tracked opening scope | 200 publication/one commit or 422 rollback | acceptance-gated persistence |
| `game/opening_presentation_renderer.py:465` / `enforce_rendered_publication` | GM response with render metadata | restored engine text; null update proposals | applied in API final publication path |

Critical answer: **B — during provider request construction in call_gpt**, after shared legacy message construction and before SDK dispatch. Before repair, prepare_opening_renderer merely inserted a second system message while retaining the full legacy system and user payload. Selection was not deferred entirely to response time, but the outgoing requirements remained contradictory. After repair the same branch replaces provider-facing messages and attaches its text.format schema; the local authority catalog remains available to the response renderer.

OpenAI client construction uses existing API-key, timeout and SDK-retry settings. Model routing, pinning, admission/budgets and the opening output cap are unchanged. ProviderBudget.dispatch forwards keyword arguments to responses.create. The ordinary parser branch (_safe_json) is used only when opening_catalog is absent. The enabled branch extracts text with _extract_provider_response_text, then uses realize_opening_provider_text. Unsupported/incomplete responses still take existing failure handling. Publication enforcement is still applied in the API path; no new ordinary-turn renderer routing exists.
