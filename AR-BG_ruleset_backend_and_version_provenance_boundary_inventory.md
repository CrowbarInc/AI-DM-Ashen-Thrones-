# AR-BG - Ruleset, Backend, and Version-Provenance Boundary Inventory

## 1. Executive Summary

This report inventories the long-term extensibility boundaries around rulesets, AI backends, version identity, and provenance identity.

Repository-grounded conclusion: the current architecture is ready for a minimal extensibility contract layer, but not ready for alternate rulesets or additional AI providers by simple configuration alone.

The runtime spine should remain unchanged:

1. Runtime transaction and domain simulation establish truth.
2. CTIR captures resolved-turn meaning after authoritative mutation.
3. Prompt context packages authoritative state and CTIR into model-facing context.
4. Realization/model I/O produces candidate expression.
5. Final Emission validates, repairs, packages, and seals.
6. Persistence, logs, replay, evidence, and governance observe finalized output.

The required next work is local boundary clarification, not architectural rework. The missing seams are:

- ruleset identity, version, selection, and adapter/contract ownership;
- provider-neutral backend identity and adapter boundary;
- a version/provenance bundle spanning runtime, ruleset, backend/model, prompt/policy, CTIR, persistence, and Final Emission schema surfaces;
- a capability/version facade before external tooling or hosted integrations consume internals.

No evidence supports reopening CTIR, state authority, Final Emission, persistence envelopes, or replay governance as part of this cycle.

## 2. Ruleset Boundary Assessment

### Current Stable Foundation

The repository already separates a substantial amount of mechanical truth from narration:

- `game/combat.py` owns combat mechanics and returns canonical `CombatEngineResult` dictionaries.
- `game/skill_checks.py` resolves deterministic skill checks and check-trigger decisions.
- `game/exploration.py` and `game/social.py` own domain-specific non-combat resolution.
- `game/noncombat_resolution.py` classifies non-combat action kinds, delegates to exploration/social owners, normalizes a bounded contract, and carries `NONCOMBAT_FRAMEWORK_VERSION = "2026.04.noncombat.v1"`.
- `game/models.py` defines standardized engine result dataclasses for exploration, combat, and social resolution.
- `game/ctir.py` consumes bounded resolution payloads and explicitly rejects prose-like authority as CTIR truth.
- `game/prompt_context.py` consumes CTIR and shipped contracts; it does not adjudicate mechanics.
- `game/final_emission_gate.py` and related Final Emission modules validate and seal player-facing output without owning domain simulation.

This is a credible single-ruleset architecture. Domain mechanics are not primarily encoded in prompts or GPT output.

### Existing Ruleset-Like Identity

Ruleset-adjacent versions exist locally:

- `game/noncombat_resolution.py` exposes `NONCOMBAT_FRAMEWORK_VERSION`.
- `game/ctir.py` exposes `_CTIR_VERSION` and `ctir_version()`.
- `game/persistence_contract.py` exposes `PERSISTENCE_FORMAT_VERSION`.
- Prompt/narration planning carries local plan metadata and versions inside the prompt-context seam.
- Final Emission and replay projection carry governed provenance fields and runtime lineage vocabulary.

These are subsystem versions, not an active global ruleset identity.

### Missing Ruleset Boundary

No repository evidence was found for:

- a ruleset registry;
- a ruleset package/manifest;
- an active ruleset selector;
- a ruleset id/version stored in session, CTIR, replay, or provenance;
- a ruleset-owned mechanics protocol;
- tests using a fake or second ruleset.

AR-AG and AR-AI already classified modular ruleset support as partially supported for exactly this reason: domain modules, standardized engine results, state authority, CTIR, and non-combat contracts provide a foundation, but the identity/selection/adapter contract is absent.

### Correct Boundary Placement

Ruleset ownership should sit below CTIR and prompt construction and above individual mechanics modules only where a contract is needed.

The runtime chassis should own:

- active ruleset identity publication;
- ruleset selection for a campaign/session/deployment;
- compatibility checks between saved state, CTIR/provenance/replay, and the active ruleset;
- provenance packaging of active ruleset id/version/capabilities.

The ruleset should own:

- mechanical semantics, such as combat math, action legality, skill/check logic, spell/effect interpretation, and ruleset-specific character sheet meanings;
- ruleset-specific content validation and data interpretation;
- ruleset capability declaration.

The ruleset should not own:

- runtime transaction order;
- CTIR lifecycle;
- prompt assembly policy;
- Final Emission legality and packaging;
- persistence envelope mechanics;
- replay acceptance authority.

### Risk Classification

Current single-ruleset work is low risk if it stays inside existing domain owners.

Alternate-ruleset work is medium-to-high risk until a minimal ruleset identity/contract exists, because scattered conditionals across `combat.py`, `skill_checks.py`, `noncombat_resolution.py`, prompt context, CTIR, and persistence would make provenance and replay ambiguous.

## 3. AI Backend Boundary Assessment

### Current Stable Foundation

`game/model_routing.py` already owns deterministic model route selection:

- `ModelRouteDecision` carries `selected_model`, `route_reason`, `route_family`, and `escalation_allowed`.
- `resolve_model_route(...)` is deterministic and keyed by explicit route purpose, strict-social pressure, retry escalation, and high-precision forcing.
- `game/config.py` preserves legacy `MODEL_NAME` while adding `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, `RETRY_ESCALATION_MODEL_NAME`, and `ENABLE_MODEL_ROUTING`.
- `tests/test_model_routing_config.py` verifies route-related env compatibility.
- `tests/test_model_routing_runtime.py` verifies routed selected models flow through `call_gpt`, route metadata is attached, and route metadata can be preserved downstream.

`game/gm.py` also contains useful backend-adjacent foundations:

- `_classify_upstream_gpt_error(...)` normalizes upstream failure class, retryability, status code, error code, and message excerpt.
- `_attach_model_route_metadata(...)` stamps selected model, route reason, route family, purpose, retry attempt, escalation flag, and escalation trigger.
- `call_gpt(...)` preserves gameplay by returning schema-shaped fallback output on upstream failure.
- fallback metadata uses `attach_realization_fallback_family(..., GPT_BUDGET_OR_PROVIDER_FAILURE)` for provider/budget failure provenance.

### Current Provider Coupling

The live provider implementation remains OpenAI-specific:

- `game/gm.py:call_gpt` imports `OpenAI` directly.
- It constructs `OpenAI(api_key=get_openai_api_key())`.
- It calls `client.responses.create(model=route.selected_model, input=messages)`.
- It reads `resp.output_text`.
- `game/config.py` requires `OPENAI_API_KEY`.

That is acceptable for a single-provider runtime. It is the wrong place to branch multiple providers.

### Missing Backend Boundary

No repository evidence was found for:

- provider-neutral backend protocol;
- backend registry;
- backend/provider id distinct from selected model;
- capability declaration for streaming, tool calls, structured output, JSON mode, timeout behavior, local inference, or retry semantics;
- deterministic fake backend adapter as a first-class runtime backend;
- provider/backend version fields in replay/provenance.

The fake-client model routing tests prove `call_gpt` can be tested without live OpenAI calls, but they do not create a backend abstraction.

### Correct Boundary Placement

Backend ownership should be separated from model routing:

- `game/model_routing.py` should continue to decide route purpose and selected model lane.
- A backend adapter boundary should own provider invocation, response normalization, capability declaration, and provider-specific error mapping.
- `game/gm.py` or a successor realization module should consume a normalized backend response, not branch directly on provider details.
- Prompt context should remain provider-neutral; it packages messages/contracts, not provider APIs.
- Final Emission should remain downstream; it validates sealed output, not backend behavior.

### Risk Classification

Adding more OpenAI model lanes is low risk under existing routing.

Adding a second provider or local inference backend is medium-to-high risk unless a backend adapter exists first. Without it, provider behavior would leak into `call_gpt`, fallback handling, route metadata, replay/provenance fields, and tests.

## 4. Version Identity Matrix

| Identity Surface | Current Repository Evidence | Current Owner | Gap | Needed Before Expansion |
|---|---|---|---|---|
| Runtime architecture version | Campaign reports and ownership docs define architecture, but no executable runtime-architecture id | Governance/docs | No runtime-readable architecture/capability version | Conditional; useful before public facade or hosted integrations |
| Ruleset id | No active global ruleset id found | Missing | Cannot distinguish current PF1e-inspired mechanics from future rulesets | Required before alternate rulesets |
| Ruleset version | `NONCOMBAT_FRAMEWORK_VERSION` exists only for non-combat; no global ruleset version | Missing | Combat/skill/social/exploration versions are not unified | Required before alternate rulesets or migrated saved campaigns |
| Ruleset capabilities | Domain modules imply capabilities; no declared capability bundle | Missing | External tooling/replay cannot know supported mechanics | Required before ruleset selection or public tooling |
| Backend provider id | OpenAI is implicit via `game.gm.call_gpt` and `OPENAI_API_KEY` | Missing/provider call site | Selected model is recorded, provider is not | Required before second provider |
| Backend adapter version | No backend adapter exists | Missing | Backend behavior cannot be versioned separately from `game.gm` | Required before second provider/local backend |
| Model route identity | `ModelRouteDecision`; route metadata in `game.gm` | `game/model_routing.py` and `game/gm.py` metadata packaging | Good for model lane; not provider-neutral | Present, should be carried into provenance bundle |
| Prompt/policy version | Prompt context exports policy objects and plan versions; no single prompt-policy bundle id | Prompt/policy modules | Policy evolution is distributed | Recommended before broad replay/provenance or public explanations |
| CTIR schema version | `_CTIR_VERSION = 1`; `ctir_version()`; CTIR root `version` | `game/ctir.py` | Strong local version; not tied to global version bundle | Present, include in provenance/version bundle |
| Non-combat contract version | `NONCOMBAT_FRAMEWORK_VERSION` | `game/noncombat_resolution.py` | Local only, not a ruleset id | Present, include under ruleset/mechanics contract |
| Persistence envelope version | `PERSISTENCE_FORMAT_VERSION = 1`; validation rejects unsupported versions | `game/persistence_contract.py` | Strong envelope version; payload semantic versions remain feature-owned | Present, include in saved-state compatibility checks |
| Final Emission schema/version | FEM metadata/projection fields exist; no single FEM schema version found | Final Emission metadata/projection owners | Field stability governed by tests/docs, not a single schema id | Recommended before public replay/provenance consumers |
| Replay acceptance schema | Protected replay projection/test helpers and governance docs exist | Test/governance replay owners | Acceptance schema is protected but not unified with runtime version bundle | Recommended before external replay APIs |
| Provenance vocabulary version | Realization fallback family and runtime lineage vocabulary exist | `game/realization_provenance.py`, `game/final_emission_replay_projection.py`, telemetry vocab owners | No global provenance bundle id | Required before player-facing explanation or multi-backend/ruleset provenance |

## 5. Provenance Ownership Matrix

| Provenance Kind | Current Evidence | Owner | Boundary Rule |
|---|---|---|---|
| CTIR builder provenance | `game/ctir.py:normalize_provenance` records builder source, source modules, signals, retry-safe flags, and extras | CTIR owner | Explains CTIR construction; does not select mechanics or prompt behavior |
| CTIR runtime attachment | `game/ctir_runtime.py:build_runtime_ctir_for_narration` sets source modules to `game.ctir_runtime` and `game.api` | CTIR runtime/API | Placement provenance only; not a substitute for ruleset identity |
| Model route provenance | `game/gm.py:_attach_model_route_metadata` stamps selected model, route reason, family, purpose, retry attempt, and escalation data | Model routing plus GM metadata packaging | Records model lane; does not identify provider/backend contract |
| Upstream/provider failure provenance | `game/gm.py:call_gpt` returns structured fallback metadata and realization fallback family for provider/budget failure | GM realization path plus realization provenance helper | Good failure evidence; provider id remains implicit |
| Realization fallback family | `game/realization_provenance.py` distinguishes governed `realization_fallback_family` from diegetic `fallback_family_used` | Realization provenance owner | Must not collapse runtime and replay vocabularies |
| Final Emission lineage | `game/final_emission_replay_projection.py` derives runtime lineage from finalized FEM and explicitly must not mutate output or select fallback | Final Emission replay/runtime-lineage projection owner | Read-side diagnostic projection only |
| Fallback content/selection ownership | Final Emission replay projection preserves split selection/content/provenance ownership fields | Final Emission/provenance projection owners | Prevents single-owner false attribution |
| Persistence envelope provenance | `game/persistence_contract.py` stores persistence version, document kind, saved_at, and optional integrity hash | Persistence contract owner | Document integrity/version; not gameplay provenance |
| Ruleset provenance | No active global ruleset provenance found | Missing | Required before alternate rulesets |
| Backend/provider provenance | Selected model exists; provider/backend identity absent | Missing | Required before second provider |
| Prompt/policy provenance | Prompt context carries policy objects and plan metadata; no unified prompt-policy version | Prompt/policy owners | Recommended before public explanations and replay portability |

## 6. Dependency Boundary Map

The durable dependency direction is:

```text
Ruleset/domain mechanics
  -> authoritative resolution/state mutation
  -> CTIR resolved-turn meaning
  -> prompt/context packaging
  -> backend/model realization
  -> Final Emission legality/packaging
  -> persistence/log/response
  -> replay/evidence/governance/read-side projection
```

Allowed dependencies:

- CTIR may consume bounded outputs from domain mechanics and non-combat contracts.
- Prompt context may consume CTIR, visibility, response policy, and shipped plan bundles.
- Backend realization may consume prompt messages/contracts and return candidate output.
- Final Emission may consume candidate output, authoritative context, validators, repairs, sanitizer, fallback metadata, and provenance packagers.
- Persistence/replay/evidence may observe finalized runtime outputs.

Disallowed or high-risk dependencies:

- Rulesets should not call prompt context or Final Emission to decide mechanics.
- Prompt context should not infer mechanical outcomes when CTIR is present.
- Backend adapters should not mutate authoritative state.
- Final Emission should not become a ruleset/mechanics authority.
- Replay projection should not feed behavior back into live runtime.
- Provider-specific branching should not spread across prompt context, Final Emission, persistence, and replay.
- Ruleset-specific branching should not scatter through `game.api`, CTIR, prompt context, and Final Emission without an active ruleset contract.

## 7. Future Expansion Assessment

### Alternate Rulesets

Architectural readiness: partial.

Supported foundations:

- domain-owned mechanics;
- standardized engine result shapes;
- CTIR as a resolved-turn meaning boundary;
- state authority separation;
- non-combat versioned contract;
- persistence envelope versioning;
- replay/provenance observation.

Missing prerequisites:

- active ruleset id and version;
- ruleset selection lifecycle;
- ruleset capability bundle;
- ruleset-owned mechanics contract;
- provenance/replay/session fields for active ruleset;
- fake or second ruleset tests.

Assessment: feasible after local contract work. Do not implement by adding ad hoc ruleset conditionals to existing mechanics and prompt code.

### Additional AI Providers

Architectural readiness: partial.

Supported foundations:

- deterministic model routing;
- model route metadata;
- upstream error normalization;
- safe schema-shaped fallback on provider failure;
- fake-client tests around the current call path.

Missing prerequisites:

- provider-neutral backend request/response protocol;
- provider/backend id and adapter version;
- backend capability declaration;
- normalized response/error surface;
- deterministic fake backend adapter;
- provenance fields for provider/backend/model/capabilities.

Assessment: feasible after extracting a backend adapter. Do not add provider branching inside `game.gm.call_gpt`.

### Versioned Public Tooling and Hosted APIs

Architectural readiness: conditional.

Supported foundations:

- internal FastAPI/browser UI;
- UI mode/channel projection;
- state authority;
- persistence envelopes;
- final sealed public/author/debug payload separation.

Missing prerequisites:

- public command/query facade;
- stable API/event schemas;
- capability/version bundle;
- redaction model for provenance/explanations;
- ruleset/backend identity if external tools need compatibility guarantees.

Assessment: should follow the version/provenance contract work if external integrations are planned.

### Generic Plugin System

Architectural readiness: not indicated as necessary.

No evidence suggests a generic plugin architecture should be built before concrete ruleset/backend/public-facade contracts. Current repository evidence supports small explicit adapters first.

## 8. Architectural Readiness Assessment

### Ready Now

- Continue current-ruleset mechanics inside existing domain owners.
- Add bounded feature lanes that follow the established pattern: domain owner, state authority, CTIR projection, prompt adaptation, Final Emission preservation, replay/provenance tests.
- Add more configured OpenAI model lanes through `game/model_routing.py` if they preserve the current metadata contract.
- Extend persistence envelope use for new runtime documents where needed.

### Ready After Minimal Contract Work

- Alternate ruleset implementation.
- Second AI provider or local inference backend.
- Public/external tooling API.
- Player-facing provenance/explanation UI.
- Versioned replay/provenance export.

### Not Recommended Yet

- Generic plugin framework.
- Multi-ruleset execution inside one turn.
- Provider logic branching inside `call_gpt`.
- Public external consumers reading raw internal API dictionaries as a stable contract.
- Collapsing Final Emission, replay, realization, and fallback provenance vocabularies into one field.

### Bottom Line

The architecture is not blocked by missing fundamentals. It is blocked, for these specific expansion classes, by missing identity and adapter contracts.

That is a good failure mode: the required work is small, explicit, and local compared with a runtime redesign.

## 9. Recommended Next Cycle

Recommended next cycle: **AR-BH - Minimal Extensibility Contract Definition: Ruleset, Backend, and Version-Provenance Bundle**.

Why this follows naturally:

- AR-BF validated Final Emission as stable enough not to block upstream extensibility work.
- AR-BG confirms ruleset/backend expansion is structurally viable but lacks explicit identity, adapter, and provenance contracts.
- A minimal contract definition cycle should decide contract fields and ownership without implementing an alternate ruleset, alternate provider, or plugin system.

Expected AR-BH output:

- a minimal ruleset identity/version/capability contract;
- a provider-neutral backend adapter contract and OpenAI adapter placement decision;
- a version/provenance bundle shape covering runtime, ruleset, backend/provider/model, prompt/policy, CTIR, persistence, Final Emission, and replay surfaces;
- explicit non-goals around plugins, simultaneous multi-ruleset execution, and public hosted APIs unless product scope requires them.

Conditional follow-on after AR-BH: **AR-BI - Public UI, Tooling, and Adapter Facade Boundary Discovery**, if external tooling, hosted APIs, or third-party integrations remain planned.

## 10. Files Required For External Review

### Required

- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-BF_final_emission_boundary_validation.md`
- `AR-BE_boundary_reconciliation_discovery_and_evidence_inventory.md`
- `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
- `AR-AI_final_vision_compatibility_closeout.md`
- `AR-AH_final_vision_compatibility_assessment.md`
- `AR-AG_final_vision_compatibility_discovery.md`
- `docs/architecture_ownership_ledger.md`
- `docs/ctir_prompt_adapter_architecture.md`
- `docs/runtime_persistence_envelope.md`
- `game/model_routing.py`
- `game/gm.py`
- `game/config.py`
- `game/prompt_context.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/models.py`
- `game/combat.py`
- `game/skill_checks.py`
- `game/noncombat_resolution.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`
- `game/persistence_contract.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_ctir_schema.py`
- `tests/test_ctir_snapshot_examples.py`
- `tests/test_noncombat_resolution.py`
- `tests/test_runtime_persistence_regression_suite_obj14.py`

### Conditional

- `game/api.py` - required if AR-BH or AR-BI decides where active ruleset/backend/version identity is attached to the turn/session response.
- `game/storage.py` - required if saved-state compatibility and migration behavior are in scope.
- `game/final_emission_meta.py` - required if FEM schema/version fields are defined.
- `game/runtime_lineage_telemetry.py` - required if runtime-lineage provenance versioning is defined.
- `tests/helpers/golden_replay_projection.py` - required if replay acceptance schema/version fields are changed.
- `tests/test_prompt_context_ctir_consumption.py` and related prompt-context tests - required if prompt-policy versioning is added.
- UI/backend integration tests - required only if the next cycle expands into public UI/tooling facade work.

### Not Needed

- Static frontend files, unless public facade or capability display becomes part of the next cycle.
- Content lint templates, unless ruleset-specific content packaging is explicitly in scope.
- Generic plugin scaffolding, because no plugin architecture should be designed from this inventory alone.
- Live provider credentials or network calls, because backend boundary assessment can be grounded in code and tests.

## Closing Finding

AR-BG validates the same architectural posture reached by AR-BE and AR-BF: the runtime architecture is durable, but the next expansion layer needs explicit identity.

Rulesets need identity/version/capability before alternates.

Backends need provider/adapter/capability before a second provider.

Provenance needs a version bundle before replay, explanation, public tooling, or multi-provider/multi-ruleset behavior can be trusted as portable evidence.

None of that requires rewriting the runtime spine.
