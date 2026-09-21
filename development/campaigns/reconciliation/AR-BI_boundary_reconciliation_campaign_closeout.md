# AR-BI - Boundary Reconciliation Campaign Closeout

## 1. Executive Summary

Confirmed fact: Campaign 4 Boundary Reconciliation is complete.

Campaign 4 established that the repository's recovered architecture is internally consistent, durable, and ready to support implementation without additional mandatory architectural reconciliation. The campaign did not find a need to redesign runtime orchestration, state authority, CTIR, prompt adaptation, realization, Final Emission, persistence, replay, diagnostics, or governance.

The campaign's central closeout doctrine is:

```text
Player intent
  -> runtime transaction
  -> domain simulation and state authority
  -> CTIR resolved-turn meaning
  -> prompt/adaptation packaging
  -> realization/model expression
  -> Final Emission legality and packaging
  -> persistence/log/response
  -> replay/projection/evidence/diagnostics
  -> governance
```

Strong inference: future work should now move from Boundary Reconciliation to implementation-focused campaigns. Remaining work is implementation, documentation, governance, or product choice. The only remaining architecture is optional and conditional on future product scope, such as public tooling APIs, player-facing explanation/redaction, or hosted/external integrations.

No additional Boundary Reconciliation cycle is required.

## 2. Campaign Objective Assessment

| Objective | Status | Evidence | Closeout Finding |
|---|---|---|---|
| Durable subsystem boundaries | Complete | AR-BE stable boundary inventory; AR-BD concept map; `docs/architecture_ownership_ledger.md` | Permanent owners and exclusions are now documented. |
| Permanent ownership | Complete | Ownership ledger rows for response policy, prompt contracts, CTIR, Final Emission, metadata, telemetry, turn packet, state authority, and test governance | Ownership is direct-owner based, with downstream/compatibility consumers explicitly demoted from co-ownership. |
| Dependency direction | Complete | AR-BD dependency map; AR-BG dependency boundary map; AR-BH placement matrix | Runtime truth flows forward; replay/governance observe after runtime. |
| Extensibility boundaries | Complete | AR-BG inventory; AR-BH contract definition | Ruleset/backend/version/provenance gaps are contract and implementation work, not runtime redesign. |
| Implementation separation | Complete | AR-BE pressure-point classification; AR-BH implementation/documentation/governance separation | Current architecture can be implemented through local contracts/adapters without reopening core boundaries. |
| Governance boundaries | Complete | Ownership ledger; AR-BD governance doctrine; AR-BF drift-watch framing | Governance declares, watches, and tests; it does not execute gameplay. |
| Final Emission ownership | Complete | AR-BF; `game/final_emission_gate.py`, `game/final_emission_runtime.py`, `game/final_emission_boundary_contract.py`, `game/final_emission_meta.py`, tests cited by AR-BF | Final Emission is durable as last-mile legality, selection, packaging, FEM/meta, terminal exception, sealing, and traceability. |
| Long-term extensibility contracts | Complete for architecture | AR-BG and AR-BH | Minimum contracts are defined; implementation remains. |

Overall: Campaign 4 met its objective.

## 3. Permanent Architectural Doctrine

1. A turn has one runtime transaction spine.
2. Domain simulation owns game truth.
3. State authority governs which owners may mutate/read domains.
4. CTIR owns resolved-turn meaning after authoritative mutation and before prompt construction.
5. Prompt/adaptation packages approved truth, CTIR, visibility, response contracts, and plan context for expression.
6. Realization/model I/O produces candidate expression and realization provenance; it does not own truth.
7. Model routing chooses model lanes; backend/provider invocation should be an adapter responsibility before multi-provider expansion.
8. Final Emission owns last-mile legality, selection, packaging, metadata/FEM, terminal exceptions, sealing, and traceability.
9. Validators predicate; repairs are bounded; sanitizers strip/package/drop; fallback has split content/selection/application/provenance/observer ownership.
10. Persistence stores runtime documents and envelopes; transaction timing belongs to runtime/API orchestration.
11. Replay, projection, evidence, diagnostics, and telemetry observe finalized runtime behavior.
12. Provenance records behavior and ownership paths; it does not select behavior.
13. Governance declares doctrine, classifies evidence, assigns owners, and watches drift; it does not execute gameplay.
14. Compatibility residue is not co-equal ownership unless explicitly promoted by current doctrine.
15. Future feature lanes should follow the pattern: domain owner, state authority, CTIR/projection, prompt adaptation, Final Emission preservation, replay/provenance evidence, focused tests.

Confirmed fact: AR-AI already stated that domain modules own simulation truth, `game.api` owns transaction order, CTIR owns resolved-turn meaning, prompt construction adapts authoritative state, Final Emission owns last-mile legality/packaging, persistence stores runtime documents, and replay/evidence observes runtime output. Campaign 4 validated and refined that doctrine.

## 4. Permanent Boundary Inventory

| Subsystem | Ownership | Explicit Exclusions | Stability | Evidence |
|---|---|---|---|---|
| Runtime transaction | Coordinates turn order from request through mutation, CTIR, realization, Final Emission, persistence, logs, and response | Domain mechanics, prompt semantics, replay acceptance, storage mechanics | Stable | AR-BD, AR-AI, AR-BG |
| Domain simulation | Resolves authoritative game outcomes through domain modules | Prompt/model truth, Final Emission text mutation, replay/governance decisions | Stable | `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/models.py`, AR-BG |
| State authority | Domain registry, read matrix, write allow-list, mutation trace helpers | Persistence logic, prompt assembly, CTIR semantics, emission repairs | Stable | `game/state_authority.py`; ownership ledger |
| Ruleset identity | Future ruleset id/version/family/capabilities/mechanics contract | Plugin framework, prompt inference, provider/backend choices, simultaneous multi-ruleset execution | Architecturally defined; implementation pending | AR-BG, AR-BH |
| CTIR | Bounded resolved-turn meaning, schema version, provenance normalization, runtime attach/stamp | Full state, prompt prose, model instructions, domain mechanics, final legality | Stable | `game/ctir.py`, `game/ctir_runtime.py`, tests cited in AR-BG/AR-BH |
| Prompt/adaptation | Model-facing context packaging from CTIR, authoritative state, visibility, response contracts, plan bundles | Domain truth, validator verdicts, repair policy, Final Emission ordering | Stable | `game/prompt_context.py`; ownership ledger |
| Response policy contracts | Shipped policy contract shape builders, resolution helpers, read-only accessors | Validator verdicts, repair strategy, gate ordering, FEM packaging | Stable | `game/response_policy_contracts.py`; ownership ledger |
| Realization/model I/O | Candidate expression, route metadata, upstream failure handling, governed fallback-family metadata | Domain truth, CTIR construction, final legality, replay authority | Stable for current provider; adapter implementation pending | `game/gm.py`, `game/model_routing.py`, `game/realization_provenance.py`, AR-BG/AR-BH |
| Model routing | Deterministic model lane selection and route metadata | Provider SDK invocation, prompt construction, Final Emission, domain mechanics | Stable | `game/model_routing.py`, `tests/test_model_routing_config.py`, `tests/test_model_routing_runtime.py` |
| Backend identity | Future backend/provider id, adapter version, capability, request/response/error contract | Model routing alone, prompt context, Final Emission, replay as runtime selector | Architecturally defined; implementation pending | AR-BG, AR-BH |
| Final Emission gate | Last-mile order, validation orchestration, selection/application, legality, sealing | Domain truth, ordinary semantic authoring, replay authority, persistence authority | Stable with drift-watch residue | AR-BF; ownership ledger |
| Final Emission metadata | Metadata defaults, merge helpers, slimming/coercion, FEM read-side packaging | Gate sequencing, validator decisions, repair control flow, prompt contracts | Stable | `game/final_emission_meta.py`; ownership ledger |
| Validators | Deterministic predicates, verdicts, reason codes, evidence | Replacement output, prose repair, layer orchestration | Stable | AR-BF, AR-BD |
| Repairs | Bounded known-failure correction; transitional semantic residue explicitly watched | Domain truth, unbounded synthesis, replay decisions | Stable with compatibility/drift-watch | AR-BF; ownership ledger |
| Sanitizers | Strip/package/drop contamination and route-illegal artifacts | General diegetic rewrite, fallback authorship, domain truth | Stable | AR-BF, AR-BD |
| Fallback | Bounded substitute behavior with split content/selection/application/provenance/observer axes | Single-owner fallback authority, untraceable invention, replay authority | Stable with vocabulary compatibility pressure | AR-BF, AR-BD, `game/realization_provenance.py` |
| Persistence | Versioned document envelopes, validation, failure categories, storage mechanics | Gameplay semantics, ruleset mechanics, replay authority | Stable | `game/persistence_contract.py`, `docs/runtime_persistence_envelope.md` |
| Replay/projection | Read-side observation of finalized runtime surfaces; protected acceptance projections | Live runtime selection, mutation, provider/ruleset selection | Stable | AR-BD, AR-BE, AR-BG |
| Provenance | Source/family/owner/lineage explanation of behavior | Selecting behavior, authoring output, mutating domain state | Stable; bundle implementation pending | `game/realization_provenance.py`, `game/final_emission_replay_projection.py`, AR-BH |
| Diagnostics/telemetry | Explanatory read-side snapshots, lineage, traces, evidence | Live gameplay decisions unless explicitly runtime-packaged | Stable | `game/stage_diff_telemetry.py`, ownership ledger |
| Governance/test governance | Doctrine, canonicality, direct-owner tests, drift-watch, evidence classification | Gameplay execution, runtime mutation, replay as live authority | Stable | `docs/architecture_ownership_ledger.md`, AR-BD |
| UI/tooling projection | Local UI mode/channel projection and API consumption | Runtime truth ownership, raw-public stable external contract | Stable locally; public facade optional future architecture | AR-BE, AR-BG, AR-BH |

## 5. Canonical Dependency Model

Canonical forward runtime dependency:

```text
Runtime transaction
  -> Domain simulation
  -> State authority mutation/publication
  -> CTIR resolved-turn meaning
  -> Prompt/context adaptation
  -> Model routing
  -> Realization/backend/model candidate output
  -> Final Emission validators/repairs/sanitizers/fallback selection
  -> Final sealed player/author/debug payloads
  -> Persistence/log/response
  -> Runtime diagnostic projection
  -> Protected replay projection
  -> Replay/evidence/diagnostics
  -> Governance/test governance
```

Canonical dependency rules:

- Domain simulation precedes narration.
- CTIR is built after authoritative mutation.
- Prompt context consumes CTIR when present and must not re-decide CTIR-owned meaning.
- Realization consumes prompt context and route decisions; candidate output is not truth.
- Final Emission consumes candidate/prepared/fallback output and authoritative context; it does not become domain simulation.
- Persistence observes finalized runtime surfaces and owns storage mechanics.
- Replay and evidence observe after runtime; runtime must not depend on protected replay acceptance structures.
- Governance consumes evidence and declares doctrine; it does not drive live behavior.

Optional future contract dependency:

```text
Ruleset contract
  -> domain mechanics selection/capability publication
  -> runtime/session/persistence/provenance/replay identity

Backend contract
  -> provider invocation and response/error normalization
  -> realization provenance
  -> diagnostics/replay identity
```

These future contracts attach identity and capability to the existing dependency model. They do not change the runtime spine.

## 6. Remaining Work Classification

### Implementation

- Implement ruleset contract/registry fields defined by AR-BH.
- Publish active ruleset identity in runtime/session metadata.
- Add ruleset compatibility checks for persisted payloads and replay metadata.
- Extract backend adapter boundary before adding any second provider.
- Move OpenAI invocation behind the first backend adapter.
- Add deterministic fake backend tests.
- Emit version/provenance bundle fields.
- Continue bounded feature implementation inside existing domain-owner pattern.

### Documentation

- Add ruleset contract decision record when implementation begins.
- Add backend adapter decision record when implementation begins.
- Add version/provenance field registry.
- Update ownership ledger after new contract modules exist.
- Produce concise implementation handoff notes from AR-BI.

### Governance

- Add direct-owner tests for ruleset contract and backend contract modules.
- Add drift guards preventing provider-specific logic from spreading into prompt context, Final Emission, replay, or persistence.
- Add replay/provenance compatibility tests for version bundle fields.
- Keep Final Emission semantic repair residue under drift-watch until compatibility retirement.
- Keep protected replay projection separate from runtime diagnostic projection.

### Product Decisions

- Whether alternate rulesets are actually in scope.
- Whether additional providers/local inference are actually in scope.
- Whether external/public tooling requires a public command/query/event facade.
- Whether player-facing explanation UX should expose provenance.
- Whether long-lived saved campaigns require formal migration policy across ruleset/backend versions.

### Optional Future Architecture

- Public UI/tooling facade architecture.
- Player-safe explanation and hidden-information redaction schema.
- Formal saved-campaign migration policy.
- Hosted/multi-user API/event model.
- Generic plugin architecture, only if concrete ruleset/backend/tool/content requirements justify it.

No remaining item is classified as mandatory unresolved architecture.

## 7. Campaign Closeout Decision

### Is Campaign 4 Complete?

Yes.

Confirmed fact: AR-BE completed the boundary inventory, AR-BF certified Final Emission durability, AR-BG inventoried extensibility identity gaps, and AR-BH defined the minimum ruleset/backend/version/provenance contracts. No cycle found instability requiring runtime redesign.

### Is Additional Boundary Reconciliation Required?

No.

Strong inference: additional Boundary Reconciliation would repeat already-settled doctrine unless future product choices introduce new scope. Current remaining questions are implementation sequencing, documentation placement, governance tests, and product direction.

### Is Implementation Now The Recommended Focus?

Yes.

The next major work should be implementation-focused: either a controlled feature lane using the existing pattern, or implementation of the minimal extensibility contracts if alternate rulesets/additional providers/replay portability are the chosen product goal.

Repository evidence:

- AR-AI found ownership, CTIR, replay, persistence, and feature-locality ready.
- AR-BE found the boundary model mature and durable.
- AR-BF found Final Emission architecturally durable.
- AR-BG found extensibility structurally viable after local contracts.
- AR-BH defined those contracts and declared Campaign 4 ready for closeout.

## 8. Recommendations

Recommended next major campaign: **Controlled Implementation Campaign 5 - Extensibility Contract Implementation and First Bounded Feature Lane**.

Why it follows naturally:

- Boundary Reconciliation is complete.
- The architecture now has a stable doctrine and dependency model.
- AR-BH identified the exact contracts required before alternate rulesets, additional providers, replay portability, and save compatibility.
- AR-AI previously recommended implementation through bounded feature lanes: domain owner, state ownership, CTIR/projection, UI/API exposure, replay/provenance, and tests.

Recommended first implementation tracks:

1. **Minimal Extensibility Contract Implementation** if the immediate goal is alternate rulesets, additional providers, local inference, or replay portability.
2. **Controlled Feature Lane Implementation** if the immediate goal is gameplay expansion inside the current ruleset/provider architecture.
3. **Public Facade Discovery/Implementation** only if external tooling or hosted/public APIs are the immediate product direction.

Do not begin with a generic plugin framework. Do not branch providers inside `game.gm.call_gpt`. Do not add alternate rulesets through scattered mechanics conditionals.

## 9. Files Required For Future Campaigns

### Core Doctrine

- `AR-BI_boundary_reconciliation_campaign_closeout.md`
- `AR-BH_minimal_extensibility_contract_definition.md`
- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-BF_final_emission_boundary_validation.md`
- `AR-BE_boundary_reconciliation_discovery_and_evidence_inventory.md`
- `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
- `AR-AI_final_vision_compatibility_closeout.md`
- `docs/architecture_ownership_ledger.md`
- `docs/runtime_persistence_envelope.md`

### Frequently Needed

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
- `game/final_emission_gate.py`
- `game/final_emission_runtime.py`
- `game/final_emission_meta.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_ctir_schema.py`
- `tests/test_noncombat_resolution.py`
- `tests/test_runtime_persistence_regression_suite_obj14.py`
- `tests/test_realization_provenance.py`
- `tests/test_final_emission_meta.py`

### Rarely Needed

- Static frontend files, unless UI/tooling facade work is selected.
- `game/api.py`, unless runtime publication, public facade, or transaction placement is in scope.
- `game/storage.py`, unless save compatibility or migration behavior is in scope.
- `tests/helpers/golden_replay_projection.py`, unless replay observation schema/versioning is in scope.
- Importer/content tooling files, unless ruleset/content packaging is selected.
- Generic plugin scaffolding, unless a future product decision explicitly chooses plugin architecture.
- Live provider credentials or network traces.

## Final Closeout Statement

Boundary Reconciliation is officially complete.

The architecture is stable enough for implementation campaigns. Future work should use the doctrine in this file as the default architectural reference and should reopen Boundary Reconciliation only when new repository evidence contradicts the dependency model or when a deliberate product decision introduces a genuinely new architectural class.
