# AR-BE Boundary Reconciliation Discovery and Evidence Inventory

Campaign: Campaign 4 - Boundary Reconciliation

Scope: repository-grounded discovery of architectural responsibility boundaries after Campaigns 1-3. This report performs no production-code refactoring and treats prior campaign outputs as governing doctrine unless repository evidence contradicts them.

Evidence posture: conclusions below are labeled as confirmed facts, strong inferences, tentative interpretations, or evidence gaps where useful. Paths and symbols are repository-relative.

## 1. Executive Summary

The boundary model appears mature and substantially durable. The strongest repository-supported architecture is the forward runtime truth pipeline documented in `AR-BD_concept_map_synthesis_and_campaign_closeout.md`: player intent enters a runtime transaction, domain simulation establishes truth, CTIR captures resolved-turn meaning, prompt/adaptation packages that truth, realization produces candidate expression, final emission seals player-facing output, persistence/log/response preserve it, and replay/evidence/governance observe it afterward.

Durable boundaries are especially clear around state authority, CTIR vs prompt adaptation, final emission legality/packaging, replay/projection non-authority, governance as doctrine/test-side policy, content lint as author-time tooling, and UI mode projection as a non-authoritative view layer.

Intentional overlap remains central rather than accidental. Final emission intentionally orchestrates validators, repair, sanitizers, fallback handling, provenance packaging, and metadata. Fallback intentionally spans content author, selector, applicator, recorder, provenance packager, and replay observer. State authority intentionally separates mutation ownership from publication/projection participation.

Transitional pressure is concentrated in final-boundary semantic repair residue, dual fallback/provenance vocabulary, compatibility import barrels, legacy sanitizer rewrite mode, direct OpenAI client coupling in `game.gm.call_gpt`, absence of a ruleset registry/version contract, and raw internal FastAPI dicts serving as the current UI/tooling interface.

No evidence found requires reopening the transaction spine, state authority model, CTIR boundary, final-emission boundary, persistence model, or replay governance model. The next cycles should primarily validate/reconcile known overlaps, then investigate specific local seams that prior campaigns already identified: final-emission semantic residue, ruleset/backend/version bundle boundaries, and public UI/tooling/plugin-adapter facade.

Recommended next cycle: `AR-BF Final-Emission and Defensive Runtime Overlap Validation`.

## 2. Prior Architectural Decisions Recovered

| Decision or doctrine | Source document | Boundary families affected | Current implementation evidence | Still authoritative |
|---|---|---|---|---|
| Runtime truth flows forward from transaction to domain simulation, CTIR, prompt/adaptation, realization, final emission, persistence, replay/evidence, governance. | `AR-BD_concept_map_synthesis_and_campaign_closeout.md` | Runtime orchestration, domain simulation, AI interaction, final emission, replay/evidence, governance | `game/api.py` has transaction entry points (`action`, `chat`, `start_campaign`), `_run_resolved_turn_pipeline`, CTIR attach, GPT call, final-emission finalize, save/log calls. | Yes. Confirmed by docs and code shape. |
| Domain simulation owns game truth; GPT/prompt/final text/replay do not mutate truth. | `AR-BD_concept_map_synthesis_and_campaign_closeout.md`, `docs/state_authority_model.md` | Domain simulation, state authority, AI interaction, final emission, replay | `game/state_authority.py` guards; `tests/test_state_authority.py`; `game/world.py`, `game/world_progression.py`, `game/noncombat_resolution.py`, `game/social.py`, `game/combat.py`. | Yes. |
| State authority is registry/guard vocabulary, not persistence or prompt policy. | `docs/state_authority_model.md`, `docs/architecture_ownership_ledger.md` | Evidence/provenance, persistence, UI projection, domain simulation | `StateDomainSpec`, `CrossDomainWriteSpec`, `assert_owner_can_mutate_domain`, `assert_cross_domain_write_allowed` in `game/state_authority.py`; direct tests in `tests/test_state_authority.py`. | Yes. |
| CTIR is resolved-turn meaning, separate from prompt text and turn packet. | `docs/system_overview.md`, `docs/architecture_ownership_ledger.md`, `AR-BD...` | Runtime orchestration, AI interaction, replay/projection | `game/ctir.py`, `game/ctir_runtime.py`, `game/turn_packet.py`; `tests/test_ctir_turn_packet_boundary.py`, `tests/test_prompt_context_ctir_consumption.py`. | Yes. |
| Prompt/adaptation packages truth for expression and does not create truth. | `AR-BD...`, `docs/system_overview.md` | AI interaction, domain simulation, UI/read models | `game/prompt_context.py:build_narration_context`, `build_response_policy`, imports CTIR/read models/contracts; state-authority tests reject prompt context as truth mutator. | Yes. |
| Realization/GPT owns candidate expression only. | `AR-BD...`, `AR-AI_final_vision_compatibility_closeout.md` | AI interaction, final emission, provenance | `game/gm.py:call_gpt`, `game/model_routing.py:resolve_model_route`, `game/realization_authority.py`, `game/realization_provenance.py`. | Yes, with backend-adapter refinement pending. |
| Final emission owns final legality, selection, packaging, FEM/meta, and sealed terminal exceptions, not ordinary domain truth or semantic authoring. | `AR-BB_defensive_runtime_boundary_reconciliation.md`, `AR-BD...`, `docs/architecture_ownership_ledger.md` | Final emission, diagnostics, evidence/provenance | `game/final_emission_gate.py:apply_final_emission_gate`, `game/final_emission_runtime.py:finalize_player_facing_emission`, `game/final_emission_boundary_contract.py`, `tests/test_final_emission_boundary_contract.py`. | Yes, with transitional semantic-repair residue. |
| Validators, repair, sanitizers, fallback, and final emission are distinct defensive concepts with hierarchical and orthogonal overlaps. | `AR-BB...` | Final emission, diagnostics, evidence/provenance | `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, `game/final_emission_gate.py`; many direct-owner tests. | Yes. |
| Replay/projection/evidence observe finalized surfaces; replay must not become runtime authority. | `AR-BD...`, `docs/testing/replay_governance_authority.md` | Replay/projection, evidence, governance | `game/final_emission_replay_projection.py`, tests under `tests/test_golden_replay_*`, `tests/test_replay_boundary_governance.py`. | Yes. |
| Governance declares and watches; it does not execute gameplay. | `AR-BD...`, `docs/testing/replay_governance_authority.md`, `docs/architecture_ownership_ledger.md` | Governance, tooling, replay | `tests/ownership_registry_contract.py`, `tests/ownership_inventory_governance.py`, replay governance contract/registry/approval/traceability tests. | Yes. |
| Ruleset support is architecturally enabled but lacks registry/version/selection contract. | `AR-AG_final_vision_compatibility_discovery.md`, `AR-AI_final_vision_compatibility_closeout.md` | Ruleset architecture, plugins/adapters, provenance | Domain/rules modules exist (`game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`), but no ruleset registry or package contract was found. | Yes as an unresolved local seam. |
| Multiple AI backends are enabled by model routing but need a provider-neutral adapter before second provider/local inference. | `AR-AG...`, `AR-AI...` | AI interaction, plugins/adapters, provenance, UI/tooling | `game/model_routing.py`; `tests/test_model_routing_*`; `game/gm.py:call_gpt` remains OpenAI-specific. | Yes. |
| Local UI/tooling can proceed through UI mode/state-channel projection, but external tooling needs a public command/query facade. | `AR-AG...`, `AR-AI...`, `docs/system_overview.md` | UI integration, tooling, persistence | `game/ui_mode_policy.py`, `game/state_channels.py`, `game/api.py:_project_state_for_ui_mode`, `static/app.js`, `tests/test_ui_mode_backend_integration.py`. | Yes. |

## 3. Repository Boundary Map

### Runtime Orchestration

Purpose: coordinate one live turn from request entry through resolution, CTIR, realization, final emission, persistence/log/response.

Primary modules and files: `game/api.py`, `game/api_turn_support.py`, `game/session.py`, `run.py`.

Principal interfaces or symbols: `action`, `chat`, `start_campaign`, `_run_resolved_turn_pipeline`, `_apply_post_gm_updates`, `_build_gpt_narration_from_authoritative_state`, `_complete_opening_turn_persistence_like_chat`.

Upstream dependencies: HTTP/UI requests, `game.models` request DTOs, storage load functions.

Downstream dependencies: domain modules (`world`, `combat`, `social`, `noncombat_resolution`, `clues`, `leads`), CTIR, prompt context, GPT/model routing, final emission, persistence/logging, UI projection.

State authority: orchestrates scene/session/world mutations under state-authority guard seams; does not own all domain meanings.

Relevant tests: `tests/test_start_campaign_api.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_api_narration_path_selection.py`, `tests/test_ctir_pipeline_integration.py`, `tests/test_runtime_persistence_regression_suite_obj14.py`.

Documentation: `AR-BD...`, `docs/system_overview.md`, `docs/state_authority_model.md`.

Compatibility support: large `game/api.py` contains post-GM adoption gateways and local compatibility paths; this is implementation concentration, not by itself architectural ownership collapse.

### Domain Simulation

Purpose: decide game truth and structured outcomes before expression.

Primary modules and files: `game/world.py`, `game/world_progression.py`, `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/social.py`, `game/clues.py`, `game/leads.py`, `game/clocks.py`, `game/scene_graph.py`, `game/scene_actions.py`, `game/interaction_context.py`.

Principal interfaces or symbols: `apply_resolution_world_updates`, `advance_world_tick`, `apply_progression_delta`, `resolve_attack`, `resolve_skill_check`, `resolve_noncombat_action`, `resolve_social_action`, `apply_authoritative_clue_discovery`, `upsert_lead`, `advance_session_lead_lifecycle`, `is_transition_valid`.

Upstream dependencies: runtime orchestration, authored content, current state documents.

Downstream dependencies: CTIR slices, prompt/adaptation read models, persistence, final-emission constraints, UI projections.

State authority: owns authoritative mutations for world, scene, interaction, hidden/publication seams according to `game/state_authority.py`.

Relevant tests: `tests/test_world_state.py`, `tests/test_world_progression_backbone.py`, `tests/test_combat_resolution.py`, `tests/test_noncombat_resolution.py`, `tests/test_social_interaction_authority.py`, `tests/test_lead_*`, `tests/test_clue_*`, `tests/test_scene_transition_authority.py`.

Documentation: `docs/state_authority_model.md`, `docs/world_simulation_backbone.md`, `docs/system_overview.md`.

Compatibility support: legacy raw fields and CTIR absent fallbacks exist, but doctrine says contracts own meaning when present.

### Ruleset Architecture

Purpose: currently provides PF1e-inspired mechanics and structured action resolution; long-term would isolate ruleset identity, selection, versioning, and adapters.

Primary modules and files: `game/combat.py`, `game/skill_checks.py`, `game/conditions.py`, `game/noncombat_resolution.py`, `game/schema_contracts.py`, `game/models.py`, `data/character.json`, `data/combat.json`.

Principal interfaces or symbols: `resolve_attack`, `resolve_skill`, `resolve_spell`, `resolve_skill_check`, `should_trigger_check`, `normalize_noncombat_resolution`.

Upstream dependencies: runtime orchestration, character/combat/scene content.

Downstream dependencies: domain state, CTIR, prompt contracts, replay/provenance.

State authority: ruleset mechanics may compute outcomes but must mutate through domain owner seams.

Relevant tests: `tests/test_combat_resolution.py`, `tests/test_skill_checks.py`, `tests/test_noncombat_runtime_integration.py`, `tests/test_ctir_noncombat_consumption.py`.

Documentation: `AR-AG...`, `AR-AH_final_vision_compatibility_assessment.md`, `AR-AI...`.

Compatibility support: no alternate-ruleset registry, package manifest, or selection/version contract found. This is a local architectural refinement before alternate rulesets, not evidence that current mechanics are unstable.

### AI Interaction

Purpose: package approved truth for model expression, route model calls, handle upstream responses/errors, and record realization provenance.

Primary modules and files: `game/prompt_context.py`, `game/model_routing.py`, `game/gm.py`, `game/gm_retry.py`, `game/upstream_response_repairs.py`, `game/api_upstream_preflight.py`, `game/realization_authority.py`, `game/realization_provenance.py`, `game/response_policy_contracts.py`, `game/response_policy_enforcement.py`.

Principal interfaces or symbols: `build_narration_context`, `build_response_policy`, `resolve_model_route`, `call_gpt`, `apply_response_policy_enforcement`, `build_upstream_prepared_emission_payload`, `attach_realization_fallback_family`.

Upstream dependencies: CTIR, prompt contracts, model configuration, state/read models.

Downstream dependencies: candidate GM output, final emission, provenance, runtime lineage, replay projections.

State authority: no authoritative domain mutation from GPT text; structured effects are validated and applied by engine/API seams.

Relevant tests: `tests/test_prompt_context.py`, `tests/test_prompt_context_ctir_boundary.py`, `tests/test_model_routing_config.py`, `tests/test_model_routing_runtime.py`, `tests/test_response_policy_enforcement_mutation.py`.

Documentation: `docs/system_overview.md`, `docs/architecture_ownership_ledger.md`, `AR-AI...`.

Compatibility support: direct OpenAI Responses API path remains in `game.gm.call_gpt`; prior campaigns classify provider-neutral backend adapter as local refinement before adding providers.

### Final Emission

Purpose: last-mile final selection, legality, packaging, FEM/meta, sealed terminal exceptions, and traceable output.

Primary modules and files: `game/final_emission_runtime.py`, `game/final_emission_gate.py`, `game/final_emission_terminal_pipeline.py`, `game/final_emission_boundary_contract.py`, `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/final_emission_meta.py`, `game/final_emission_finalize.py`.

Principal interfaces or symbols: `finalize_player_facing_emission`, `apply_final_emission_gate`, `run_gate_terminal_enforcement_pipeline`, `assert_final_emission_mutation_allowed`, `sanitize_player_facing_output`.

Upstream dependencies: GPT/fallback candidate, response contracts, CTIR/turn packet context, sanitizer/repair helpers.

Downstream dependencies: persistence/log/response, runtime diagnostic projection, protected replay projection, evidence/tests.

State authority: may package/select final player-facing output; must not mutate authoritative domain truth or silently invent ordinary missing meaning.

Relevant tests: `tests/test_final_emission_boundary_contract.py`, `tests/test_final_emission_gate_orchestration_order.py`, `tests/test_final_emission_boundary_no_semantic_repair.py`, `tests/test_final_emission_repairs.py`, `tests/test_output_sanitizer.py`, `tests/test_final_emission_meta.py`.

Documentation: `AR-BB...`, `AR-BD...`, `docs/architecture_ownership_ledger.md`.

Compatibility support: semantic repair residue, legacy sanitizer rewrite mode, dual fallback vocabulary, and compatibility facades are drift-watch/transitional.

### Replay and Projection

Purpose: observe finalized runtime surfaces and convert them into diagnostic/protected replay forms without driving runtime behavior.

Primary modules and files: `game/final_emission_replay_projection.py`, `game/ownership_projection_views.py`, `game/runtime_lineage_telemetry.py`, `tests/test_golden_replay_*`, `tests/replay_governance_*.py`, `tools/replay_maintenance_metrics.py`, `tools/projection_drift_watch.py`.

Principal interfaces or symbols: `normalize_fem_for_replay_acceptance`, `read_fem_from_turn_for_replay`, `build_fem_runtime_lineage_events`, replay governance contract validators.

Upstream dependencies: finalized FEM, logs, traces, runtime snapshots.

Downstream dependencies: tests, audits, scorecards, evidence reports, governance registry.

State authority: none over live runtime; read-side observation only.

Relevant tests: `tests/test_replay_boundary_governance.py`, `tests/test_golden_replay_projection_engine.py`, `tests/test_golden_replay_projection_governance.py`, `tests/test_golden_replay_projection_registry.py`.

Documentation: `docs/testing/replay_governance_authority.md`, `docs/testing/replay_governance_contract.md`, `AR-BD...`.

Compatibility support: acceptance projection and runtime diagnostic projection remain separate by explicit tests.

### Evidence and Provenance

Purpose: explain finalized behavior, owner/path contribution, fallback family, mutation lineage, and architectural claims.

Primary modules and files: `game/realization_provenance.py`, `game/fallback_provenance_debug.py`, `game/final_emission_meta.py`, `game/runtime_lineage_telemetry.py`, `game/semantic_mutation_attribution.py`, `tools/*_report.py`, `artifacts/`, `audits/`.

Principal interfaces or symbols: `attach_realization_fallback_family`, `normalize_realization_fallback_family`, lineage event builders, report generators.

Upstream dependencies: runtime metadata, final-emission metadata, replay projections.

Downstream dependencies: audits, governance, scorecards, trend reports, external review files.

State authority: records/explains behavior; does not select fallback, mutate truth, or decide runtime outcomes.

Relevant tests: `tests/test_realization_provenance.py`, `tests/test_fallback_projection_coverage_audit.py`, `tests/test_semantic_mutation_attribution_governance.py`, `tests/test_attribution_contract.py`.

Documentation: `AR-BB...`, `AR-BD...`, `AR-BC_permanent_transitional_historical_concept_classification.md`.

Compatibility support: generated/advisory evidence fanout is explicitly transitional unless promoted by governance.

### Diagnostics and Telemetry

Purpose: explain paths, failures, stage diffs, route decisions, and ownership lineage without becoming hidden policy.

Primary modules and files: `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`, `game/telemetry_vocab.py`, `game/dead_turn_report_visibility.py`, `tools/fallback_incidence_report.py`, `tools/failure_dashboard_*`, `artifacts/architecture_audit/*`.

Principal interfaces or symbols: stage diff snapshots, lineage normalization helpers, `storage.append_debug_trace`.

Upstream dependencies: runtime transaction, final emission, state mutation traces.

Downstream dependencies: debug UI, audits, tests, governance reports.

State authority: diagnostic; may be emitted/stored but should not alter outcomes.

Relevant tests: `tests/test_stage_diff_telemetry.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/test_dead_turn_report_visibility.py`, `tests/test_debug_payload_spoiler_safety.py`.

Documentation: `docs/architecture_ownership_ledger.md`, `AR-BD...`.

Compatibility support: debug/author/player channel projection guards protect player surfaces from diagnostic leakage.

### Persistence

Purpose: load/save runtime documents, logs, scenes, snapshots, and persistence envelope mechanics.

Primary modules and files: `game/storage.py`, `game/persistence_contract.py`, `game/campaign_state.py`, `game/campaign_reset.py`, `data/*.json`, `data/scenes/*.json`.

Principal interfaces or symbols: `load_session`, `save_session`, `load_world`, `save_world`, `load_active_scene`, `activate_scene`, `append_log`, `create_snapshot`, `build_effective_scene`.

Upstream dependencies: runtime transaction and domain owners.

Downstream dependencies: API state composition, replay/evidence, UI, tests.

State authority: owns I/O mechanics and lazy structural roots; does not own domain semantics or transaction timing.

Relevant tests: `tests/test_save_load.py`, `tests/test_runtime_persistence_regression_suite_obj14.py`, `tests/test_project_schema.py`, `tests/test_activate_scene_validation_and_get_persistence.py`.

Documentation: `docs/runtime_persistence_envelope.md`, `docs/state_authority_model.md`, `AR-BD...`.

Compatibility support: load-time adapters and lazy init seams are intentionally scoped and tested as not direct semantic mutation owners.

### Governance

Purpose: declare ownership, authority, canonicality, test placement, replay governance, and compatibility residue handling.

Primary modules and files: `docs/architecture_ownership_ledger.md`, `docs/state_authority_model.md`, `docs/testing/replay_governance_authority.md`, `tests/ownership_registry_contract.py`, `tests/ownership_inventory_governance.py`, `tests/test_ownership_registry.py`, `tests/replay_governance_*.py`.

Principal interfaces or symbols: ownership registry records, governance inventory checks, replay governance record validators.

Upstream dependencies: doctrine and evidence.

Downstream dependencies: direct-owner tests, audits, future campaign instructions.

State authority: governance-only; not a gameplay executor.

Relevant tests: `tests/test_ownership_registry.py`, `tests/test_replay_governance_authority.py`, `tests/test_compat_import_governance.py`.

Documentation: prior AR campaign reports, ledger docs, replay governance docs.

Compatibility support: allows historical aliases and import barrels under explicit caps/registries.

### Tooling

Purpose: offline inspection, audits, linting, measurement, report generation, replay refresh, and maintenance diagnostics.

Primary modules and files: `tools/*.py`, `scripts/*.py`, `docs/architecture_audit_*`, `artifacts/`.

Principal interfaces or symbols: `tools/run_content_lint.py:main`, `tools/architecture_audit.py`, `tools/final_emission_ownership_audit.py`, `tools/validation_layer_audit.py`, replay/fallback/report scripts.

Upstream dependencies: repository files, test outputs, runtime logs/artifacts.

Downstream dependencies: reports, audits, governance decisions.

State authority: offline/advisory except where explicitly used in CI; not production runtime authority.

Relevant tests: `tests/test_content_lint_tool.py`, `tests/test_architecture_audit_tool.py`, `tests/test_validation_layer_audit_smoke.py`, `tests/test_test_audit_tool.py`.

Documentation: `docs/architecture_audit_readme.md`, `docs/content_lint_pipeline.md` if present, `docs/system_overview.md`.

Compatibility support: generated reports are evidence unless promoted by governance.

### UI Integration

Purpose: project runtime state into player/author/debug views and transport commands through the local browser/FastAPI UI.

Primary modules and files: `static/app.js`, `static/index.html`, `static/styles.css`, `game/api.py`, `game/ui_mode_policy.py`, `game/state_channels.py`, `game/api_ui_mode.py`.

Principal interfaces or symbols: `compose_state`, `_project_state_for_ui_mode`, `resolve_requested_ui_mode`, `get_ui_mode_policy`, `project_public_payload`, `deep_project_debug_payload`.

Upstream dependencies: persisted state, runtime logs, UI mode query/payload.

Downstream dependencies: browser rendering, local operator/debug workflows.

State authority: presentation/projection only; UI state must not become authoritative runtime truth.

Relevant tests: `tests/test_ui_mode_backend_integration.py`, `tests/test_frontend_ui_mode_hardening_objective15.py`, `tests/test_ui_mode_policy.py`, `tests/test_state_channels.py`.

Documentation: `AR-AG...`, `AR-AI...`, `docs/system_overview.md`.

Compatibility support: current API is internal dict-oriented; prior campaigns recommend public facade before external tooling/hosted integrations.

### Plugins and Adapters

Purpose: import/adapter seams and future extension packaging; currently narrow importers and compatibility barrels rather than a general plugin framework.

Primary modules and files: `game/importers/pf_json_importer.py`, compatibility import modules/facades, `tests/test_compat_import_governance.py`.

Principal interfaces or symbols: `import_sheet`, compat import governance collectors, barrel fan-in caps.

Upstream dependencies: external character sheet JSON, legacy import paths, future backend/ruleset/tool decisions.

Downstream dependencies: API import endpoint, character state, tests/governance.

State authority: adapters translate inputs; they should not bypass validation, governance, or domain owner mutation seams.

Relevant tests: `tests/test_compat_import_governance.py`, importer-related tests.

Documentation: `AR-AG...`, `AR-AI...`, compatibility closeouts and governance docs.

Compatibility support: no generic plugin architecture found; prior doctrine explicitly defers generic plugin systems until product evidence requires them.

### Content

Purpose: authored campaign/world/scene data and author-time validation/linting.

Primary modules and files: `data/world.json`, `data/campaign.json`, `data/character.json`, `data/combat.json`, `data/session.json`, `data/scenes/*.json`, `game/validation.py`, `game/content_lint.py`, `game/scene_lint.py`, `tools/run_content_lint.py`.

Principal interfaces or symbols: `validate_scene`, `validate_all_scenes`, `lint_all_content`, `build_content_bundle`, `lint_bundle_governance`.

Upstream dependencies: authored JSON content and optional world registry references.

Downstream dependencies: storage, domain simulation, UI, content lint reports.

State authority: content supplies templates/definitions; runtime owners decide mutations and reveal/publication.

Relevant tests: `tests/test_content_lint.py`, `tests/test_content_lint_tool.py`, `tests/test_scene_validation.py`, `tests/test_scene_graph.py`, `tests/test_clocks_projects_logging_lint.py`.

Documentation: `docs/system_overview.md`, content lint notes/tests.

Compatibility support: author-time lint is deterministic tooling, not gameplay hot-path authority.

## 4. Preliminary Boundary Classification Matrix

| Boundary family | Preliminary classification | Permanent responsibility | Explicit exclusions | Intentional overlaps | Transitional overlap or compatibility support | Implementation alignment | Likely future change type | Confidence | Key evidence |
|---|---|---|---|---|---|---|---|---|---|
| Runtime orchestration | Stable with intentional overlap | Coordinate one transaction and handoffs | Domain truth ownership, replay authority | API orchestrates domain, CTIR, GPT, final emission, persistence | Large API hub and adoption gateways | Strong but concentrated | Interface clarification, dependency cleanup | High | `game/api.py`, `AR-BD...`, `tests/test_turn_pipeline_shared.py` |
| Domain simulation | Stable | Authoritative outcomes/state transitions | GPT prose, final text, replay projection | API orchestration, CTIR projection, persistence | Legacy/raw fields and compatibility reads | Strong | Implementation completion, test coverage | High | `game/world.py`, `game/noncombat_resolution.py`, `game/social.py`, `docs/state_authority_model.md` |
| Ruleset architecture | Architecturally unresolved | Mechanics/rules outcome contract | Generic plugin system, simultaneous rulesets by default | Domain simulation, provenance/versioning | Current PF1e-inspired modules without registry | Partial | Local architectural refinement | Medium-High | `AR-AG...`, `AR-AI...`, no ruleset registry found |
| AI interaction | Transitional | Prompt/adaptation, model routing, candidate expression, upstream repair packaging | Domain truth, final legality | CTIR consumption, realization provenance, fallback | Direct OpenAI client, no provider-neutral adapter | Strong for current provider | Adapter/interface clarification | High | `game/prompt_context.py`, `game/model_routing.py`, `game/gm.py:call_gpt`, `AR-AI...` |
| Final emission | Stable with intentional overlap | Final selection, legality, packaging, FEM/meta, sealed exceptions | Domain truth, ordinary semantic authoring | Validators, repair, sanitizer, fallback, provenance | Semantic repair residue, sanitizer legacy rewrite | Strong, heavily guarded | Compatibility retirement, focused validation | High | `AR-BB...`, `game/final_emission_boundary_contract.py`, `tests/test_final_emission_boundary_contract.py` |
| Replay/projection | Stable | Read finalized surfaces into replay/protected/diagnostic forms | Runtime mutation, fallback selection, final legality | Evidence/governance/reporting | Projection fanout and compat fields | Strong | Documentation/test coverage | High | `game/final_emission_replay_projection.py`, `tests/test_replay_boundary_governance.py` |
| Evidence/provenance | Stable with intentional overlap | Record/explain source, owner, family, lineage | Selecting behavior or mutating results | Fallback, final emission, replay, governance | Dual fallback/provenance vocabulary | Strong but vocabulary dense | Interface clarification, documentation | Medium-High | `game/realization_provenance.py`, `game/fallback_provenance_debug.py`, `AR-BB...` |
| Diagnostics/telemetry | Stable | Explain paths/stage changes/lineage | Hidden runtime policy or player text authority | Final emission, replay, UI debug | Debug/author channel projection | Strong | Test coverage and channel hygiene | Medium-High | `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`, `tests/test_debug_payload_spoiler_safety.py` |
| Persistence | Stable with intentional overlap | I/O, envelopes, snapshots, logs | Domain semantics, transaction timing | Runtime orchestration, replay, UI state composition | Lazy structural roots, load adapters | Strong | Documentation/test coverage | High | `game/storage.py`, `docs/runtime_persistence_envelope.md`, `tests/test_save_load.py` |
| Governance | Stable | Doctrine, ownership ledgers, test governance, replay governance | Gameplay execution, replay running/classification | Evidence, tests, compatibility registers | Historical docs and generated inventories | Strong | Documentation maintenance | High | `docs/architecture_ownership_ledger.md`, `docs/testing/replay_governance_authority.md` |
| Tooling | Stable with intentional overlap | Offline inspection/lint/audit/report generation | Production runtime authority | Governance/evidence/content/replay | Generated advisory artifacts | Mostly strong | Test coverage, documentation | Medium | `tools/*.py`, `tests/test_content_lint_tool.py`, `tests/test_architecture_audit_tool.py` |
| UI integration | Transitional | Project state by mode/channel and transport local commands | Authoritative runtime truth | API, persistence, state channels | Internal dict API; no public facade | Good local alignment | Interface clarification/local facade | High | `game/ui_mode_policy.py`, `game/state_channels.py`, `static/app.js`, `tests/test_ui_mode_backend_integration.py` |
| Plugins/adapters | Transitional | Translate external/import/compat inputs without bypassing owners | Generic extension authority | Ruleset/backend/tooling/future public API | PF importer and compatibility barrels only | Narrow and governed | Architectural refinement before expansion | Medium | `game/importers/pf_json_importer.py`, `tests/test_compat_import_governance.py`, `AR-AI...` |
| Content | Stable with intentional overlap | Authored definitions and author-time lint/validation | Runtime orchestration or state mutation policy | Storage, domain simulation, content tooling | Lint vs runtime validation split | Strong | Test coverage, implementation completion | High | `game/content_lint.py`, `game/validation.py`, `data/*.json`, `tests/test_content_lint.py` |

## 5. Cross-Boundary Flow Traces

### Flow A: Normal Chat / Action Turn

1. Request entry - Runtime orchestration: `game/api.py:action` or `game/api.py:chat` accepts DTOs and UI mode.
2. State load - Persistence participates: `game/storage.py` loads session/world/scene/combat; storage does not decide semantics.
3. Intent/action routing - Runtime orchestration plus domain modules: `game/intent_parser.py`, `game/scene_actions.py`, `game/social.py`, `game/noncombat_resolution.py`.
4. Authoritative resolution - Domain simulation owns outcome: combat/social/noncombat/world/lead/clue modules produce structured effects.
5. Mutation/hygiene - State authority constrains owner writes: `game/state_authority.py` guards; `game/api.py` orchestrates timing.
6. CTIR attach - CTIR owns resolved-turn meaning: `game/ctir_runtime.py:ensure_ctir_for_turn` and `game/ctir.py:build_ctir`.
7. Prompt packaging - AI interaction adapts truth: `game/prompt_context.py:build_narration_context`; no truth mutation.
8. Model realization - AI interaction calls `game/gm.py:call_gpt`, routed by `game/model_routing.py`.
9. Upstream repair/prepared payload - AI interaction may attach bounded upstream-prepared emission via `game/upstream_response_repairs.py`.
10. Final emission - Final emission owns legality/selection/packaging via `finalize_player_facing_emission` and `apply_final_emission_gate`.
11. Persistence/log/response - Persistence stores documents/logs; API returns projected result.
12. Replay/evidence - Replay/projection later reads finalized FEM/logs/traces; no feedback into runtime.

### Flow B: Campaign Startup

1. Request entry - Runtime orchestration: `game/api.py:start_campaign`.
2. Reset/bootstrap - Persistence/state factories: `game/campaign_state.py:create_fresh_*`, `game/campaign_reset.py`.
3. Opening resolution - Runtime orchestration/domain scene state: `_build_opening_scene_resolution`, opening visible fact selection/realization modules.
4. CTIR/prompt - CTIR and prompt/adaptation package opening meaning.
5. Realization/fallback - GPT candidate or deterministic opening fallback may produce candidate expression.
6. Final emission - Gate selects/packages legal player-facing opening; final text is not domain truth.
7. Save/log/UI projection - `save_world`, `save_session`, `append_log`, `_project_state_for_ui_mode`.

### Flow C: Upstream Failure / Fallback

1. Model call fails or candidate unusable - AI interaction/runtime orchestration detects failure.
2. Retry/fallback selection - `game.gm_retry`, `game.upstream_response_repairs`, deterministic fallback modules may produce bounded substitute behavior.
3. Provenance records path - `game/fallback_provenance_debug.py` and `game/realization_provenance.py` explain, not select.
4. Final emission validates and packages - gate may apply sealed terminal exception or strict-social fallback; mutation contract rejects semantic-disallowed boundary mutations.
5. Replay projection observes fallback fields - `game/final_emission_replay_projection.py` normalizes finalized data for replay/evidence.

### Flow D: UI State Projection

1. Browser requests `/api/state?ui_mode=...` - UI integration/API.
2. `game/api.py:compose_state` reads persisted state and derived journal.
3. `game/api_ui_mode.py:resolve_requested_ui_mode` and `game/ui_mode_policy.py` select mode.
4. `game/api.py:_project_state_for_ui_mode` applies `game/state_channels.py` channel projection.
5. `static/app.js` renders the returned mode-specific payload and clears forbidden DOM content on mode changes.
6. UI remains projection/transport; domain owners and API orchestration remain authoritative for runtime mutation.

### Flow E: Content Lint / Author-Time Tooling

1. Operator invokes `tools/run_content_lint.py`.
2. Tool loads authored scene/world content; it does not run gameplay.
3. `game/content_lint.py:lint_all_content` and `game/validation.py:validate_scene` produce findings.
4. Output is evidence/tooling; governance or content authors may act later.
5. Runtime semantics are unchanged until content files or runtime code are deliberately modified.

## 6. Boundary Pressure Points

| Identifier | Boundaries involved | Files and symbols | Observed condition | Why it may matter | Preliminary classification | Evidence still needed | Later cycle |
|---|---|---|---|---|---|---|---|
| BE-PP1 Final-boundary semantic repair residue | Final emission, AI interaction, domain simulation | `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/final_emission_boundary_contract.py`, `docs/architecture_ownership_ledger.md` | Doctrine says semantic repair at final boundary is transitional; mutation contract fences disallowed kinds. | Boundary could regress from legality/packaging into semantic authoring. | Transitional/defensive, not unresolved. | Symbol-level inventory of remaining semantic mutation sites after current closeouts. | Mandatory AR-BF. |
| BE-PP2 Large runtime orchestration hub | Runtime orchestration, domain simulation, AI, final emission, persistence | `game/api.py` (`_run_resolved_turn_pipeline`, `_apply_post_gm_updates`, `chat`, `action`) | API coordinates many handoffs and contains adoption gateways. | Concentration may hide ownership leakage, though doctrine allows orchestration participation. | Implementation pressure, not architecture violation by itself. | Focused caller/callee inventory for adoption gateways. | Conditional under AR-BF or later. |
| BE-PP3 Ruleset identity absent | Ruleset architecture, provenance, replay, plugins/adapters | No ruleset registry/manifest found; mechanics in `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py` | Current rules work, but alternate rulesets lack identity/version/selection boundary. | Blocks future alternate ruleset without local seam. | Architecturally unresolved local seam. | Product decision: one active ruleset vs coexistence; minimum registry/version fields. | Mandatory AR-BG if alternate rulesets remain in roadmap. |
| BE-PP4 Provider-neutral backend absent | AI interaction, plugins/adapters, provenance, UI/tooling | `game/model_routing.py`, `game/gm.py:call_gpt`, `tests/test_model_routing_runtime.py` | Routing exists; provider call path remains OpenAI-specific. | Second provider/local inference would couple into realization path without adapter. | Transitional/local refinement. | Backend protocol scope, fake backend expectations, provenance fields. | Mandatory AR-BG or AR-BH. |
| BE-PP5 Public UI/tooling facade absent | UI integration, tooling, persistence, governance | `game/api.py`, `game/ui_mode_policy.py`, `game/state_channels.py`, `static/app.js` | Local UI is guarded; external/public API remains raw dict-oriented. | External tools/hosted UI could couple to internal storage shapes. | Transitional. | Product target: local-only vs external/hosted; command/query/event schema. | Conditional AR-BH. |
| BE-PP6 Dual fallback/provenance vocabulary | Fallback, provenance, replay/projection, final emission | `game/realization_provenance.py`, `game/fallback_provenance_debug.py`, `game/final_emission_replay_projection.py` | Prior docs classify dual fallback-family vocabulary as transitional/read-compatibility pressure. | Could be mistaken for duplicate ownership. | Transitional compatibility, not violation. | Field permanence/read precedence table. | Mandatory under AR-BF if not already adequate. |
| BE-PP7 Compatibility import barrels | Governance, tooling, final emission/social/replay | `tests/test_compat_import_governance.py`, compat modules | Fan-in caps and allowed importer registries guard legacy import paths. | Compatibility paths can become permanent by accident. | Transitional/governed. | Current fan-in report and allowed importer deltas. | Conditional. |
| BE-PP8 Generated/advisory evidence fanout | Evidence, governance, tooling | `artifacts/`, `audits/`, many `tools/*_report.py` | Reports are numerous and useful, but doctrine says generated/advisory artifacts are not authority unless promoted. | Risk of citing stale generated outputs as current doctrine. | Stable with governance caveat. | Canonicality labels for most-used reports. | Conditional. |
| BE-PP9 UI/debug leakage risk | UI integration, diagnostics, player-visible state | `game/state_channels.py`, `game/ui_mode_policy.py`, `static/app.js`, tests | Mode/channel tests guard projections. | Hidden/debug data must not leak to player surfaces or prompts. | Stable with intentional overlap. | None blocking; keep tests current. | Not mandatory. |
| BE-PP10 Content lint vs runtime validation | Content, tooling, domain simulation | `game/content_lint.py`, `game/validation.py`, `tools/run_content_lint.py` | Author-time lint and runtime validation have different responsibilities. | Tool findings should not become hidden runtime authority. | Stable with intentional overlap. | None blocking. | Not mandatory. |

## 7. Stable Boundary Evidence

- State authority is explicit and executable: `game/state_authority.py` defines five canonical domains, read matrix, owner guards, cross-domain allow-list, and mutation traces; `tests/test_state_authority.py` directly locks registry shape and deferrals.
- CTIR is separate from prompt and turn packet: `game/ctir.py`, `game/ctir_runtime.py`, and `game/turn_packet.py` have separate symbols and tests (`tests/test_ctir_turn_packet_boundary.py`) proving turn packet is not CTIR.
- Prompt/adaptation is read-side packaging: `game/prompt_context.py:build_narration_context` consumes CTIR/state/contracts; state authority docs/tests classify prompt as non-authoritative for domain mutation.
- Final emission has a formal mutation taxonomy: `game/final_emission_boundary_contract.py` distinguishes packaging allowed, legality allowed, and semantic disallowed mutation kinds; tests fail closed on unknown/disallowed kinds.
- Replay projection is read-side: `game/final_emission_replay_projection.py` reads finalized FEM/metadata; `tests/test_replay_boundary_governance.py` asserts runtime and acceptance projection modules remain separate.
- Governance hierarchy is explicit: `docs/testing/replay_governance_authority.md` declares replay governance contract, registry, approval, traceability, and reporting consumer levels and excludes replay execution/classification.
- UI projection is mode/channel governed: `game/ui_mode_policy.py` and `game/state_channels.py` define player/author/debug projections; backend and frontend tests guard mode-specific leakage and DOM clearing.
- Content lint is author-time tooling: `game/content_lint.py` and `tools/run_content_lint.py` have dedicated tests that distinguish engine rule matrices from CLI/tool policy.
- Persistence is mechanics, not domain semantics: `game/storage.py` owns I/O, lazy roots, overlays, logs, snapshots; `docs/state_authority_model.md` explicitly keeps storage from becoming policy except load/shape mechanics.
- Compatibility support is governed rather than invisible: `tests/test_compat_import_governance.py` caps import barrels and demands registry updates for new importers.

## 8. Remaining Evidence Gaps

| Exact question | Why it matters | Files, runtime evidence, or human decisions needed | Can later work proceed without it |
|---|---|---|---|
| Which final-emission repair symbols remain semantic rather than legality/packaging? | Needed to retire or bless final-boundary overlap without reopening the whole boundary. | Symbol-level audit of `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/final_emission_*` policy modules, current tests. | Yes for discovery; no for AR-BF closeout. |
| What is the intended minimum ruleset contract? | Alternate rulesets need identity/version/selection/adapters before implementation. | Human decision plus docs/code proposal; inspect mechanics modules and provenance/replay needs. | Yes unless alternate ruleset work begins. |
| What provider/backend capabilities must be abstracted first? | Prevents direct OpenAI-specific branching from hardening when adding providers. | `game/gm.py:call_gpt`, `game/model_routing.py`, tests, product decision for streaming/tools/local inference. | Yes for current provider; no before second provider. |
| Should public UI/tooling be local-only, external, hosted, or multi-user? | Determines whether internal FastAPI dicts are acceptable or need facade/versioning. | Human product decision; inspect `game/api.py` endpoints and `static/app.js` coupling. | Yes for local UI; no before external/hosted tooling. |
| Which generated reports are canonical enough for future campaigns? | Prevents stale/advisory evidence from becoming doctrine accidentally. | Governance labels or minimal evidence-source registry for high-use reports. | Yes if AR-BE summarizes enough. |
| What plugin scope is real: rulesets, AI backends, tools, content packs, UI extensions, or none? | Avoids building generic plugin architecture too early or letting adapters bypass governance. | Human product decision and feature roadmap. | Yes until plugin work begins. |

## 9. Recommended Campaign Decomposition

### AR-BF Final-Emission and Defensive Runtime Overlap Validation

Exact boundary problem: determine which final-emission overlaps are permanent legality/packaging orchestration, which are defensive exceptions, and which semantic repair residues remain transitional.

Why distinct: BE-PP1 and BE-PP6 are the highest-pressure overlap cluster and already have rich tests/contracts.

Primary evidence: `AR-BB...`, `game/final_emission_boundary_contract.py`, `game/final_emission_gate.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, `game/realization_provenance.py`, `game/final_emission_replay_projection.py`, final-emission tests.

Expected artifact: symbol-level overlap classification and retirement/validation register.

Dependencies: AR-BE.

Mandatory.

### AR-BG Ruleset, Backend, and Version-Provenance Boundary Inventory

Exact boundary problem: inventory the local seams needed before alternate rulesets or additional AI backends: ruleset identity/version, backend adapter, fake backend, and provenance/version bundle.

Why distinct: ruleset and backend seams both affect provenance/replay/capability identity and were already grouped as final-vision prerequisites.

Primary evidence: `AR-AG...`, `AR-AH...`, `AR-AI...`, `game/combat.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/model_routing.py`, `game/gm.py`, `tests/test_model_routing_*`, provenance/replay fields.

Expected artifact: minimal boundary decision record for ruleset/backend/version identity, not implementation.

Dependencies: AR-BE; can follow AR-BF or run after if no final-emission evidence is needed.

Mandatory if alternate rulesets/backends remain planned; otherwise conditional but recommended.

### AR-BH Public UI, Tooling, and Adapter Facade Boundary Discovery

Exact boundary problem: determine the smallest public command/query/event and adapter boundary needed before external tooling, hosted UI, or plugin-like integrations.

Why distinct: current UI is local and mode-guarded, while external tooling/plugin scope depends on product decisions and could overfit if mixed with runtime/final-emission work.

Primary evidence: `game/api.py`, `game/ui_mode_policy.py`, `game/state_channels.py`, `game/api_ui_mode.py`, `static/app.js`, `game/importers/pf_json_importer.py`, `tests/test_ui_mode_backend_integration.py`, `tests/test_frontend_ui_mode_hardening_objective15.py`, `tests/test_compat_import_governance.py`.

Expected artifact: facade/adapters inventory and decision points for local-only vs public/hosted integrations.

Dependencies: AR-BE; AR-BG if backend/ruleset capabilities are in scope.

Conditional.

### AR-BI Evidence Canonicality and Governance Surface Compression

Exact boundary problem: classify high-use audits/artifacts/reports as authoritative, generated evidence, advisory, historical, or obsolete to prevent future campaigns from re-reading excessive evidence.

Why distinct: this is a governance/evidence hygiene cycle, not a runtime boundary cycle.

Primary evidence: `docs/architecture_ownership_ledger.md`, `docs/testing/replay_governance_authority.md`, `artifacts/`, `audits/`, `tools/*_report.py`, prior AR closeouts.

Expected artifact: minimal evidence-source registry for future campaign prompts.

Dependencies: AR-BE; useful after AR-BF if final-emission reports dominate.

Conditional.

Total focused campaign size including AR-BE: 3 mandatory/likely cycles (`AR-BE`, `AR-BF`, `AR-BG`) plus 1-2 conditional cycles (`AR-BH`, `AR-BI`).

## 10. Files to Provide for External Review

### Required

- `AR-BE_boundary_reconciliation_discovery_and_evidence_inventory.md`
- `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
- `AR-BB_defensive_runtime_boundary_reconciliation.md`
- `docs/architecture_ownership_ledger.md`
- `docs/state_authority_model.md`
- `game/final_emission_boundary_contract.py`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/output_sanitizer.py`
- `game/upstream_response_repairs.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`
- `tests/test_final_emission_boundary_contract.py`
- `tests/test_replay_boundary_governance.py`

### Conditional

- `AR-AG_final_vision_compatibility_discovery.md`
- `AR-AH_final_vision_compatibility_assessment.md`
- `AR-AI_final_vision_compatibility_closeout.md`
- `game/api.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/prompt_context.py`
- `game/model_routing.py`
- `game/gm.py`
- `game/world.py`
- `game/world_progression.py`
- `game/noncombat_resolution.py`
- `game/social.py`
- `game/combat.py`
- `game/ui_mode_policy.py`
- `game/state_channels.py`
- `game/importers/pf_json_importer.py`
- `game/content_lint.py`
- `tests/test_state_authority.py`
- `tests/test_ctir_turn_packet_boundary.py`
- `tests/test_ui_mode_backend_integration.py`
- `tests/test_compat_import_governance.py`

### Not Needed Unless Requested

- Full `artifacts/` and `audits/` trees.
- Generated JSON reports not directly cited by the next cycle.
- Large golden replay corpora and replay refresh outputs.
- Full `tests/` directory.
- Static UI files beyond `static/app.js` unless AR-BH is selected.
- All scene/content JSON files unless a content-boundary ambiguity is selected.
