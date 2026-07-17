# Backend Contract Registry

This registry centralizes backend-facing architectural contracts currently
present in the repository. It is documentation-only. It does not introduce a
new backend, change provider routing, modify OpenAI calls, alter replay or
provenance behavior, update CI policy, or move implementation authority into
documentation.

## Registry Scope

Backend contracts in this repository are the explicit interfaces around live
model access, model routing, upstream health, backend configuration, response
normalization, diagnostics, and upstream-dependent run gating.

Deterministic gameplay resolution, Final Emission legality, replay acceptance,
ruleset behavior, and local fallback text generation are not backend contracts
unless they consume backend-facing metadata.

## Contract Inventory

| Contract ID | Contract | Canonical Owner | Repository Location | Purpose | Consumers | Compatibility Requirements | Replay Implications | Provenance Implications | Versioning Status | Verification Method | Future Extensibility Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BCR-01 | Model routing decision | Model routing owner | `game/model_routing.py::ModelRouteDecision`, `game/model_routing.py::resolve_model_route`; overview in `docs/model_routing_architecture.md` | Select a configured model from explicit call-site inputs without changing player-facing schemas. | `game.gm.call_gpt`, model routing tests, architecture docs, backend contract reviewers. | Preserve deterministic route inputs: `purpose`, `response_policy`, `segmented_turn`, `retry_attempt`, `strict_social`, and `force_high_precision`. Preserve `ENABLE_MODEL_ROUTING=false` fallback to default model. | Low. Protected replay does not accept model identity as an acceptance field; long-session helpers mark model-routing escalation as not directly observable. | Low. Selected model metadata is diagnostic call context, not realization provenance authority. | Stable, configuration-versioned by environment variables rather than a formal schema version. | `tests/test_model_routing_runtime.py`, `tests/test_model_routing_escalation.py`, `tests/test_model_routing_config.py`. | Future providers should extend this surface through explicit route decisions rather than provider branching in unrelated modules. |
| BCR-02 | Backend model configuration | Configuration owner with model routing owner | `game/config.py`; user docs in `docs/README.md`; compatibility row in `docs/compatibility_residue_register.md` | Load backend-related environment settings and keep OpenAI API key validation lazy until upstream-call time. | `game.model_routing`, `game.gm.call_gpt`, `game.api_upstream_preflight`, local operators, tests. | `MODEL_NAME` remains backward compatible and seeds `DEFAULT_MODEL_NAME`. `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, and `RETRY_ESCALATION_MODEL_NAME` keep their fallback chain. `OPENAI_API_KEY` must not be required at import time. | None to low. Configuration may affect which model generated text, but protected replay should not depend on live provider identity. | Low. Configuration identifies backend context only; it must not become content ownership or fallback provenance. | Stable, env-var contract; legacy compatibility is permanent unless a separate package approves migration. | `tests/test_model_routing_config.py`, `tests/test_model_routing_runtime.py`, `tests/test_api_upstream_preflight.py`. | A future provider registry should document provider-specific env vars here without weakening lazy secret validation. |
| BCR-03 | GPT call adapter | GM/model-call owner | `game/gm.py::call_gpt` | Wrap the live OpenAI Responses API call and return the repository's expected GM output dict shape. | `game.api._build_gpt_narration_from_authoritative_state`, opening/start campaign flow, chat/action pipeline, tests that monkeypatch `game.api.call_gpt`. | Preserve the call signature and route-context kwargs used by API retry orchestration. Continue returning safe schema-shaped fallback output on upstream exceptions. | Medium. Live prose is not deterministic, but replay fixtures generally monkeypatch calls or observe finalized downstream payloads. | Medium. The adapter attaches selected-model metadata and provider-error metadata; realization/fallback provenance remains owned by downstream provenance helpers. | Stable interface, no formal version field. | `tests/test_model_routing_runtime.py`, `tests/test_model_routing_escalation.py`, `tests/test_api_upstream_preflight.py`, API pipeline tests that patch `call_gpt`. | New backend adapters should preserve the GM dict contract and keep provider-specific exceptions normalized before API callers see them. |
| BCR-04 | Prompt message adapter | Prompt/GM owner with API orchestration owner | `game/gm.py::build_messages`; API usage in `game/api.py` | Convert authoritative game/session/resolution state into the `list[dict[str, str]]` message shape consumed by `call_gpt`. | `game.api`, prompt/context tests, CTIR and social convergence paths, model call adapter. | Preserve role/content message shape and avoid bypassing deterministic resolution authority. Prompt changes must not reassign gameplay ownership to the backend. | Medium. Prompt content can affect live model output; protected replay should validate downstream deterministic surfaces rather than prompt text unless a prompt test owns the assertion. | Low to medium. Prompt debug mirrors may appear in metadata, but provenance ownership remains with realization/final-emission helpers. | Stable shape, no formal backend version. | `tests/test_build_messages_projection.py`, `tests/test_prompt_and_guard.py`, `tests/test_model_routing_escalation.py`, CTIR/prompt integration tests. | Future provider-specific message formats should be adapted at the backend boundary without changing upstream state ownership. |
| BCR-05 | Upstream error normalization | GM/model-call owner with preflight consumer | `game/gm.py::_classify_upstream_gpt_error`, `_status_code_from_upstream_error`, `_error_code_from_upstream_error` | Normalize provider/network/API failures into stable failure class, retryability, status, error code, and message excerpt fields. | `game.gm.call_gpt`, `game.api_upstream_preflight.compute_api_runtime_health_from_exception`, tests and diagnostics. | Preserve nonretryable classifications for auth, quota, invalid request, unsupported model, and model access failures. Keep excerpts secret-safe and bounded. | Medium. Upstream failures can trigger deterministic fallback paths later observed by replay, but replay should not depend on raw provider exceptions. | Medium. Provider error metadata can explain fallback selection but must not replace realization provenance family stamping. | Stable internal dict shape; no formal schema version. | `tests/test_api_upstream_preflight.py`, `tests/test_model_routing_runtime.py`, upstream fast-fallback tests where provider failures are simulated. | Multi-provider support should map provider-specific failures into this normalized shape before orchestration decisions. |
| BCR-06 | Upstream API preflight status | Upstream preflight owner | `game/api_upstream_preflight.py::UpstreamApiPreflightStatus`, `run_upstream_api_preflight`, `get_latest_upstream_api_preflight`; skip env `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT` | Probe the same Responses API path used by live calls, cache a health row, and expose startup/operator diagnostics. | `game.api` startup, `game.upstream_dependent_run_gate`, local operators, preflight tests. | Preserve lazy API key access. Preserve skip behavior for local/test environments. Preserve cached status shape and secret-safe startup lines. | Low. Preflight status validates manual/live run reliability but is not a replay acceptance contract. | Low. Health status is diagnostic and must not author content provenance. | Stable typed dict shape with no explicit version field. | `tests/test_api_upstream_preflight.py`, `tests/test_upstream_dependent_run_bhc2.py`, `tests/test_upstream_dependent_run_gate_presentation.py`. | Future providers should provide equivalent health rows and keep run-gate consumers provider-neutral where possible. |
| BCR-07 | Upstream-dependent run gate | Upstream run-gate owner | `game/upstream_dependent_run_gate.py::compute_upstream_dependent_run_gate`; presentation in `game/upstream_dependent_run_gate_presentation.py`; API embedding in `game/api.py` | Convert cached preflight health into manual testing validity and operator-facing gate payloads. | `game.api` new campaign/startup paths, validation/manual QA workflows, tests. | Do not perform new network probes. Consume cached preflight only. Preserve stable keys: `upstream_runtime_healthy`, `preflight_available`, `startup_run_valid`, `manual_testing_blocked`, `block_reason`, `preflight_health_class`, and `preflight_checked_at`. | Low. The gate can mark manual live runs invalid, but protected replay should not treat it as replay policy. | Low. Gate payloads are diagnostics and operator guidance, not content provenance. | Stable dict shape; no formal schema version. | `tests/test_upstream_dependent_run_bhc2.py`, `tests/test_upstream_dependent_run_gate_presentation.py`, startup/new-campaign tests. | Future backend health providers should feed the same cached-health contract or a separately versioned successor. |
| BCR-08 | Backend diagnostics and model-route metadata | GM diagnostics owner | `game/gm.py::_attach_model_route_metadata`, `_log_model_route`; metadata emitted by `call_gpt` | Attach selected model, route reason, route family, route purpose, retry attempt, and escalation diagnostics to GM output. | Finalized response metadata consumers, debug logs, model routing tests, realization/provenance tests that assert metadata preservation. | Preserve metadata as diagnostic. Do not make model route metadata a legality gate or provenance source of truth. | Low to medium. Metadata may be visible in downstream debug payloads, but protected replay currently avoids direct model-routing acceptance. | Medium. Metadata can explain backend selection but must not replace realization provenance fields such as fallback family. | Stable key set by convention; no formal version field. | `tests/test_model_routing_runtime.py`, `tests/test_model_routing_escalation.py`, `tests/test_realization_provenance.py`. | Future provider diagnostics should extend metadata additively and document any promoted stable keys here. |
| BCR-09 | Backend compatibility surface | Compatibility planning owner with model routing owner | `docs/compatibility_residue_register.md` row `CR-14`; implementation in `game/config.py` and `game/model_routing.py` | Preserve legacy `MODEL_NAME` and single-model routing behavior while newer route configuration exists. | Local operators, docs, preflight tests, model routing tests, future backend expansion work. | Do not remove `MODEL_NAME` support or single-model disabled-routing behavior without a compatibility retirement package. | None to low. Compatibility affects selected model, not replay schema. | Low. Compatibility configuration is not provenance ownership. | Permanent compatibility until separately reclassified. | `tests/test_model_routing_config.py`, `tests/test_model_routing_runtime.py`, compatibility register review. | Any retirement proposal must start from the compatibility register and include consumer evidence. |

## Ownership Mapping

| Owner Category | Owns | Does Not Own |
|---|---|---|
| Model routing owner | Route decision inputs, selected model, route family, route reason, routing-disabled fallback behavior. | Prompt content, gameplay resolution, final player-facing legality, provider exception classes. |
| Configuration owner | Environment loading, lazy secret validation, model env-var fallback chain. | Provider routing policy beyond configured values; runtime fallback semantics. |
| GM/model-call owner | Live backend call adapter, provider response text normalization, model-route metadata, upstream error normalization. | API retry loop orchestration, deterministic gameplay resolution, replay acceptance. |
| Prompt/GM owner | Message shape passed to backend and prompt payload assembly from authoritative state. | Mechanical resolution authority, CTIR state authority, backend provider selection. |
| Upstream preflight owner | Health probe, cached status row, startup lines, skip-env interpretation. | Manual QA policy beyond health row; gameplay behavior. |
| Upstream run-gate owner | Cached-health-to-operator gate mapping and presentation. | Network probing, provider calls, protected replay policy. |
| Compatibility planning owner | Legacy backend configuration inventory and retirement prerequisites. | Behavior retirement or migration by documentation alone. |

## Consumer Mapping

| Consumer | Consumed Contracts | Notes |
|---|---|---|
| `game.api` shared turn pipeline | BCR-03, BCR-04, BCR-07 | API orchestrates when messages are built, calls are made, retries happen, and upstream-dependent startup/new-campaign gates are reported. |
| `game.gm_retry` and retry orchestration callers | BCR-03, BCR-05, BCR-08 | Retry logic consumes GM output and backend error/fallback metadata indirectly through API orchestration. |
| Model routing tests | BCR-01, BCR-02, BCR-03, BCR-08 | Verify deterministic route selection, metadata attachment, disabled-routing behavior, and env compatibility. |
| Upstream preflight tests | BCR-02, BCR-05, BCR-06 | Verify lazy secret access, status normalization, cache behavior, startup output, and client-factory probe behavior. |
| Upstream run-gate tests | BCR-06, BCR-07 | Verify cached preflight is the only authority for run validity and operator guidance. |
| Protected replay / golden replay | BCR-03, BCR-08 indirectly | Replay should observe finalized downstream payloads, not raw provider behavior or direct model-routing frequency. |
| Compatibility register | BCR-02, BCR-09 | Tracks legacy env-var and single-model compatibility as an active compatibility surface. |
| Documentation/governance reviewers | All BCR contracts | Use this registry to decide whether backend work requires docs, compatibility, replay/provenance, or test updates. |

## Compatibility Assessment

| Compatibility Surface | Current Status | Requirement |
|---|---|---|
| `MODEL_NAME` legacy env var | Permanent Compatibility | Must continue to seed `DEFAULT_MODEL_NAME` when newer variables are omitted. |
| `ENABLE_MODEL_ROUTING=false` | Active compatibility | Must keep calls on `DEFAULT_MODEL_NAME` without changing player-facing schemas. |
| Single OpenAI Responses API adapter | Active | Future providers must not leak provider-specific response shapes beyond the backend adapter. |
| Safe fallback GM dict on upstream exception | Active | Must preserve expected response shape so API callers do not special-case provider exceptions. |
| Cached upstream preflight | Active | Run gate must consume cache only and must not perform hidden network probes. |
| Route metadata in GM output | Active | Metadata may be extended additively but must remain diagnostic unless separately promoted. |

## Version Status

| Contract Area | Version Status | Change Rule |
|---|---|---|
| Model route decision | Stable, unversioned dataclass | Additive fields require tests and registry update; semantic changes require implementation package approval. |
| Backend env vars | Stable env-var contract | Compatibility-impacting changes must update compatibility register and docs. |
| GM output from `call_gpt` | Stable dict shape by convention | Shape changes require API/replay/provenance review. |
| Upstream error normalization | Stable internal dict shape | New failure classes must be tested and documented here. |
| Preflight status | Stable typed dict | New keys should be additive and tested; changed meanings require run-gate review. |
| Upstream run gate | Stable dict shape | Key removal or semantic changes require governance and API consumer review. |
| Backend diagnostics metadata | Stable key set by convention | Additive diagnostics allowed when tests and registry are updated. |

## Verification Requirements

Backend contract changes should choose verification based on the touched
contract:

| Change Type | Required Verification |
|---|---|
| Model routing or env-var behavior | `python -m pytest tests/test_model_routing_config.py tests/test_model_routing_runtime.py tests/test_model_routing_escalation.py -q` |
| OpenAI key lazy access or preflight behavior | `python -m pytest tests/test_api_upstream_preflight.py -q` |
| Upstream-dependent run gate | `python -m pytest tests/test_upstream_dependent_run_bhc2.py tests/test_upstream_dependent_run_gate_presentation.py -q` |
| Prompt message adapter | Focused `build_messages`/prompt tests for the touched prompt surface. |
| GM output shape, route metadata, or provider error fallback | Model routing runtime/escalation tests plus focused API pipeline tests for affected callers. |
| Compatibility changes | Compatibility register review plus focused model routing/config tests. |
| Documentation-only registry update | Link checks, source-reference searches, and `git status --short` scope check confirming no backend behavior changed. |

## Reviewer Checklist

- Does every backend-facing contract have a canonical owner and implementation
  location?
- Is the authoritative implementation code, not this document?
- Are compatibility expectations explicit, especially `MODEL_NAME` and
  disabled-routing behavior?
- Are replay and provenance implications classified without adding new replay
  acceptance or provenance semantics?
- Are versioning expectations recorded for the touched contract?
- Are provider-specific details contained at the backend boundary?
- Did the change avoid backend implementation, routing, provider logic, replay
  schema, provenance, governance policy, and CI behavior changes unless the
  package explicitly approved them?

## Maintenance Rules

- Update this registry when backend-facing contract shape, ownership,
  compatibility, version status, or verification requirements change.
- Do not update this registry as a substitute for implementation tests.
- Do not retire backend compatibility from this registry; use the Compatibility
  Residue Register and an approved retirement package.
- Do not add provider-specific branching outside backend adapter/routing
  surfaces without updating this registry.
- Keep generated documentation strategy separate: this registry is manual until
  a future executable backend contract registry is approved.
