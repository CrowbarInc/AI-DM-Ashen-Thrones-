# AR-BX - Chassis Strategy Discovery and Evidence Inventory

Campaign: Campaign 6 - Chassis Strategy

Scope: discovery and classification only. No implementation, package movement, runtime behavior change, or architectural redesign was performed.

## 1. Executive Summary

The repository appears ready for long-term chassis definition. Campaigns 1-5 already recovered, reconciled, and operationalized a coherent architecture, and current source/tests/docs mostly reinforce the same dependency direction rather than contradicting it.

Strongest candidate stable boundaries:

- Runtime transaction spine: `game/api.py` owns request/turn ordering, including authoritative mutation, CTIR timing, realization, Final Emission, persistence/logging, and response endpoints.
- Domain simulation and state authority: mechanics live in `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/exploration.py`, `game/social.py`, `game/world.py`, and are bounded by `game/state_authority.py`.
- CTIR and prompt adaptation: `game/ctir.py` and `game/ctir_runtime.py` own resolved-turn meaning; `game/prompt_context.py` and `game/gm.py::build_messages` adapt approved truth for model expression.
- Backend/model boundary: `game/model_routing.py`, `game/config.py`, `game/gm.py::call_gpt`, `game/api_upstream_preflight.py`, and `game/upstream_dependent_run_gate.py` form the current backend surface.
- Final Emission: `game/final_emission_gate.py`, `game/final_emission_runtime.py`, `game/final_emission_boundary_contract.py`, `game/final_emission_meta.py`, validators, repairs, sanitizers, and terminal pipelines own last-mile legality, packaging, metadata, and sealing.
- Persistence, replay, provenance, diagnostics, and governance are downstream/observational except where runtime metadata is explicitly produced by owner helpers.

Clearest extension mechanisms:

- Backend contract path: documented in `docs/backend_contract_registry.md`; executable substrate is current model routing, config, GM adapter, upstream preflight, and run-gate code.
- Ruleset contract path: documented in `docs/ruleset_contract_registry.md`; executable substrate is action normalization, affordances, skill checks, combat, conditions, non-combat framework, schema contracts, scene validation, state authority, and validation-layer registry.
- Version/provenance path: documented in `docs/version_and_provenance_contract_registry.md`; executable substrate includes CTIR versioning, persistence envelope versioning, non-combat framework versioning, realization provenance, FEM metadata, runtime lineage projection, protected replay registries, recurrence/reporting schemas, and generated artifact manifests.
- Feature lane path: documented in `docs/feature_lane_verification.md`; ordinary features attach through a domain owner, API wiring, state authority, CTIR/prompt adaptation if meaning changes, Final Emission preservation if output changes, and direct-owner tests.

Most important internal boundaries:

- Sanitizers, repair helpers, fallback internals, final-emission preflight helpers, projection helpers, compatibility adapters, generated-report scripts, and governance guard helpers should remain internal or owner-scoped. Treating them as public extension APIs would recreate split ownership and replay/provenance drift.

Areas requiring deliberate future analysis:

- Executable ruleset identity/version/capability fields are not implemented yet; the current ruleset registry is documentation-only.
- Executable backend adapter/provider registry is not implemented yet; the current backend registry is documentation-only and `game/gm.py::call_gpt` remains the OpenAI adapter.
- Public tooling/hosted API facade, player-facing provenance redaction, saved-campaign migration policy, and formal multi-provider/multi-ruleset loading remain deliberate evolution areas only if product scope requires them.

## 2. Prior Campaign Doctrine Recovered

| Conclusion | Source Document |
|---|---|
| Campaign 1 established a target doctrine in which request/API, runtime orchestration, domain simulation, narrative/prompt work, Final Emission, persistence, replay/evidence, and governance have separate responsibilities. | `AR-AD_target_architecture_doctrine.md` |
| Domain modules own simulation truth; `game.api` owns transaction order; CTIR owns resolved-turn meaning; prompt construction adapts authoritative state; Final Emission owns last-mile legality/packaging; persistence stores runtime documents; replay/evidence observes runtime output. | `AR-AI_final_vision_compatibility_closeout.md`; restated by `AR-BI_boundary_reconciliation_campaign_closeout.md` |
| Campaign 3 stabilized permanent vocabulary: runtime transaction, domain simulation, state authority, CTIR, prompt/adaptation, response policy contracts, realization, Final Emission, validators, repair, sanitizers, fallback, provenance, projection, replay, evidence, diagnostics, telemetry, governance, compatibility residue, and persistence. | `AR-BD_concept_map_synthesis_and_campaign_closeout.md` |
| Campaign 4 found no need to redesign runtime orchestration, state authority, CTIR, prompt adaptation, realization, Final Emission, persistence, replay, diagnostics, or governance. | `AR-BI_boundary_reconciliation_campaign_closeout.md` |
| Ruleset/backend/version/provenance gaps were classified as local contract/implementation work, not a runtime redesign. | `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`; `AR-BH_minimal_extensibility_contract_definition.md`; `AR-BI_boundary_reconciliation_campaign_closeout.md` |
| Final Emission was certified as durable last-mile legality, selection, packaging, metadata/FEM, terminal exception, sealing, and traceability boundary, with semantic repair residue under drift-watch. | `AR-BF_final_emission_boundary_validation.md`; `docs/architecture_ownership_ledger.md` |
| Campaign 5 reduced coordination cost through workflow guides, compatibility register, governance workflow, generated-doc strategy, split-owner automation, and backend/ruleset/version/provenance registries without intentionally changing runtime behavior. | `AR-BW_campaign5_coordination_cost_reduction_closeout.md` |
| Contract registry docs are navigation/governance surfaces and explicitly do not move implementation authority out of code. | `docs/backend_contract_registry.md`; `docs/ruleset_contract_registry.md`; `docs/version_and_provenance_contract_registry.md` |

## 3. Repository Architectural Map

Product-facing entry points:

- `run.py`: Uvicorn startup for `game.api:app`, including operator-facing upstream preflight messaging.
- `static/index.html`, `static/app.js`, `static/styles.css`: local browser UI consuming API state/log/action surfaces.
- `game/api.py`: FastAPI app, HTTP endpoints, turn transaction spine, UI mode projections, reset/import/snapshot surfaces, action/chat/start-campaign entry points.
- `game/api_ui_mode.py`, `game/ui_mode_policy.py`, `game/api_turn_support.py`: API-adjacent support and projection policy.

Runtime and orchestration:

- `game/api.py`: central turn orchestration and transaction sequencing.
- `game/gm.py`, `game/gm_retry.py`: prompt/message building, OpenAI call adapter, retry-supporting model output handling, many legacy/compatibility helpers.
- `game/model_routing.py`, `game/config.py`: deterministic model route decisions and environment-backed model configuration.
- `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py`, `game/upstream_dependent_run_gate_presentation.py`: backend health/preflight and manual-run gate diagnostics.
- `game/ctir.py`, `game/ctir_runtime.py`: canonical turn-meaning object and runtime attach/stamp lifecycle.
- `game/turn_packet.py`, `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`: turn packet, telemetry, and lineage projections.

Gameplay/domain packages:

- `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/exploration.py`, `game/social.py`, `game/adjudication.py`: deterministic mechanics and resolution.
- `game/world.py`, `game/world_progression.py`, `game/campaign_state.py`, `game/session.py`, `game/clocks.py`, `game/clues.py`, `game/projects.py`, `game/leads.py`, `game/conditions.py`: stateful campaign/world support.
- `game/scene_actions.py`, `game/affordances.py`, `game/scene_graph.py`, `game/scene_destination_binding.py`, `game/validation.py`, `game/scene_lint.py`, `game/content_lint.py`, `game/schema_contracts.py`: action/content/schema validation and normalization.
- `data/*.json`, `data/scenes/*.json`, `data/validation/scenario_spines/*.json`: authored content, campaign state, scene library, and validation scenario data.

Final Emission and realization:

- `game/final_emission_gate.py`, `game/final_emission_runtime.py`, `game/final_emission_terminal_pipeline.py`, `game/final_emission_strict_social_stack.py`, `game/final_emission_non_strict_stack.py`: last-mile gate and pipeline.
- `game/final_emission_boundary_contract.py`: executable mutation taxonomy and assertion helper.
- `game/final_emission_meta.py`, `game/final_emission_meta_read.py`, `game/final_emission_meta_observability.py`, `game/final_emission_fem_assembly.py`, `game/final_emission_finalize.py`: FEM metadata write/read/packaging surfaces.
- `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, `game/fallback_behavior.py`, `game/opening_deterministic_fallback.py`, `game/fallback_provenance_debug.py`: validators, bounded repair/sanitizer/fallback support.
- `game/realization_authority.py`, `game/realization_provenance.py`, `game/opening_scene_realization.py`, `game/narrative_planning.py`, `game/narration_plan_bundle.py`: realization authority/provenance and planning surfaces.

Contracts, registries, adapters:

- `game/state_authority.py`: executable state-domain registry and guard helpers.
- `game/validation_layer_contracts.py`: executable phase/layer responsibility registry.
- `game/contract_registry.py`: metadata-only prompt/projection/fallback key registry.
- `game/persistence_contract.py`: executable persistence envelope/version/validation contract.
- `docs/backend_contract_registry.md`, `docs/ruleset_contract_registry.md`, `docs/version_and_provenance_contract_registry.md`, `docs/compatibility_residue_register.md`: current contract/compatibility navigation.

Replay, provenance, diagnostics, evidence:

- `game/final_emission_replay_projection.py`, `game/ownership_projection_views.py`, `game/attribution_read_views.py`, `game/observability_attribution_read.py`, `game/semantic_mutation_attribution.py`: runtime/read-side projection and attribution helpers.
- `tests/helpers/golden_replay*.py`, `tests/helpers/protected_replay*.py`, `tests/helpers/replay_bug_recurrence*.py`: replay/protected observation/projection helper layer.
- `artifacts/golden_replay/`, `audits/`, `docs/audits/`: retained evidence, generated reports, historical audits, and closeouts.
- `tools/*replay*`, `tools/*fallback*`, `tools/*attribution*`, `tools/*stability*`, `tools/refresh_protected_replay_manifest.py`: evidence and governance tooling.

Documentation and governance:

- Root `AR-*`, `CI_*`, `CL*`, `CM*`, etc.: campaign and cycle artifacts.
- `docs/architecture_ownership_ledger.md`, `docs/feature_lane_verification.md`, `docs/governance_refresh_workflow.md`, `docs/generated_documentation_appendices.md`, `docs/convergence_ci_inventory.md`: active governance/workflow.
- `tests/README_TESTS.md`, `tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `tests/validation_coverage_registry.py`: test governance and validation coverage.
- `.github/workflows/`, `Makefile`, `pytest.ini`: CI/local command surfaces.

Legacy or compatibility areas:

- `docs/compatibility_residue_register.md`: active compatibility planning register.
- `game/gm.py` and `game/api.py`: large historical hubs with compatibility helpers and current orchestration/adapter responsibilities.
- `docs/archive/dead_governance/`: archived historical governance.
- `codex_pytest_tmp*`, `.pytest_cache`, `__pycache__`, `artifacts/bv3b_replay_refresh/*`: generated/temp/historical evidence outputs rather than architectural contracts.

## 4. Stable Boundary Candidates

| Boundary | Owning Area | Executable Evidence | Documentation Evidence | Exceptions or Ambiguities | Preliminary Classification |
|---|---|---|---|---|---|
| Runtime transaction order | `game/api.py` | `action`, `chat`, `start_campaign`, `_run_resolved_turn_pipeline`, `_build_gpt_narration_from_authoritative_state`, persistence-like opening completion | `AR-BI` permanent doctrine; `AR-AD`; `docs/feature_lane_verification.md` | `game/api.py` is large and includes legacy adoption/compat helpers; delegate extraction is cleanup only if transaction authority remains intact. | Stable Doctrine |
| Domain simulation owns mechanics truth | Domain modules | `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py::NONCOMBAT_FRAMEWORK_VERSION`, `game/exploration.py`, `game/social.py`, `game/models.py` | `docs/ruleset_contract_registry.md` RCR-04/RCR-05/RCR-07; `AR-BI` | Current ruleset is PF1e-inspired and single-engine; alternate rulesets not implemented. | Stable Doctrine with future ruleset extension |
| State authority registry/guards | `game/state_authority.py` | `StateDomainSpec`, `CrossDomainWriteSpec`, `assert_owner_can_mutate_domain`, `assert_cross_domain_write_allowed`, `build_state_mutation_trace`; `tests/test_state_authority.py` | `docs/state_authority_model.md`; `docs/architecture_ownership_ledger.md`; RCR-08 | Guard adoption is partial by design; module is registry/guard, not persistence engine. | Stable Doctrine |
| CTIR resolved-turn meaning | `game/ctir.py`, `game/ctir_runtime.py`, API timing | `_CTIR_VERSION`, `build_ctir`, `looks_like_ctir`, `attach_ctir`, `ensure_ctir_for_turn`; CTIR tests named in ownership ledger | `docs/ctir_prompt_adapter_architecture.md`; `AR-BD`; `AR-BI` | `prompt_context` has bounded fallback reads when CTIR absent; not a second semantic owner. | Stable Doctrine |
| Prompt/adaptation | `game/prompt_context.py`, `game/gm.py::build_messages` | prompt context assembly, `build_messages`, response policy bundle consumption | `docs/architecture_ownership_ledger.md` Prompt Contracts; BCR-04 | Provider-specific message adaptation may need backend adapter extraction before new providers. | Stable Doctrine with backend evolution |
| Response policy contracts | `game/response_policy_contracts.py` | `materialize_response_policy_bundle`, contract resolvers/builders; direct owner test `tests/test_response_policy_contracts.py` | ownership ledger; feature-lane guide | Private compatibility accessors remain supported but not public extension surfaces. | Stable Doctrine |
| Model routing | `game/model_routing.py` | `ModelRouteDecision`, `resolve_model_route`, env config via `game/config.py`; model routing tests | BCR-01/BCR-02; `docs/model_routing_architecture.md` | Route metadata is diagnostic, not replay acceptance or provenance authority. | Stable Doctrine / Backend Extension Mechanism |
| Backend call adapter | `game/gm.py::call_gpt` | `call_gpt`, upstream error normalization helpers, route metadata attachment; preflight tests | `docs/backend_contract_registry.md` BCR-03/BCR-05/BCR-08 | No separate provider adapter registry yet; future multi-provider work should extract one deliberately. | Expected Extension Mechanism, implementation pending |
| Final Emission boundary | Final Emission modules | `apply_final_emission_gate`, `finalize_player_facing_emission`, `classify_final_emission_mutation`, `assert_final_emission_mutation_allowed`; gate/direct-owner tests | `AR-BF`; ownership ledger; feature-lane guide | Semantic repair residue remains drift-watch; not a reason to redesign. | Stable Doctrine with drift-watch |
| Validators vs repairs vs sanitizers | validator/repair/sanitizer owner modules | `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, mutation taxonomy | `AR-BD`; ownership ledger; feature-lane guide | Some repairs historically mutate meaning; convergence target is bounded legality/packaging. | Stable Doctrine / Internal Boundaries |
| Persistence envelope | `game/persistence_contract.py`, storage I/O owner | `PERSISTENCE_FORMAT_VERSION`, `wrap_runtime_payload`, `unwrap_and_validate`, `PersistenceFailureCategory` | `docs/runtime_persistence_envelope.md`; `AR-BI`; VPCR | Legacy missing-envelope normalization is compatibility, not new schema freedom. | Stable Doctrine |
| Replay/projection observes runtime | replay helpers/tests and projection owners | `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection*.py`, protected field registries; replay governance tests | `docs/testing/protected_replay_manifest.md`; VPCR-01/02/11; tests README | Runtime must not depend on protected replay acceptance helpers. | Stable Doctrine |
| Provenance explains behavior | realization/FEM/lineage owners | `game/realization_provenance.py`, `game/final_emission_meta.py`, `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py` | VPCR-03/04/05/06; feature-lane guide | Provenance must not select behavior; some metadata is replay-sensitive. | Stable Doctrine |
| Governance declares/watches | docs/tests/tools governance | ownership ledger, validation coverage registry, replay governance contracts, split-owner scripts/tests | `docs/governance_refresh_workflow.md`, `tests/README_TESTS.md`, `AR-BW` | Manual docs can drift; governance workflow mitigates but does not enforce all registries. | Stable Doctrine with manual drift risk |

## 5. Extension Mechanism Inventory

| Extension Mechanism | Extensible Capability | Governing Contract | Selection or Registration Path | Validation / Replay / Provenance Obligations | Central Changes Required? | Maturity |
|---|---|---|---|---|---|---|
| Model routing | Model lane selection and escalation policy | `game/model_routing.py::ModelRouteDecision`, `resolve_model_route`; BCR-01 | Explicit call-site inputs plus env config in `game/config.py` | Model routing tests; metadata diagnostic only; protected replay should observe downstream payloads, not route frequency | May require routing config/call-site edits, but not core transaction redesign | Executable and stable |
| Backend call adapter | Provider request/response/error normalization | `game/gm.py::call_gpt`; BCR-03/BCR-05/BCR-08 | Current direct OpenAI Responses adapter; future provider adapter should sit behind this boundary | Preserve GM output dict shape, normalized errors, lazy secret access, route metadata, realization provenance separation | Future second provider requires deliberate adapter extraction and tests | Current provider stable; multi-provider pending |
| Upstream preflight/run gate | Backend health and operator validity | `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py`; BCR-06/BCR-07 | Startup/preflight cache and run-gate computation | No hidden probes in run gate; secret-safe status; not replay policy | Provider expansion should feed equivalent cached-health row | Executable and stable |
| Ruleset action/content ingress | New action types/content shapes | `game/scene_actions.py`, `game/affordances.py`, `game/schema_contracts.py`, `game/validation.py`; RCR-02/03/09/10 | Canonical action normalization, affordance generation, schema adapters, scene validation | Domain tests, schema tests, scene/content validation; replay if outcomes change | Usually local domain/schema/validation edits; no architecture change | Executable and stable |
| Domain mechanics | New gameplay subsystem or mechanics variant | domain modules plus `game/state_authority.py`; RCR-04/05/06/07/08 | Domain owner implementation called by API or non-combat framework | Direct-owner domain tests, state authority checks, CTIR changes if resolved meaning changes, replay if protected behavior changes | API wiring may be needed; no foundational change | Executable for current engine |
| Non-combat framework | New non-combat kinds/domain policies | `game/noncombat_resolution.py::NONCOMBAT_FRAMEWORK_VERSION`; RCR-07; VPCR-08 | Classification/delegation/normalized outcome framework | Version review, CTIR/prompt tests, fail-closed behavior, replay-adjacent tests | Central non-combat framework edit likely; architecture remains intact | Executable and versioned |
| Ruleset identity/capability | Alternate ruleset publication | `docs/ruleset_contract_registry.md`; AR-BH ruleset contract | Not yet executable; future identity/version/family/capability fields | Must include save/replay/provenance/version impact and drift guards against conditionals in prompt/FE/replay/backend | Yes, new contract module/registry and tests before alternate rulesets | Documented, implementation pending |
| Response policy contracts | New response-shape policy | `game/response_policy_contracts.py`; ownership ledger | Contract builders/resolvers shipped through turn/prompt/gate surfaces | Direct owner tests first; downstream smoke only; FE must read, not redefine | Local owner and consumer wiring | Executable and stable |
| Final Emission layers | New last-mile legality/packaging rule | FE owner module and boundary taxonomy | Add validator/repair/sanitizer/gate integration under owner | Mutation kind classification, direct-owner tests, FEM/provenance/replay if observed | Gate orchestration edits may be required; not a public plugin point | Executable but tightly governed |
| Persistence envelope | New persisted document kind or schema validation | `game/persistence_contract.py`; runtime persistence docs | `wrap_runtime_payload`/`unwrap_and_validate` with expected kind | Version/integrity/legacy acceptance review; replay/save compatibility | Local storage/persistence edits | Executable and stable |
| Protected replay observation registry | New protected replay field/scenario | `tests/helpers/protected_replay_registry.py`, golden projection fields, manifest tooling; VPCR-01/02 | Executable registry plus `tools/refresh_protected_replay_manifest.py` | Manifest refresh/check, protected/advisory classification, governance tests | No runtime changes unless protected behavior changed | Executable test/governance mechanism |
| Generated documentation/artifacts | New generated evidence views | `docs/generated_documentation_appendices.md`, generator-specific scripts/manifests | Source registry/generator-specific refresh paths | Generated sections identify source; docs do not become executable authority | Generator or docs workflow edits only | Governance mechanism, partly manual |
| Feature-lane workflow | Future implementation without rediscovery | `docs/feature_lane_verification.md` | Manual lane selection by change type | Direct owner tests before downstream smoke; replay/provenance checks only when relevant | No central runtime edits required by the workflow itself | Mature manual process |

True extension mechanisms are the owner contracts above. Ordinary internal indirection, private helpers, compatibility shims, and projection utilities are not extension mechanisms.

## 6. Internal Implementation Boundary Inventory

| Internal Area | Responsibility | Current Consumers | Why It Should Remain Internal | Leakage or Misuse Risk | Evidence |
|---|---|---|---|---|---|
| Final Emission preflight helpers | Assemble gate context, branch flags, turn packet, upstream telemetry, strict-social preflight | Final Emission gate/terminal stacks | They support one gate ordering contract; external callers should not sequence gate internals | External reliance would freeze helper order and recreate split gate ownership | `game/final_emission_gate_preflight_*.py`; ownership ledger |
| Repair helpers | Bounded legality/packaging repair and drift-watch semantic residue | Final Emission gate, downstream smoke tests | Repairs are not a general content synthesis API | Treating them as extensible prose generators would move domain/prompt semantics to the boundary | `game/final_emission_repairs.py`; `game/final_emission_boundary_contract.py`; `tests/test_final_emission_boundary_convergence.py` |
| Sanitizers/output scrubbing | Strip/drop/package illegal output artifacts | Final Emission and response policy paths | Sanitizers enforce output hygiene, not domain truth or style policy | A public sanitizer API could become ad hoc semantic rewrite layer | `game/output_sanitizer.py`; AR-BD sanitizer definition; ownership ledger |
| Fallback internals | Deterministic local substitutes, selection/application/provenance fragments | API retry/fallback, Final Emission, replay projection | Fallback has split ownership axes and compatibility residue; no single public fallback extension point exists | New fallback authorship could bypass provenance/family stamping and replay observability | `game/fallback_behavior.py`, `game/opening_deterministic_fallback.py`, `game/social_exchange_fallback_catalog.py`, `game/realization_provenance.py` |
| Projection helpers | Read-side replay/diagnostic projection of finalized metadata | Replay, dashboards, recurrence/stability reports | Projection observes runtime; it must not influence runtime selection/mutation | Runtime dependencies on projection would invert architecture and destabilize protected replay | `game/final_emission_replay_projection.py`; `tests/helpers/golden_replay_projection*.py`; VPCR |
| Compatibility adapters | Preserve legacy payload/env/import behavior | Runtime schema, model config, tests, compatibility register | Compatibility is evidence-managed, not an expansion API | New work might hide behind legacy shims instead of publishing owner contracts | `game/schema_contracts.py`, `game/config.py`, `docs/compatibility_residue_register.md` |
| Contract metadata registry | Central key sets and telemetry identifiers | Planner/prompt docs/tests, emergency fallback static drift tests | It is metadata-only and explicitly does not build/validate/repair runtime artifacts | Treating it as enforcement would move behavior into a registry not designed for it | `game/contract_registry.py`; VPCR-09 |
| Governance guard helpers | Import/scope/write-path/replay boundary checks | Governance tests | They enforce known structure; they are not runtime extension APIs | Feature logic could leak into test-support helpers or make governance brittle | `tests/ownership_guard_*.py`, `tests/ownership_closeout_delegate_locks.py`, `tests/test_*governance.py` |
| Evidence/report scripts | Generate audit, replay, fallback, recurrence, stability outputs | Maintainers and CI/document refresh workflows | They are observers/generators, not runtime behavior | Generated evidence could become hand-maintained doctrine or duplicate executable truth | `tools/*`, `scripts/*`, `docs/generated_documentation_appendices.md` |
| UI mode projection helpers | Project API state/log for player/debug modes | API endpoints/local UI | They are local projection policy, not a public stable external API facade | External tooling may couple to raw internal shapes before a facade is designed | `game/api_ui_mode.py`, `game/ui_mode_policy.py`, `AR-BI` UI/tooling projection note |
| Test fixtures/helpers | Harnesses, replay runners, gauntlet/report support | Tests/tools only | They encode verification mechanics, not production extension contracts | Production code depending on tests would collapse replay/evidence separation | `tests/helpers/*`, `tests/README_TESTS.md` |

## 7. Representative Feature Attachment Traces

### 1. New gameplay subsystem modifying world-state behavior

- Entry or attachment point: domain owner module near `game/world.py`, `game/world_progression.py`, `game/exploration.py`, `game/noncombat_resolution.py`, or a new domain module called by `game/api.py`.
- Expected dependency path: API receives action -> action normalization if needed -> domain resolver mutates authoritative state -> `game/state_authority.py` guards/trace if new write/read path -> CTIR updated if resolved-turn meaning changes -> prompt/Final Emission consume result -> persistence/log/replay observe.
- Contracts involved: state authority registry, schema contracts, non-combat framework if non-combat, persistence envelope if persisted document shape changes, feature-lane guide.
- Protected internal boundaries: GPT/model output must not mutate truth; Final Emission must not create mechanics; replay projection must not drive runtime.
- Likely implementation locations: `game/world*.py`, `game/noncombat_resolution.py`, `game/api.py`, `game/ctir.py`, focused tests under the domain owner.
- Architectural implications: no foundational change if the subsystem fits existing domain-owner/state-authority/CTIR pattern. Coordination cost emerges if state is written from prompt/Final Emission or if new state domains are added without state authority review.

### 2. New ruleset with materially different domain policies

- Entry or attachment point: not directly implemented today. First attach through an explicit ruleset identity/capability/version contract, then domain mechanics/action/schema/non-combat/state contracts.
- Expected dependency path: ruleset identity -> action/schema/non-combat/domain mechanic selection -> state authority/persistence/provenance/replay identity -> CTIR/prompt/Final Emission consume resolved outcomes.
- Contracts involved: `docs/ruleset_contract_registry.md`, AR-BH ruleset contract definition, `game/state_authority.py`, `game/noncombat_resolution.py`, `game/schema_contracts.py`, validation-layer registry, version/provenance registry.
- Protected internal boundaries: no scattered ruleset conditionals in prompt, Final Emission, replay projection, or backend code; no GPT-owned mechanics.
- Likely implementation locations: future ruleset identity module/registry, domain mechanic modules, schema/action validation, tests for identity and compatibility.
- Architectural implications: deliberate evolution/implementation package required, but current chassis provides attachment contracts. Coordination cost emerges if alternate ruleset behavior is introduced before identity/version/capability publication.

### 3. New AI backend or model provider

- Entry or attachment point: backend adapter boundary around `game/gm.py::call_gpt`, with model routing in `game/model_routing.py` kept distinct.
- Expected dependency path: API/prompt builds messages -> model routing selects lane -> backend adapter normalizes request/response/error -> GM output shape preserved -> realization/fallback provenance and Final Emission continue downstream.
- Contracts involved: backend contract registry BCR-01 through BCR-09; `game/config.py`; upstream preflight/run-gate contracts; realization provenance and FEM metadata.
- Protected internal boundaries: provider-specific shapes must not leak into prompt context, API transaction logic, Final Emission legality, replay acceptance, or ruleset mechanics.
- Likely implementation locations: new backend adapter module, `game/gm.py` delegation, `game/config.py`, preflight equivalents, model routing tests and provider fake tests.
- Architectural implications: no runtime redesign, but adapter extraction is deliberate implementation work before adding a second provider. Coordination cost emerges if provider branches are added inside prompt/gate/replay.

### 4. Richer player-facing product or UI

- Entry or attachment point: API endpoints and local UI projection surfaces: `game/api.py`, `game/api_ui_mode.py`, `game/ui_mode_policy.py`, `static/*`.
- Expected dependency path: UI consumes projected state/log/action surfaces -> API remains transaction owner -> runtime emits player/author/debug payloads -> UI mode policy controls visibility.
- Contracts involved: UI mode policy, API response shapes, state authority visibility/publication, feature-lane guide.
- Protected internal boundaries: UI must not become state authority, replay acceptance authority, or direct Final Emission mutator.
- Likely implementation locations: `static/*`, `game/api_ui_mode.py`, `game/ui_mode_policy.py`, selected API projection helpers and tests.
- Architectural implications: richer local UI can proceed in current chassis. Public/hosted external facade or multi-user event model would require deliberate future architecture.

### 5. New persistence, replay inspection, or debugging tool

- Entry or attachment point: tools/tests/docs layer, persistence contract, projection helpers, protected replay registries.
- Expected dependency path: read persisted/runtime artifacts -> use `game/persistence_contract.py` and replay/projection helpers -> generate reports/artifacts -> governance docs/manifests record source.
- Contracts involved: persistence envelope, VPCR rows for protected replay/projection/generated docs/recurrence/stability, governance refresh workflow.
- Protected internal boundaries: tool must observe; it must not feed protected acceptance or diagnostics back into runtime behavior.
- Likely implementation locations: `tools/`, `tests/helpers/`, `artifacts/`, `docs/testing/`, focused tests.
- Architectural implications: no foundational change for local tools. Coordination cost emerges if generated outputs become manually edited doctrine or if runtime imports test helpers.

### 6. New content package or campaign type

- Entry or attachment point: `data/`, `data/scenes/`, `game/validation.py`, `game/content_lint.py`, `game/scene_actions.py`, `game/affordances.py`, `game/storage.py`.
- Expected dependency path: content loaded/validated -> normalized scene/action schemas -> domain mechanics resolve actions -> API/CTIR/prompt/Final Emission/persistence proceed normally.
- Contracts involved: scene/content validation contract, schema contracts, action normalization, affordance generation, persistence envelope if save shape changes.
- Protected internal boundaries: content must not define arbitrary runtime mutation or bypass validation; campaign type should not imply a new ruleset unless identity/capability contract exists.
- Likely implementation locations: `data/scenes/*.json`, validation/lint tests, maybe importers under `game/importers/`.
- Architectural implications: new content packages can mostly proceed without architecture change. Coordination cost emerges if content-specific logic spreads into API/gate/prompt instead of validation/domain owners.

### 7. New diagnostic or observability capability

- Entry or attachment point: telemetry/projection/reporting owner modules: `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py`, `tools/`, `tests/helpers/`.
- Expected dependency path: runtime owner emits bounded metadata/trace -> read-side diagnostic projection derives events -> reports/tests consume -> governance updates if field becomes protected or schema-versioned.
- Contracts involved: VPCR-04/05/10/12/13, feature-lane guide, generated documentation strategy.
- Protected internal boundaries: diagnostics/provenance explain behavior; they must not select behavior or substitute for domain/gate decisions.
- Likely implementation locations: runtime metadata owner if new field is produced; projection/report tools if purely observational; tests for schema/projection.
- Architectural implications: no foundational change if read-side and producer ownership remain separate. Coordination cost emerges if diagnostics are used as runtime policy switches without owner approval.

## 8. Package and Repository Organization Assessment

No foundational packaging concern was found. The physical repository broadly expresses the recovered architecture: runtime code under `game/`, product entry/UI at `run.py` and `static/`, authored content under `data/`, tests under `tests/`, retained evidence under `artifacts/` and `audits/`, active docs under `docs/`, and campaign reports at the root.

Naming or documentation concerns:

- Root-level campaign reports are numerous and useful for history, but active doctrine is easier to find through `docs/architecture_ownership_ledger.md`, `docs/feature_lane_verification.md`, and the Campaign 5 registries. This is an organization/discoverability issue, not a chassis defect.
- `game/gm.py` and `game/api.py` remain large historical hubs. Current doctrine treats `game/api.py` as the transaction spine and `game/gm.py` as prompt/GM/backend adapter plus compatibility surface. Size alone is not evidence of architecture failure; future extraction should be owner-preserving.
- Contract registries for backend/ruleset/version are manual docs. They clearly state that implementation authority remains in code, but manual drift remains possible.

Implementation cleanup:

- Future backend adapter extraction should occur before adding a second provider.
- Future ruleset identity/capability module should exist before alternate ruleset behavior.
- Compatibility retirement packages should start from `docs/compatibility_residue_register.md`, not ad hoc cleanup.

Packaging improvement:

- A contract registry index page could reduce navigation cost, as AR-BW already lists as optional.
- If executable backend/ruleset/version registries are later approved, generated appendices could replace manually duplicated summaries.

Deliberate future evolution:

- Public UI/tooling facade, hosted/multi-user API/event model, player-safe provenance redaction, and saved-campaign migration policy.

Foundational architectural concern:

- None found in this cycle. The current package organization adequately expresses the recovered architecture for controlled feature expansion.

## 9. Executable and Documentation Governance Assessment

Authoritative executable contracts include:

- `game/state_authority.py`: state domains, read matrix, mutation guards, cross-domain write allow-list.
- `game/ctir.py` and `game/ctir_runtime.py`: CTIR version, normalized resolved-turn meaning, attach/stamp lifecycle.
- `game/model_routing.py`, `game/config.py`, `game/gm.py::call_gpt`, `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py`: backend route/call/preflight/run-gate behavior.
- `game/persistence_contract.py`: persistence envelope version, validation, integrity, and legacy normalization.
- `game/final_emission_boundary_contract.py`, Final Emission modules, validators, repairs, metadata helpers: last-mile mutation/packaging behavior.
- `game/validation_layer_contracts.py`, `tests/validation_coverage_registry.py`, replay governance/projection helpers: executable governance/test registries.

Contracts enforced by tests:

- Direct-owner tests named in `docs/architecture_ownership_ledger.md` and `tests/README_TESTS.md` for response policy, prompt context, CTIR, Final Emission, state authority, telemetry, replay, validation coverage, and governance.
- Backend tests listed by `docs/backend_contract_registry.md`: model routing, upstream preflight, run-gate, prompt/message adapter, API pipeline tests.
- Ruleset tests listed by `docs/ruleset_contract_registry.md`: action/affordance/schema, skill checks, combat, non-combat, state authority, scene validation, validation layer.
- Replay/provenance tests and manifest checks listed by `docs/version_and_provenance_contract_registry.md`.

Normative documentation:

- `AR-AD_target_architecture_doctrine.md`, `AR-BD_concept_map_synthesis_and_campaign_closeout.md`, `AR-BI_boundary_reconciliation_campaign_closeout.md`, `AR-BW_campaign5_coordination_cost_reduction_closeout.md`.
- `docs/architecture_ownership_ledger.md`, `docs/feature_lane_verification.md`, `docs/governance_refresh_workflow.md`, `docs/backend_contract_registry.md`, `docs/ruleset_contract_registry.md`, `docs/version_and_provenance_contract_registry.md`, `docs/compatibility_residue_register.md`.

Descriptive/historical documentation:

- Older audits and root closeouts provide evidence and history, but current doctrine should be routed through closeouts, ownership ledger, and registries.
- `artifacts/` and many `docs/audits/` reports are evidence records, not live runtime authority unless a current governance doc names them.

Drift detection:

- Tests and tooling include `tools/test_audit.py`, governance tests, validation coverage audit, protected replay manifest refresh/check, split-owner matrix scripts, architecture/validation/final-emission audits.
- Manual registry drift remains a known risk. AR-BW explicitly notes that the registries improve navigation but do not implement behavior.

Documentation duplication risk:

- Backend/ruleset/version registries intentionally summarize executable owners and verification paths. They could silently diverge because they are manual. The current mitigation is governance refresh workflow and registry maintenance rules, not executable generation.

## 10. Long-Term Modularity and Coordination Assessment

Modularity already structural:

- Domain truth precedes narration and is separated from backend/model expression.
- CTIR sits between authoritative resolution and prompt adaptation.
- Final Emission owns last-mile legality/packaging but is not domain truth.
- Persistence stores envelopes/documents and does not own gameplay semantics.
- Replay/projection/evidence observe after runtime and have governance tests preventing ownership leakage.
- State authority and validation-layer registries make cross-domain/phase ownership inspectable.

Modularity dependent on conventions plus tests:

- Final Emission repair residue remains drift-watch and direct-owner-test governed.
- Prompt/GM/backend boundaries are stable, but `game/gm.py` still combines prompt construction, backend call adapter, and compatibility helpers.
- Backend/ruleset/version registries are manual and depend on maintainer discipline until executable registries exist.

Modularity dependent on documentation:

- Future ruleset identity/capability and backend provider adapter decisions.
- Public facade/product integration choices.
- Compatibility retirement sequencing.

Incompletely enforced:

- Ruleset identity/version/capability publication is not executable.
- Backend provider abstraction is not a separate executable provider registry yet.
- Documentation registry drift is possible.

Intentionally unnecessary:

- Generic plugin system is not warranted by current evidence.
- Multi-ruleset runtime loading and multi-provider dispatch are not needed before concrete product requirements.
- Moving packages for aesthetic symmetry is not justified.

Future expansion can proceed without restoring split ownership if contributors follow the feature-lane pattern: start at the owner, extend direct-owner tests, treat adapters/projections as consumers, and update replay/provenance/governance only when their contracts are actually affected.

## 11. Preliminary Chassis Classification

| Architectural Area | Stable Doctrine | Expected Extension Mechanism | Future Implementation Work | Deliberate Evolution Area | Unresolved | Rationale |
|---|---:|---:|---:|---:|---:|---|
| Runtime transaction spine (`game/api.py`) | X |  | X |  |  | Stable owner of order; future delegate cleanup must preserve spine authority. |
| Domain simulation mechanics | X | X | X |  |  | Engine-first domain owners are stable; new mechanics attach through domain/state contracts. |
| State authority | X | X | X |  |  | Executable registry/guards support new domains/edges only through explicit review. |
| CTIR resolved-turn meaning | X | X | X |  |  | Versioned canonical meaning object; can extend slices with tests. |
| Prompt/adaptation | X | X | X |  |  | Stable consumer/adaptor of CTIR/truth; provider-specific adaptation may evolve. |
| Response policy contracts | X | X | X |  |  | Explicit owner and direct tests; extensible via shipped contracts. |
| Backend/model routing | X | X | X |  |  | Routing is executable; provider adapter extraction remains future work. |
| Backend provider registry/adapter |  | X | X | X |  | Documented extension path; no executable multi-provider registry yet. |
| Ruleset identity/capability |  | X | X | X |  | Documented contract; alternate ruleset loading not implemented. |
| Action/schema/content validation | X | X | X |  |  | Stable ingress and content contracts; content/ruleset extensions attach here. |
| Non-combat framework | X | X | X |  |  | Explicit framework version; future variants require version/CTIR review. |
| Final Emission gate | X |  | X |  |  | Stable boundary with drift-watch residue; not a public extension point. |
| Validators/repairs/sanitizers | X |  | X |  |  | Internal owner-scoped implementation surfaces, not generic plugins. |
| Fallback/provenance | X |  | X | X |  | Stable split ownership; taxonomy/versioning may evolve deliberately. |
| Persistence envelope | X | X | X | X |  | Stable versioned envelope; saved-campaign migration policy may evolve. |
| Replay/protected projection | X | X | X |  |  | Test/governance extension path for protected observations; runtime remains independent. |
| Diagnostics/lineage/evidence | X | X | X |  |  | Read-side tools can grow if producer ownership and provenance remain separate. |
| Compatibility residue | X |  | X | X |  | Register governs lifetime; retirement is deliberate package work. |
| Governance/test governance | X | X | X |  |  | Direct-owner and boundary tests enforce much of the doctrine; manual docs require refresh. |
| Local UI/product surface | X | X | X | X |  | Local UI can grow; public/hosted facade is optional future architecture. |
| Generic plugin architecture |  |  |  | X |  | Current evidence does not justify it; only revisit with concrete requirements. |

## 12. Risks and Unknowns

- Manual registry drift: backend/ruleset/version registries are documentation-only and could diverge from source unless governance refresh is followed. Evidence: each registry states it does not change behavior; AR-BW names manual drift as a remaining risk.
- Backend extension readiness is not the same as provider support: `docs/backend_contract_registry.md` documents the path, but `game/gm.py::call_gpt` remains the current OpenAI adapter and no executable provider registry was found.
- Ruleset extension readiness is not the same as alternate ruleset support: `docs/ruleset_contract_registry.md` documents ruleset-facing contracts, but current mechanics are one engine-first PF1e-inspired ruleset and no executable ruleset identity/loader was found.
- Final Emission semantic repair residue remains a managed drift-watch area. Evidence: ownership ledger and AR-BF classify repair residue and convergence target without reopening the boundary.
- Public/external UI or hosted integrations may require a facade not currently present. Evidence: AR-BI classifies public tooling APIs/hosted integrations as optional future architecture conditional on product scope.
- Saved-campaign migration across future ruleset/backend/version fields is not formalized. Evidence: AR-BI lists formal saved-campaign migration policy as optional future architecture/product decision.

No additional source files are required to define the next Campaign 6 cycle, but the next cycle should inspect the same owner files if it chooses to turn this inventory into normative chassis doctrine.

## 13. Recommended Next Cycle

Recommended title: **AR-BY - Chassis Doctrine Draft and Stability Decision Matrix**

Objective: Convert the AR-BX evidence inventory into a concise long-term chassis doctrine that decides which boundaries are permanent, which extension mechanisms are approved attachment paths, which surfaces are explicitly internal, and which future evolution areas require separate architectural decision records.

Questions it should resolve:

- Which AR-BX stable-boundary candidates become normative chassis doctrine?
- Which extension mechanisms should be named as approved feature/backend/ruleset/tooling attachment paths?
- Which internal implementation areas should be explicitly marked non-public to prevent accidental extension-surface growth?
- Which deliberate evolution areas need decision records before implementation?
- What minimum executable/governance checks are required before Campaign 6 closeout?

Evidence it should use:

- AR-BX inventory.
- Campaign closeouts: `AR-AD`, `AR-AI`, `AR-BD`, `AR-BI`, `AR-BW`.
- Active docs: ownership ledger, feature-lane guide, governance workflow, compatibility register, backend/ruleset/version-provenance registries.
- Executable owner files and direct-owner tests named in this inventory.

Mode: analysis-only by default. Limited documentation implementation may be appropriate only if the cycle is explicitly asked to publish the doctrine artifact. No production behavior changes are necessary before the doctrine decision.

Why necessary before campaign closeout:

- AR-BX establishes evidence and preliminary classification. Campaign 6 still needs a smaller normative decision artifact that future contributors can use without rereading every campaign report.
