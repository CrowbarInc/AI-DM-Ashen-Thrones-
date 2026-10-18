# PR-BS Call-Chain Evidence

Mode: discovery only. No gameplay or model API calls were performed for this artifact.

## Runtime Map

| Step | File -> function/class | Responsibility | Evidence |
| --- | --- | --- | --- |
| 1 | `game/api.py -> chat` | Loads campaign/session/world/scene, increments turn counter, advances world tick/clock, classifies the turn, and orchestrates resolution/narration. | `game/api.py:5404-5520` |
| 2 | `game/live_resolution.py -> attach_interaction_obligation` | Builds and attaches the typed `resolution_contract` and live resolution metadata to the resolution object. | `game/live_resolution.py:384-458` |
| 3 | `game/resolution_contract.py -> ResolutionContract` and helpers | Owns operation, target, dimensions, epistemic mode, provenance, expected resolution, and raw player input. | `game/resolution_contract.py:1-5`, `24-64`, `265-279` |
| 4 | `game/gm_resolution_decision.py -> build_gm_resolution_decision` / `attach_gm_resolution_decision` | Turns contract plus scene/world/temporal state into `GMResolutionDecision`, `epistemic_acts`, and `realization_claims`. | `game/gm_resolution_decision.py:231-306`, `1496-1574`, `2054-2290` |
| 5 | `game/prompt_context.py -> build_narration_context` | Canonical prompt-context renderer and packager. Assembles instructions, response policy, visibility, narrative plan, turn packet, memory, scene/world slices, and bounded improvisation projection. | `game/prompt_context.py:1-91`, `735-759` |
| 6 | `game/gm.py -> build_messages` | Calls prompt-context assembly, adds extra instruction strings, serializes one user JSON payload, and pairs it with `SYSTEM_PROMPT`. | `game/gm.py:4005-4244` |
| 7 | `game/gm.py -> call_gpt` | Sends `client.responses.create(model=route.selected_model, input=messages)`. | `game/gm.py:4473-4505` |
| 8 | `game/response_policy_enforcement.py -> guard_gm_output` plus `game/gm_resolution_decision.py -> audit_realization_envelope_against_decision` | Parses/normalizes model output and validates declared claims/narration against the decision. | `game/gm.py:4662`, `game/gm_resolution_decision.py:3203-3460` |
| 9 | `game/immutable_valid_response.py -> run_preserve_if_valid` | Accepts hard-valid output, regenerates once with structured feedback when invalid, then preserves only an immutable accepted response or safe nonresolution. | `game/immutable_valid_response.py:1-16`, `684-790`, `1288-1320` |
| 10 | `game/api.py -> retry loop` and `game/gm_retry.py -> build_retry_prompt_for_failure` | For non-immutable candidates, selects retry failures and appends retry feedback to the full original messages. | `game/api.py:3071-3155`; `game/gm_retry.py:2308-2517` |
| 11 | `game/bounded_improvisation.py` | Validates low-consequence `improvisation_proposals`; accepted entries are runtime continuity, not authored world truth. | `game/bounded_improvisation.py:1-5`, `230-316`, `402-450` |
| 12 | `game/api.py` post-generation sequence | Applies downstream validators/metadata and final emission while respecting immutable accepted responses. | `game/api.py:3380-3420` |

## Important Ownership Notes

- `game.prompt_context` says it is the canonical owner for prompt-context assembly and that prompt bundles are read-side instruction carriers, not canonical stores.
- `ResolutionContract` records what the player wants resolved; it explicitly does not decide what the DM may invent.
- `GMResolutionDecision` is the canonical bridge from the contract and authoritative state to model-facing realization authority.
- `declared_claims` do not authorize themselves. The model is told to realize existing decision claims where possible and only propose bounded inference/hypothesis when the supplied decision permits it.
- Retry construction in `game/api.py` appends feedback to `list(messages)`, so the full system prompt and full base user JSON are resent.
