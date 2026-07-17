# AR-BH - Minimal Extensibility Contract Definition

## 1. Executive Summary

Confirmed fact: Campaign 4 has reduced the remaining long-term extensibility risk to explicit identity contracts, not runtime redesign. AR-BE identified stable boundaries with local seams around ruleset/backend identity. AR-BF certified Final Emission as a durable boundary. AR-BG confirmed that ruleset, backend, version, and provenance gaps are local contract gaps.

Strong inference: the minimum extensibility architecture is now definable as four small contracts:

1. a ruleset contract;
2. a backend contract;
3. a version bundle;
4. a provenance bundle.

These contracts should identify and describe active runtime capabilities. They should not implement alternate rulesets, backend adapters, public plugins, or provider-specific logic.

Minimum outcome:

- Alternate rulesets require stable ruleset identity, version, capability, selection, persistence, replay, and provenance fields.
- Additional providers require stable backend/provider identity, capability declaration, request/response boundaries, normalized errors, and routing/backend separation.
- Replay portability and save compatibility require a version bundle tying together runtime, ruleset, backend/provider/model, prompt policy, CTIR, persistence, Final Emission, replay, and provenance identities.
- Diagnostic trust requires a provenance bundle that survives where behavior evidence matters and stays diagnostics-only where it should not become replay acceptance.

Campaign 4 is ready for closeout after this contract definition. Remaining architecture is conditional on product direction: public UI/tooling facade, player-facing explanation redaction, or actual adapter/ruleset implementation decisions.

## 2. Ruleset Contract

### Required Fields

| Field | Required | Owner | Rationale |
|---|---:|---|---|
| `ruleset_id` | Yes | Ruleset contract owner/future registry | Permanent identity is required before saved state, replay, provenance, or external tools can distinguish current mechanics from alternate mechanics. |
| `ruleset_version` | Yes | Ruleset contract owner | Mechanical interpretation must be independently versioned from runtime, CTIR, and persistence envelopes. |
| `ruleset_family` | Yes | Ruleset contract owner | Stable family identity allows compatible minor versions or implementations to be grouped without implying identical code. |
| `capabilities` | Yes | Ruleset contract owner | Runtime and UI need to know supported mechanics such as combat, skills, social checks, exploration, spells, conditions, and downtime without probing modules. |
| `mechanics_contract_version` | Yes | Ruleset contract owner | The shape of ruleset-facing mechanics interfaces can evolve independently from a specific ruleset's game-content version. |
| `state_compatibility` | Yes | Ruleset contract owner plus persistence consumers | Saved campaigns must know whether active state can be loaded, migrated, or rejected. |
| `ctir_projection_compatibility` | Yes | CTIR owner consumes; ruleset contract declares | CTIR must know which bounded ruleset semantics can be projected without becoming a rules engine. |
| `provenance_label` | Yes | Ruleset contract owner | Replay and diagnostics need a human-readable but stable ruleset identity. |

Excluded from the minimum contract:

- dice formulas;
- full combat math;
- class/spell/item databases;
- UI labels beyond stable capability names;
- plugin packaging metadata;
- content pack discovery;
- simultaneous multiple active rulesets;
- provider/backend choices.

### Ownership

Confirmed fact: current domain mechanics live in domain modules such as `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/exploration.py`, `game/social.py`, and standardized result dataclasses in `game/models.py`.

The ruleset contract should be owned by a future ruleset contract/registry module, not by:

- `game/ctir.py`;
- `game/prompt_context.py`;
- `game/gm.py`;
- Final Emission modules;
- replay projection helpers;
- persistence envelope code.

Ruleset mechanics may produce authoritative domain outcomes, but the ruleset contract should only identify the active mechanical authority and its capabilities.

### Lifecycle

Minimum lifecycle:

1. Configure or select one active ruleset for a campaign/session/deployment.
2. Publish `ruleset_id`, `ruleset_version`, `ruleset_family`, and `capabilities` into runtime state metadata.
3. Include ruleset identity in saved-state compatibility checks.
4. Include ruleset identity in CTIR/provenance/replay surfaces where outcomes are interpreted.
5. Reject or migrate incompatible saved campaigns explicitly.

Strong inference: one active ruleset per campaign/session is the minimum architecture. Multiple concurrent rulesets inside one turn are out of scope until product evidence requires them.

### Persistence Relationship

The persistence envelope already owns document format versioning through `game/persistence_contract.py:PERSISTENCE_FORMAT_VERSION` and `docs/runtime_persistence_envelope.md`. Ruleset identity should live inside the persisted payload or payload metadata, not in the persistence envelope itself.

Reason: the envelope version says how the document is stored; the ruleset version says how gameplay semantics should be interpreted.

### Replay Relationship

Ruleset identity belongs in replay when replay observations depend on mechanical interpretation. It should be present as durable observation metadata, not as replay authority.

Replay may observe:

- `ruleset_id`;
- `ruleset_version`;
- relevant capability flags;
- mechanics contract version.

Replay must not use ruleset metadata to mutate live runtime behavior.

### Provenance Relationship

Ruleset provenance should permanently survive when a player-visible or replay-visible outcome depends on mechanics.

Minimum provenance fields:

- `ruleset_id`;
- `ruleset_version`;
- `mechanics_contract_version`;
- optional `ruleset_family`;
- optional capability subset used by the turn.

Diagnostics may carry richer fields, but replay portability only needs stable identity and relevant capability evidence.

## 3. Backend Contract

### Required Fields

| Field | Required | Owner | Rationale |
|---|---:|---|---|
| `backend_id` | Yes | Backend contract/adapter registry | Identifies the backend implementation boundary independently of provider and model. |
| `backend_version` | Yes | Backend contract/adapter registry | Adapter behavior can change independently of provider and selected model. |
| `provider_id` | Yes | Backend adapter | OpenAI, local inference, or another provider must be explicit before multi-provider replay/provenance is trustworthy. |
| `provider_api_family` | Yes | Backend adapter | Request/response semantics vary by API family; this should not leak into prompt or Final Emission code. |
| `capabilities` | Yes | Backend adapter | Required for architectural negotiation: structured output, streaming, tool calls, JSON mode, timeout/retry behavior, local inference, and safety/fallback limitations. |
| `request_contract_version` | Yes | Backend contract | Defines normalized inputs accepted from realization. |
| `response_contract_version` | Yes | Backend contract | Defines normalized candidate-output and metadata shape returned to realization. |
| `error_contract_version` | Yes | Backend contract | Normalized upstream errors must be stable across providers. |
| `model_id` | Yes | Model routing/backend response | Current `selected_model` is already material; it must remain distinct from provider/backend identity. |

Excluded from the minimum contract:

- provider SDK object types;
- API keys;
- transport clients;
- retry sleeps/backoff implementation;
- prompt text construction;
- Final Emission validation;
- provider-specific branching in gameplay code;
- generic plugin packaging.

### Ownership

Confirmed fact: `game/model_routing.py:ModelRouteDecision` and `resolve_model_route(...)` own deterministic model lane selection. `game/gm.py:call_gpt` currently imports `OpenAI`, calls `client.responses.create(...)`, attaches route metadata, and normalizes failures.

The backend contract should separate routing from provider invocation:

- `game/model_routing.py` owns route purpose, route family, and selected model lane.
- A backend adapter owns provider invocation and normalized response/error conversion.
- Realization/GM orchestration consumes backend responses.
- Prompt context remains a provider-neutral packager.
- Final Emission remains downstream legality/packaging.

### Routing Relationship

Routing answers: "Which model lane should this request use?"

Backend answers: "Which provider/adapter executes the request, with what capabilities and normalized result?"

The route decision should be an input to backend invocation. It should not contain provider SDK details.

Minimum normalized request boundary:

- messages or equivalent model input;
- route decision;
- purpose;
- retry attempt/retry reason;
- requested capabilities;
- correlation/turn id if available;
- prompt/policy version metadata if available.

Minimum normalized response boundary:

- candidate text or structured candidate payload;
- provider id;
- backend id/version;
- model id;
- capability mode actually used;
- normalized raw-output metadata needed for diagnostics;
- normalized error if failed;
- fallback/provenance hints, not final legality decisions.

### Provider Relationship

Provider identity must be explicit and distinct from model identity.

Evidence: current metadata records `selected_model`, `model_route_reason`, `model_route_family`, `model_route_purpose`, `model_retry_attempt`, `model_escalated`, and `model_escalation_trigger` in `game/gm.py:_attach_model_route_metadata`. It does not record provider/backend identity.

Strong inference: `provider_id` and `backend_id` are permanent architecture because the same model id can be served through different API families, and different providers may expose incompatible capabilities.

### Error Normalization

Confirmed fact: `game/gm.py:_classify_upstream_gpt_error(...)` already normalizes upstream errors into `failure_class`, `retryable`, `status_code`, `error_code`, and `message_excerpt`.

The backend contract should preserve that idea as a provider-neutral error boundary.

Minimum error fields:

- `failure_class`;
- `retryable`;
- `provider_status_code`;
- `provider_error_code`;
- `message_excerpt`;
- `backend_id`;
- `provider_id`;
- `model_id`;
- `capability_context`.

### Retry Ownership

Retry policy must remain split:

- model routing may identify retry escalation lanes;
- backend adapter may report retryable provider failures;
- runtime/realization orchestration decides whether a retry is attempted;
- Final Emission handles only finalized candidate/fallback legality and packaging.

Backend adapters should not silently rerun gameplay-level retries unless the retry is strictly transport-internal and provenance-preserving.

### Realization Ownership

Backend output is candidate expression only. It does not own:

- domain truth;
- CTIR;
- prompt policy;
- final legality;
- replay acceptance.

This matches AR-BD's invariant that GPT/model output owns expression, not truth.

## 4. Version Bundle Definition

The project should possess a unified architectural version bundle.

Strong inference: the bundle should be a small runtime-readable map, not a monolithic global schema that forces all surfaces to evolve together. Its purpose is to publish independent identities in one place for diagnostics, replay, save compatibility, and external tooling.

| Version Identity | Owner | Permanence | Consumers | Evolution Expectations |
|---|---|---|---|---|
| `runtime_contract_version` | Runtime/API contract owner | Permanent | diagnostics, external tooling, replay metadata | Changes when turn transaction or public runtime contract changes. |
| `ruleset_id` / `ruleset_version` | Ruleset contract owner | Permanent before alternate rulesets | persistence, CTIR, replay, provenance, UI/tooling | Evolves with mechanics semantics. |
| `mechanics_contract_version` | Ruleset contract owner | Permanent before alternate rulesets | ruleset adapters, tests, CTIR projection | Evolves when mechanics interface/result obligations change. |
| `backend_id` / `backend_version` | Backend adapter owner | Permanent before second provider | realization, diagnostics, replay/provenance | Evolves when adapter behavior changes. |
| `provider_id` / `provider_api_family` | Backend adapter owner | Permanent before second provider | diagnostics, replay/provenance | Evolves with provider/API family changes. |
| `model_id` | Model routing/backend response | Already necessary | diagnostics, provenance, route tests | Evolves per route/config. |
| `model_route_contract_version` | Model routing owner | Recommended permanent | realization, tests, diagnostics | Evolves if route decision shape changes. |
| `prompt_policy_version` | Prompt/response-policy owners | Recommended permanent | replay diagnostics, provenance, explanations | Evolves when shipped prompt/policy semantics change materially. |
| `ctir_version` | `game/ctir.py` | Already permanent | prompt context, tests, replay diagnostics | Existing `_CTIR_VERSION`; evolves when CTIR schema changes. |
| `persistence_format_version` | `game/persistence_contract.py` | Already permanent | storage, save/load, migrations | Existing `PERSISTENCE_FORMAT_VERSION`; evolves with envelope format. |
| `final_emission_schema_version` | Final Emission metadata owner | Recommended permanent | replay, diagnostics, external provenance | Evolves when FEM metadata/projection field contracts change. |
| `replay_observation_version` | Replay projection/governance owner | Recommended permanent | replay acceptance, regression tools | Evolves when protected observation shape changes. |
| `provenance_bundle_version` | Provenance contract owner | Permanent before portability | diagnostics, replay, public explanation redaction | Evolves when provenance field meanings change. |

Confirmed fact: CTIR and persistence already have explicit versions: `game/ctir.py:_CTIR_VERSION = 1` and `game/persistence_contract.py:PERSISTENCE_FORMAT_VERSION = 1`.

Missing evidence: no current unified version bundle module or field was found.

## 5. Provenance Bundle Definition

The provenance bundle should permanently preserve identity needed to explain "why this output exists" without becoming a behavior selector.

| Provenance Identity | Owner | Producer | Consumers | Replay Relationship | Diagnostics Relationship |
|---|---|---|---|---|---|
| `runtime_contract_version` | Runtime/API contract owner | runtime transaction | diagnostics, replay metadata, public facade | Include when replay portability matters | Always useful |
| `ruleset_id` | Ruleset contract owner | active ruleset selection | persistence, CTIR metadata, replay, diagnostics | Include for mechanics-dependent observations | Always useful for mechanics outcomes |
| `ruleset_version` | Ruleset contract owner | active ruleset selection | persistence, replay, diagnostics | Include | Always useful |
| `mechanics_contract_version` | Ruleset contract owner | active ruleset selection | adapter/tests/diagnostics | Include when outcome shape depends on it | Useful |
| `backend_id` | Backend adapter owner | backend invocation | realization diagnostics, replay metadata | Include for model-authored candidate provenance | Always useful |
| `backend_version` | Backend adapter owner | backend invocation | diagnostics, replay metadata | Include for portability | Always useful |
| `provider_id` | Backend adapter owner | backend invocation | diagnostics, replay metadata | Include for provider-dependent realization | Always useful |
| `provider_api_family` | Backend adapter owner | backend invocation | diagnostics | Conditional; include if response semantics affect replay interpretation | Useful |
| `model_id` | Model routing/backend response | model routing/backend | diagnostics, replay metadata | Include for model-authored candidate provenance | Existing model metadata should continue |
| `model_route_family` / `model_route_reason` | Model routing owner | `resolve_model_route` / GM metadata | diagnostics, replay metadata | Include when route explains candidate/fallback path | Existing fields should continue |
| `prompt_policy_version` | Prompt/policy owner | prompt context/response policy | diagnostics, explanation, replay metadata | Conditional unless replay validates prompt-policy behavior | Useful |
| `ctir_version` | CTIR owner | CTIR build | prompt context, replay diagnostics | Include because CTIR meaning shape affects downstream | Already in CTIR root |
| `realization_fallback_family` | Realization provenance owner | realization/GM/fallback paths | Final Emission, replay projection, diagnostics | Include when fallback is observed | Already governed by `game/realization_provenance.py` |
| `fallback_family_used` | Diegetic/runtime fallback owner | fallback content/selectors | replay projection, diagnostics | Include when diegetic fallback taxonomy exists | Must remain distinct from realization provenance |
| `final_emission_schema_version` | Final Emission metadata owner | Final Emission meta packaging | replay, diagnostics | Recommended include | Useful |
| `final_emission_mutation_lineage` | Final Emission lineage owner | Final Emission/meta/projection | diagnostics, replay projection | Include where replay observes mutation lineage | Existing key: `FINAL_EMISSION_MUTATION_LINEAGE_KEY` |
| `persistence_format_version` | Persistence contract owner | persistence envelope | storage/load/migration | Usually outside turn replay; include in saved replay package metadata | Already envelope-level |
| `replay_observation_version` | Replay governance/projection owner | replay projection | replay acceptance tools | Include in replay artifacts | Essential for portability |

Confirmed fact: `game/realization_provenance.py` distinguishes governed `realization_fallback_family` from diegetic `fallback_family_used`. `game/final_emission_replay_projection.py` states that runtime lineage projection must not select fallbacks, mutate output, or stamp write-time FEM.

Strong inference: provenance fields should be split into durable replay fields and diagnostics-only enrichments. Durable fields identify behavior-affecting origins. Diagnostics-only fields can include provider raw details, message excerpts, capability details, and debug notes.

## 6. Contract Placement Matrix

| Contract | Permanent Architectural Owner | Prohibited Owners | Dependency Direction | Implementation Expectations |
|---|---|---|---|---|
| Ruleset identity | Future ruleset contract/registry | CTIR, prompt context, GM/backend, Final Emission, replay | Runtime publishes active identity; domain mechanics consume/select; CTIR/replay observe | Add explicit fields before alternate ruleset implementation. |
| Ruleset capabilities | Ruleset contract/registry | UI-only code, prompt text, Final Emission | Ruleset declares; runtime/UI/replay consume | Keep capability names stable and coarse. |
| Ruleset persistence compatibility | Ruleset contract plus persistence consumers | Persistence envelope format owner alone | Persistence validates payload compatibility using ruleset metadata | Do not put mechanics semantics in envelope version. |
| Backend identity | Backend adapter contract | Model routing alone, prompt context, Final Emission | Realization invokes backend; diagnostics/replay observe | Extract before adding second provider. |
| Provider identity | Backend adapter | Model routing alone, config-only globals | Adapter produces; provenance consumes | Do not infer provider from model name. |
| Model routing | `game/model_routing.py` | Backend adapter, prompt context, Final Emission | Routing decision feeds backend invocation | Preserve deterministic `ModelRouteDecision` role. |
| Backend request/response | Backend contract/adapter | CTIR, Final Emission, replay | Prompt/realization sends normalized request; backend returns normalized response | Keep provider SDK details inside adapter. |
| Backend error contract | Backend contract/adapter | Final Emission, replay, prompt context | Adapter normalizes; realization decides fallback/retry | Preserve existing failure-class idea. |
| Version bundle | Runtime/version contract owner with surface owners | Any single subsystem as sole authority over all versions | Each owner contributes identity; runtime packages | Do not force all versions to increment together. |
| Provenance bundle | Provenance contract owner plus producing owners | Replay as behavior owner, Final Emission as sole provenance owner | Producers stamp; replay/diagnostics observe | Split durable replay fields from diagnostics-only fields. |
| CTIR version | `game/ctir.py` | Ruleset/backend contracts | CTIR publishes; prompt/replay consume | Existing version remains independent. |
| Persistence version | `game/persistence_contract.py` | Ruleset contract | Envelope publishes; storage consumes | Existing envelope version remains format-only. |
| Final Emission schema/version | Final Emission metadata/projection owner | Backend/ruleset/prompt | Final Emission stamps/packages; replay observes | Add only if external/replay portability needs stable FEM schema identity. |
| Replay observation version | Replay governance/projection owner | Runtime/live behavior modules | Replay observes finalized surfaces | Never feed replay version back into live behavior. |

Placement rejections:

- Ruleset identity must never be inferred from prompt text or model behavior.
- Backend/provider identity must never be inferred from `selected_model` alone.
- CTIR must not become a ruleset registry.
- Prompt context must not become a backend adapter.
- Final Emission must not choose ruleset mechanics or provider routing.
- Persistence envelope version must not encode gameplay semantics.
- Replay must not become runtime selection logic.

## 7. Architectural Readiness Assessment

### Remaining Architecture

Mandatory architectural reconciliation for Campaign 4: complete.

The minimum ruleset, backend, version, and provenance contracts can be stated without reopening:

- runtime orchestration;
- state authority;
- CTIR;
- prompt context;
- Final Emission;
- persistence envelopes;
- replay governance.

Conditional remaining architecture:

- public command/query/event facade if external tooling or hosted APIs become product scope;
- player-facing explanation/redaction schema if provenance becomes player-visible UX;
- migration policy details if long-lived saved campaigns across ruleset versions become product scope.

### Remaining Implementation

Implementation remains before actual expansion:

- create a ruleset contract/registry module;
- publish active ruleset identity in runtime/session metadata;
- add ruleset compatibility checks for persistence/replay;
- extract a backend adapter boundary;
- create the first OpenAI adapter behind that boundary;
- add deterministic fake backend tests;
- add version/provenance bundle emission.

### Remaining Documentation

Documentation remains:

- ruleset contract decision record;
- backend adapter decision record;
- version/provenance field registry;
- migration/replay compatibility notes when implementation begins.

### Remaining Governance

Governance remains:

- direct-owner tests for new contract modules;
- drift guards preventing provider logic from spreading through `game/gm.py`, prompt context, or Final Emission;
- replay/provenance field compatibility tests;
- ownership ledger updates when contracts are implemented.

### Expansion Enablement

Completion of these contracts would fully enable architectural readiness for:

- alternate ruleset implementation;
- additional AI providers;
- local inference backend implementation;
- replay portability planning;
- long-term save compatibility planning.

It would not by itself implement those capabilities.

## 8. Recommended Next Cycle

Recommended next cycle: **AR-BI - Campaign 4 Closeout and Implementation Handoff**.

Reason: no additional mandatory Boundary Reconciliation cycle remains for the Campaign 4 objective. AR-BE stabilized the boundary inventory, AR-BF certified Final Emission, AR-BG inventoried extensibility identity gaps, and AR-BH defines the minimum contracts required before future expansion.

AR-BI should close Campaign 4 by producing:

- a final Campaign 4 synthesis;
- the authoritative list of durable boundaries;
- the minimum implementation handoff queue;
- the optional future architecture queue;
- the files required for any future implementation campaign.

Conditional future cycle after closeout: public UI/tooling facade discovery, only if external tooling or hosted/public API work becomes the selected product direction.

## 9. Files Required For External Review

### Required

- `AR-BH_minimal_extensibility_contract_definition.md`
- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-BF_final_emission_boundary_validation.md`
- `AR-BE_boundary_reconciliation_discovery_and_evidence_inventory.md`
- `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
- `AR-AI_final_vision_compatibility_closeout.md`
- `docs/architecture_ownership_ledger.md`
- `docs/runtime_persistence_envelope.md`
- `game/model_routing.py`
- `game/gm.py`
- `game/config.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/noncombat_resolution.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`
- `game/persistence_contract.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_ctir_schema.py`
- `tests/test_noncombat_resolution.py`
- `tests/test_runtime_persistence_regression_suite_obj14.py`
- `tests/test_realization_provenance.py`
- `tests/test_golden_replay_projection_fallback_integration.py`
- `tests/test_final_emission_meta.py`

### Conditional

- `game/prompt_context.py` - required if prompt-policy versioning details are reviewed.
- `game/models.py` - required if mechanics result-shape obligations are reviewed.
- `game/combat.py` and `game/skill_checks.py` - required if ruleset mechanics boundaries are challenged.
- `tests/helpers/golden_replay_projection.py` - required if replay observation versioning is in scope.
- `game/api.py` - required if runtime publication or public facade placement is in scope.
- `game/storage.py` - required if saved-state migration behavior is in scope.

### Not Needed Unless Requested

- Static frontend files.
- Generic plugin scaffolding.
- Live provider credentials or network traces.
- Full content/data packs.
- UI mode tests, unless the next cycle expands into public tooling facade work.
- Importer-specific files, unless ruleset/content packaging becomes the immediate product scope.

## Closing Finding

Confirmed fact: current repository evidence supports explicit local extensibility contracts and does not support a need for runtime redesign.

Strong inference: Campaign 4 is ready for closeout. The next useful work is either AR-BI closeout or implementation of the contracts defined here, depending on whether the user wants one more synthesis artifact before code work.
