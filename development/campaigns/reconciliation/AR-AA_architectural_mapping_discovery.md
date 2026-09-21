# AR-AA Architectural Mapping Discovery

Date: 2026-07-01  
Scope: discovery-only architectural mapping for Campaign 1 / first Architecture Reconciliation cycle  
Mode: read-only inspection of implementation, tests, and docs; no runtime fixes attempted

## 1. Executive Summary

The current architecture is not obviously "broken"; it is heavily governed and evidence-rich. The major shape that emerged is a runtime pipeline where `game.api` orchestrates authoritative state mutation, CTIR construction, GPT narration/retry/fallback handling, final emission, persistence, log emission, and debug trace capture. Around that pipeline, several ownership ledgers and test-side projection surfaces define where authority should live.

The strongest architectural centers are:

- `game.api` as runtime turn orchestration and API/emission tail owner.
- `game.storage` plus `game.state_authority` as persistence/state-domain surfaces.
- `game.ctir` / `game.ctir_runtime` as the canonical resolved-turn meaning object and lifecycle seam.
- `game.prompt_context` and `game.narration_plan_bundle` as prompt packaging / plan-consumption layers, not semantic owners when CTIR exists.
- `game.final_emission_gate`, `game.final_emission_runtime`, `game.final_emission_finalize`, `game.final_emission_meta`, and related modules as final player-facing emission surfaces.
- `game.realization_authority` / `game.realization_provenance` as fallback/realization authority vocabulary and stamping.
- `tests.helpers.golden_replay_projection` / `docs/testing/protected_replay_manifest.md` as protected replay acceptance authority, intentionally split from runtime lineage projection in `game.final_emission_replay_projection`.

The main tension is not absent ownership. It is that ownership is explicit but broad: final emission, fallback provenance, replay projection, source/fallback vocabulary, and evidence artifacts still cross many files. The best first AR-AA focus is an **Authority/Ownership Ledger plus Runtime Flow Map**, with replay/evidence boundaries called out as a secondary map.

## 2. Major Subsystems

### API / Runtime Turn Orchestration

Purpose:

- Accept UI/API requests, route fresh campaign start/chat/action flows, orchestrate authoritative engine mutation, GPT narration, retries/fallbacks, final emission, persistence, trace/log emission, and response payload construction.

Key files / functions:

- `game/api.py`
  - `start_campaign`
  - `chat` / `api_chat`
  - `action` / `api_action`
  - `_run_resolved_turn_pipeline`
  - `_build_gpt_narration_from_authoritative_state`
  - `_complete_opening_turn_persistence_like_chat`
  - `_finalize_player_facing_for_turn`
  - `_apply_authoritative_resolution_state_mutation`
  - `_apply_post_gm_updates`
  - `_build_opening_scene_resolution`
  - `_opening_scene_normalized_action_and_resolution`

Inputs:

- HTTP payloads (`ChatRequest`, `ActionRequest`, `/api/start_campaign`)
- Runtime state loaded from `game.storage`
- Engine/domain resolution output
- GPT/model output from `game.gm.call_gpt`
- Retry/fallback validators and response-policy contracts

Outputs:

- Response payload with `gm_output`, optional `resolution`, public/private UI projection
- Mutated `session`, `world`, `combat`, scene runtime
- Session log entries
- Debug traces, latency breakdowns, final emission metadata

State:

- **Stable but high-pressure.** It is the actual runtime spine and is richly tested, but it is also a concentration point for many concerns: CTIR timing, response contracts, fallback selection, final emission, provenance, persistence, and logging.

### Storage / Runtime Persistence

Purpose:

- Own JSON file load/save, runtime document envelope handling, scene activation/effective-scene overlays, session runtime helpers, logs, snapshots, and persistence coherency.

Key files / functions:

- `game/storage.py`
  - `load_session`, `save_session`, `load_world`, `save_world`, `load_combat`, `save_combat`
  - `load_active_scene`, `activate_scene`, `get_effective_scene`
  - `get_scene_runtime`, `get_runtime_scene_overlay`, `build_effective_scene`
  - `append_log`, `load_log`, `clear_log`
  - `create_snapshot`, `load_snapshot`, snapshot restore helpers
- `docs/runtime_persistence_envelope.md`

Inputs:

- `data/*.json`, `data/scenes/*.json`, runtime envelopes, snapshot bundles
- Mutated payload dicts from runtime/domain modules

Outputs:

- Unwrapped runtime payload dicts for game logic
- Versioned runtime envelopes on disk for session/combat
- Atomic writes, append-only log entries, snapshots

State:

- **Stable.** Runtime persistence envelope docs clearly distinguish mutable runtime docs from authored/bootstrap content. Some lazy session-root materialization is explicitly deferred/accepted in `state_authority` docs.

### State Authority / Domain Ownership Registry

Purpose:

- Declare non-overlapping state domains and guard which modules can mutate which domains. It is explicitly governance/helper code, not a persistence engine.

Key files / functions:

- `game/state_authority.py`
  - `StateDomainSpec`
  - `CrossDomainWriteSpec`
  - `get_state_domain_spec`
  - `assert_owner_can_mutate_domain`
  - `assert_cross_domain_write_allowed`
  - `build_state_mutation_trace`
- `docs/architecture_ownership_ledger.md`
- `docs/state_authority_model.md` (referenced by ledger)
- `tests/test_state_authority.py`

Inputs:

- Domain IDs (`world_state`, `scene_state`, `interaction_state`, `player_visible_state`, `hidden_state`)
- Owner module names
- Cross-domain operation names

Outputs:

- Guard pass/fail
- Mutation trace dicts for debug/evidence

State:

- **Stable, declarative.** It is not wired everywhere as a hard guard, but its intended scope is explicit: registry and guard helpers, not semantic persistence.

### Campaign State / Session Bootstrap

Purpose:

- Create fresh campaign/session/combat state and reset session shape.

Key files / functions:

- `game/campaign_state.py`
  - `create_fresh_session_document`
  - `create_fresh_campaign_state`
  - `create_fresh_combat_state`
- `game/session.py`
  - `reset_session_state`
- `game/campaign_reset.py`
- `tests/test_campaign_state_factory.py`
- `tests/test_campaign_reset.py`
- `tests/test_new_campaign_silent_reset_nc2.py`
- `tests/test_start_campaign_api.py`

Inputs:

- Defaults and existing runtime docs

Outputs:

- Fresh session/campaign/combat documents
- Reset state for `/api/new_campaign` and campaign start flows

State:

- **Stable.** The start/reset boundaries are tested and appear separate from opening narration generation.

### Engine Resolution / Domain Simulation

Purpose:

- Resolve player actions into authoritative game outcomes before narration.

Key files / functions:

- `game/api.py`
  - `_resolve_engine_noncombat_seam`
  - `_apply_authoritative_resolution_state_mutation`
- `game/noncombat_resolution.py`
- `game/exploration.py`
- `game/social.py`
- `game/combat.py`
- `game/world_progression.py`
- `game/interaction_context.py`
- `game/scene_actions.py`
- `game/skill_checks.py`

Inputs:

- Normalized actions, current scene/session/world/combat, route choice, social target resolution

Outputs:

- Authoritative `resolution` dict
- Mutated scene/session/combat/world state
- Clue updates, world tick events, interaction context changes

State:

- **Transitional but governed.** Non-combat now has a contract-first flow documented in `docs/ctir_prompt_adapter_architecture.md`, but some legacy resolution mirrors are intentionally retained for compatibility.

### CTIR / Resolved-Turn Meaning

Purpose:

- Create a bounded, deterministic, JSON-safe resolved-turn meaning object for one narration attempt, attached to the session and reused through retries.

Key files / functions:

- `game/ctir.py`
  - `build_ctir`
  - normalization helpers for intent/resolution/state mutations/interaction/world/provenance/debug
- `game/ctir_runtime.py`
  - `detach_ctir`
  - `ensure_ctir_for_turn`
  - `narration_ctir_turn_stamp`
  - `build_runtime_ctir_for_narration`
- `docs/ctir_prompt_adapter_architecture.md`
- `tests/test_ctir_runtime_lifecycle.py`
- `tests/test_ctir_retry_stability.py`
- `tests/test_ctir_turn_packet_boundary.py`
- `tests/test_ctir_pipeline_integration.py`
- `tests/test_prompt_context_ctir_consumption.py`

Inputs:

- Post-mutation `resolution`
- Session/world/combat slices
- Normalized action
- Turn id, scene id, player input

Outputs:

- Session-attached `_runtime_canonical_ctir_v1`
- Retry-stable CTIR stamp
- Bounded CTIR sections for prompt adapter

State:

- **Stable and well-documented.** The lifecycle is explicit: detach stale CTIR at resolved-turn entry, mutate authoritative state, apply pre-prompt hygiene, then build/attach CTIR once for the stamp.

### Prompt Context / Narration Plan Bundle

Purpose:

- Build the public prompt payload for GPT from approved artifacts, CTIR, narrative plan bundle, visibility contracts, response policy, and compact context windows.

Key files / functions:

- `game/prompt_context.py`
- `game/narration_plan_bundle.py`
- `game/narrative_planning.py`
- `game/narrative_plan_upstream.py`
- `game/response_policy_contracts.py`
- `docs/ctir_prompt_adapter_architecture.md`
- `docs/narrative_integrity_architecture.md`

Inputs:

- Session-attached CTIR
- Narrative plan bundle
- Scene/world/session/public visibility slices
- Response policy / response type contracts

Outputs:

- GPT messages / prompt JSON
- Prompt-side contracts and visibility payloads

State:

- **Stable with compatibility residue.** Docs are clear that `prompt_context` packages and adapts; it must not re-decide CTIR-backed turn meaning. Compatibility fallbacks exist when CTIR is absent.

### GPT / Model Routing / Upstream Response Handling

Purpose:

- Call GPT with route metadata, parse/guard outputs, classify upstream API failures, and preserve model route metadata.

Key files / functions:

- `game/gm.py`
  - `build_messages`
  - `call_gpt`
  - `guard_gm_output`
  - upstream error classification helpers
- `game/model_routing.py`
- `game/model_routing_runtime.py` (if present in tests/docs; runtime file is `game/model_routing.py`)
- `game/api_upstream_preflight.py`
- `game/upstream_dependent_run_gate.py`
- `game/upstream_dependent_run_gate_presentation.py`
- `docs/model_routing_architecture.md`
- `tests/test_model_routing_runtime.py`
- `tests/test_api_upstream_preflight.py`
- `tests/test_upstream_dependent_run_bhc2.py`

Inputs:

- Prompt messages
- Route context (`purpose`, retry attempt, strict-social flag, response policy)
- Upstream API responses/errors

Outputs:

- Guarded GM dict
- Model route metadata
- Upstream API error metadata

State:

- **Stable but entangled with API fallback handling.** GPT call/guarding belongs mainly to `game.gm`, while `game.api` owns retry-loop orchestration and upstream fast-fallback selection.

### Fallback Handling / Retry System

Purpose:

- Detect bad/empty/thin GPT output, retry where allowed, select deterministic terminal fallback when necessary, stamp provenance, and preserve route/owner metadata.

Key files / functions:

- `game/api.py`
  - `_fast_fallback_for_upstream_error`
  - `_repair_terminal_player_facing_if_needed`
  - retry loop inside `_build_gpt_narration_from_authoritative_state`
- `game/gm_retry.py`
- `game/fallback_behavior.py`
- `game/diegetic_fallback_narration.py`
- `game/fallback_provenance_debug.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/upstream_response_repairs.py`
- `game/opening_deterministic_fallback.py`
- `game/social_exchange_emission.py`

Inputs:

- GPT output, retry failure classifications, upstream API error metadata
- Resolution/session/scene/world context
- Registered fallback families and response contracts

Outputs:

- Fallback GM output
- `realization_fallback_family`
- fallback provenance fingerprints/traces
- final emission metadata fields and runtime lineage projections

State:

- **Transitional / high-pressure.** The authority vocabulary is explicit, but fallback selection, content authorship, provenance packaging, and replay projection are distributed. Docs characterize this as an architecture reconciliation target rather than a hidden bug.

### Opening Scene Realization

Purpose:

- Build opening-scene contract/basis payloads from curated player-visible scene facts and visibility contracts. It is a renderer/helper layer, not the canonical structural opening authority.

Key files / functions:

- `game/api.py`
  - `_build_opening_scene_resolution`
  - `_opening_scene_normalized_action_and_resolution`
  - start-campaign/chat opening paths
- `game/opening_scene_realization.py`
  - `build_opening_scene_realization`
  - `validate_opening_scene_contract`
  - `build_opening_narration_obligations_payload`
  - `patch_opening_export_with_plan_scene_opening`
- `game/opening_visible_fact_selection.py`
- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `tests/test_opening_scene_realization.py`
- `tests/test_opening_visible_fact_selection.py`
- `tests/test_start_campaign_api.py`
- `tests/test_final_emission_opening_fallback.py`

Inputs:

- Public scene slice
- Curated visible fact strings
- Visibility contract
- Opening scene resolution

Outputs:

- Opening realization contract
- Narration basis visible facts
- Opening fallback/prepared emission metadata where applicable

State:

- **Stable but boundary-sensitive.** The module docstring explicitly says structural opening obligations are owned by `game.narrative_planning.build_narrative_plan`; this module curates diegetic basis lines and prompt instructions.

### Final Emission / Player-Facing Text Boundary

Purpose:

- Apply final legality/repair/orchestration layers, sanitize/package final text, stamp `_final_emission_meta`, and expose a production-facing delegate for API/runtime use.

Key files / functions:

- `game/final_emission_runtime.py`
  - `finalize_player_facing_emission`
- `game/final_emission_gate.py`
  - `apply_final_emission_gate`
- `game/final_emission_finalize.py`
  - `finalize_emission_output`
  - `final_emission_fast_path_eligible`
- `game/final_emission_meta.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/output_sanitizer.py`
- `game/final_emission_replay_projection.py`
- `docs/final_emission_ownership_convergence.md`
- `docs/final_emission_boundary_audit.md`
- `tests/test_final_emission_gate*.py`
- `tests/test_final_emission_meta.py`
- `tests/test_final_emission_boundary*.py`
- `tests/ownership_guard_bn_gate_context.py`

Inputs:

- GM output
- Resolution/session/scene/world
- Sanitizer trace
- Turn packet/stage telemetry
- Upstream prepared emission fields

Outputs:

- Final `player_facing_text`
- `_final_emission_meta`
- `final_emitted_source`, `final_route`, mutation lineage, fallback fields
- Runtime lineage events for read-side projection

State:

- **Governed but transitional.** Docs state the convergence target: final emission should enforce legality and packaging, while semantic content should move upstream. Current implementation still has semantic repair/fallback pressure, though much of it is documented and tested.

### Social / Strict-Social Emission

Purpose:

- Own strict-social exchange emission, deterministic social fallback shaping, speaker/ownership filtering, and terminal dialogue fallback behavior.

Key files / functions:

- `game/social_exchange_emission.py`
- `game/social_exchange_policy.py`
- `game/social_exchange_projection.py`
- `game/social_exchange_validation.py`
- `game/dialogue_social_plan.py`
- `game/speaker_contract_enforcement.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_social_emission_quality.py`
- `tests/test_dialogue_plan_final_emission_gate.py`

Inputs:

- Resolution social contract
- Session/world/scene context
- Candidate model output

Outputs:

- Strict-social candidate/fallback text
- Speaker/ownership filters and metadata
- Final emission inputs

State:

- **Stable but interconnected.** Ownership is declared in the architecture ledger, but gate/sanitizer/API are downstream selectors/consumers, creating coordination pressure.

### Replay / Projection / Evidence

Purpose:

- Run golden/protected replay scenarios, project runtime payloads into stable observation rows, detect drift, produce recurrence/evidence artifacts, and govern replay acceptance.

Key files / functions:

- `tests/helpers/golden_replay.py`
  - `run_golden_replay`
- `tests/helpers/golden_replay_projection.py`
  - `project_turn_observation`
- `tests/helpers/golden_replay_projection_fields.py`
  - `PROTECTED_OBSERVATION_FIELDS`
- `tests/helpers/protected_replay_registry.py`
  - `protected_replay_registry`
  - `protected_replay_corpus`
- `tests/helpers/golden_replay_trend.py`
  - `execute_protected_replay_corpus`
  - `run_protected_replay_trend_window`
- `game/final_emission_replay_projection.py`
  - runtime diagnostic/read-side FEM lineage projection
- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- `tests/replay_governance_*.py`

Inputs:

- Replay scenario registry
- Chat payloads and snapshots
- Final emission metadata / FEM
- Trace/debug fields

Outputs:

- Protected observation rows
- Drift buckets
- Replay reports/artifacts
- Governance decision records

State:

- **Stable but high fanout.** Runtime lineage projection and protected replay acceptance are intentionally split; this is documented and tested. The tension is vocabulary and evidence fanout, not absence of governance.

### Test / Governance / Audit Tooling

Purpose:

- Maintain ownership ledgers, static governance guards, architecture audits, replay evidence reports, fallback incidence reports, semantic mutation attribution, and corrective locality metrics.

Key files / functions:

- `docs/architecture_ownership_ledger.md`
- `tests/TEST_AUDIT.md`
- `tests/ownership_*`
- `tests/replay_governance_*`
- `tools/architecture_audit.py`
- `tools/final_emission_ownership_audit.py`
- `tools/realization_provenance_audit.py`
- `tools/run_protected_replay_trend.py`
- `tools/fallback_incidence_report.py`
- `tools/regenerate_bug_recurrence_history.py`

Inputs:

- Source tree, tests, docs, replay artifacts

Outputs:

- Governance pass/fail tests
- Advisory reports and generated artifacts

State:

- **Stable but artifact-heavy.** Foundation Stabilization produced strong evidence surfaces; Architecture Reconciliation should reduce coordination cost without discarding them.

## 3. Ownership Surfaces

### State Authority

Canonical surface:

- `game/state_authority.py`

Declared owners:

- `world_state`: `game.world`, `game.storage`
- `scene_state`: `game.storage`, `game.api`
- `interaction_state`: `game.interaction_context`, `game.api`
- `player_visible_state`: `game.narration_visibility`, `game.scene_state_anchoring`, `game.prompt_context`, `game.journal`
- `hidden_state`: `game.storage`, `game.world`, `game.api`

Enforcement / evidence:

- `assert_owner_can_mutate_domain`
- `assert_cross_domain_write_allowed`
- `build_state_mutation_trace`
- `tests/test_state_authority.py`
- Architecture ledger section "Unified State Authority Model"

Assessment:

- Authority is explicit and governance-oriented. `game.api` remains a legitimate owner for several domains because it orchestrates transitions and authoritative resolution mutation.

### Runtime Authority

Canonical surface:

- `game/api.py`

Specific authority:

- Turn orchestration for `/api/action`, `/api/chat`, `/api/start_campaign`
- Start-campaign gating against upstream preflight
- CTIR lifecycle timing
- GPT/retry/fallback loop orchestration
- Persistence/log response tail

Supporting owners:

- `game.storage` for persistence mechanics
- `game.ctir_runtime` for CTIR attach/stamp helpers
- Domain modules for actual domain-specific resolution

Assessment:

- Runtime authority is centralized in `game.api`; this is stable but creates broad change locality.

### Realization Authority

Canonical surfaces:

- `game/realization_authority.py`
- `game/realization_provenance.py`
- `docs/realization_provenance_audit.md`

Declared authority:

- GPT may phrase/style supplied constraints but may not own truth, consequences, legality, state mutation, or fallback authorship.
- `prompt_context` packages approved artifacts; it must not infer missing meaning or decide narrative obligations.
- `final_emission_gate` validates/selects already-authorized text and may apply registered sealed deterministic terminal fallback only.
- Fallback families are governed through `realization_fallback_family`.

Enforcement / evidence:

- `attach_realization_fallback_family`
- `tests/test_realization_authority.py`
- `tests/test_realization_provenance.py`
- `tools/realization_provenance_audit.py`

Assessment:

- Declarative authority is stable. Runtime attachment sites are distributed and are part of the reconciliation surface.

### Replay Authority

Canonical acceptance surface:

- `docs/testing/protected_replay_manifest.md`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/protected_replay_registry.py`

Canonical runtime diagnostic surface:

- `game/final_emission_replay_projection.py`

Governance surface:

- `docs/testing/replay_governance_authority.md`
- `tests/replay_governance_contract.py`
- `tests/replay_governance_registry.py`
- `tests/replay_governance_approval_contract.py`
- `tests/replay_governance_traceability_contract.py`

Assessment:

- Replay authority is intentionally split:
  - protected replay acceptance is test-only;
  - runtime lineage projection is diagnostic/read-side.
- This split is stable but needs clear mapping in AR-AA so future work does not merge them accidentally.

### API / Emission Authority

Canonical surfaces:

- `game/api.py` for endpoint/runtime response assembly.
- `game/final_emission_runtime.py` as production-facing final emission delegate.
- `game/final_emission_gate.py` as canonical gate orchestration owner.
- `game/final_emission_finalize.py` as final packaging/finalization owner.

Enforcement / evidence:

- `tests/ownership_guard_bn_gate_context.py` prevents runtime/API modules from importing the gate owner directly; production code should use `game.final_emission_runtime.finalize_player_facing_emission`.
- `tests/test_start_campaign_api.py` checks start-campaign opening emission/log/payload invariants.

Assessment:

- API owns response payload and persistence emission; final emission gate owns text/legal boundary. There is a clear delegate seam, but historical tests and helpers still reference lower-level surfaces.

### Fallback Authority

Canonical surfaces:

- `game/realization_authority.py`: declarative family/profile authority.
- `game/realization_provenance.py`: normalized family stamp.
- `game/api.py`: upstream API fast-fallback selection/application.
- `game/gm_retry.py`: retry terminal fallback selection.
- `game/fallback_provenance_debug.py`: upstream fast-fallback provenance packaging, not selection.
- `game/social_exchange_emission.py`: strict-social deterministic fallback content.
- `game/opening_deterministic_fallback.py` and `game/upstream_response_repairs.py`: opening/prepared fallback payload content and packaging.
- `game/final_emission_gate.py`: gate selection/application for certain prepared/sealed paths.

Assessment:

- This is the highest-pressure ownership surface. The architecture distinguishes content owner, selection owner, provenance packager, and replay projection owner, but several files participate in every final observed fallback field.

### Test / Provenance / Evidence Authority

Canonical surfaces:

- `docs/architecture_ownership_ledger.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/TEST_AUDIT.md`
- `tests/ownership_*`
- `tests/replay_governance_*`
- `tests/helpers/golden_replay_projection.py`
- `tools/realization_provenance_audit.py`
- `tools/fallback_incidence_report.py`
- `tools/run_protected_replay_trend.py`

Assessment:

- Evidence authority is strong, but evidence-bearing changes are diffuse. Foundation closeout specifically identifies this as the reason to enter Architecture Reconciliation.

## 4. Runtime Flows

### Campaign / Session Start

Files involved:

- `game/api.py`
- `game/campaign_state.py`
- `game/campaign_reset.py`
- `game/session.py`
- `game/storage.py`
- `game/upstream_dependent_run_gate.py`
- `tests/test_start_campaign_api.py`

Sequence:

1. `/api/new_campaign` resets runtime/session/log state using campaign/session factory/reset paths.
2. `/api/start_campaign` resolves UI mode and checks `compute_upstream_dependent_run_gate`.
3. `start_campaign` loads campaign, character, session, log, world, combat, conditions, and active scene.
4. `_session_allows_structured_start_campaign` blocks if campaign already started or transcript is not empty.
5. Session turn counter increments; world tick and time-pressure clock advance.
6. Start flow builds an internal `scene_opening` normalized action/resolution via `_opening_scene_normalized_action_and_resolution(... internal_bootstrap=True)`.
7. The flow rejoins `_run_resolved_turn_pipeline`.
8. `_complete_opening_turn_persistence_like_chat` performs final emission, post-GM updates, persistence, log append, and marks `campaign_started=True`.

Assessment:

- Stable. Start campaign is a bootstrap into the normal resolved-turn narration path, not a separate story-generation architecture.

### Opening Scene Generation / Realization

Files involved:

- `game/api.py`
- `game/opening_scene_realization.py`
- `game/opening_visible_fact_selection.py`
- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/narrative_planning.py`
- `game/prompt_context.py`
- `game/final_emission_gate.py`
- `tests/test_opening_scene_realization.py`
- `tests/test_opening_visible_fact_selection.py`
- `tests/test_start_campaign_api.py`
- `tests/test_final_emission_opening_fallback.py`

Sequence:

1. Runtime creates a `resolution.kind == "scene_opening"` with `action_id == "campaign_start_opening_scene"`.
2. Prompt construction uses public scene/visibility/curated facts.
3. `opening_scene_realization.build_opening_scene_realization` assembles an opening contract and narration basis from curated visible fact strings only.
4. `game.narrative_planning` owns structural opening obligations; `opening_scene_realization` is renderer/helper for diegetic basis and prompt instruction expansion.
5. GPT produces opening narration.
6. Upstream prepared opening fallback may be packaged before final emission.
7. Final emission gate consumes/selects accepted candidate or prepared/fallback opening text but should not author missing opening semantics.
8. `_complete_opening_turn_persistence_like_chat` copies opening debug fields into final emission metadata where needed and preserves response/log/payload final-text invariant.

Assessment:

- Stable but sensitive. The ownership distinction between planning, realization helper, upstream prepared fallback, and gate selection must remain explicit.

### Fallback Handling

Files involved:

- `game/api.py`
- `game/gm_retry.py`
- `game/fallback_behavior.py`
- `game/fallback_provenance_debug.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/final_emission_gate.py`
- `game/final_emission_finalize.py`
- `game/social_exchange_emission.py`
- `game/upstream_response_repairs.py`
- `game/diegetic_fallback_narration.py`
- `tests/test_upstream_fast_fallback_block_l.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_behavior_*.py`
- `tests/test_opening_fallback_owner_bucket.py`

Sequence:

1. `game.gm.call_gpt` may return normal GM output or guarded upstream error metadata.
2. API retry loop detects upstream API error, retryable/nonretryable status, social retry suppression, or validation failures.
3. `_fast_fallback_for_upstream_error` uses `force_terminal_retry_fallback`, terminal repair if empty, stamps tags/metadata, attaches `realization_fallback_family=gpt_budget_or_provider_failure`, and calls `attach_upstream_fast_fallback_provenance`.
4. Non-upstream validation failures can trigger targeted retry, deterministic retry fallback, or forced terminal fallback.
5. Final emission gate/finalize records gate entry/exit provenance and may restore selector text on overwrite containment.
6. Replay projection later reads FEM/provenance fields into runtime lineage or protected observations.

Assessment:

- Transitional. The flow is deliberately instrumented, but content author, selector, packager, and replay observer are separate and easy to blur.

### Upstream Response Handling

Files involved:

- `game/gm.py`
- `game/model_routing.py`
- `game/api.py`
- `game/api_upstream_preflight.py`
- `game/upstream_dependent_run_gate.py`
- `game/upstream_response_repairs.py`
- `tests/test_api_upstream_preflight.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_upstream_response_repairs.py`

Sequence:

1. API builds messages with route context.
2. `call_gpt` handles model call and attaches route/error metadata.
3. `guard_gm_output` normalizes/guards returned GM dict.
4. API extracts `metadata.upstream_api_error`.
5. Retryable errors may receive one direct retry unless social-dialogue retry is suppressed.
6. Remaining upstream errors become fast fallback via API-owned selection.
7. Upstream response repairs may package prepared emission/fallback text before final emission.

Assessment:

- Stable but broad. `game.gm` owns call/guard mechanics; `game.api` owns runtime retry/fallback orchestration.

### Final Emission

Files involved:

- `game/api.py`
- `game/final_emission_runtime.py`
- `game/final_emission_gate.py`
- `game/final_emission_finalize.py`
- `game/final_emission_meta.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/output_sanitizer.py`
- `game/stage_diff_telemetry.py`
- `game/turn_packet.py`
- `tests/test_final_emission_gate*.py`
- `tests/test_final_emission_meta.py`
- `tests/ownership_guard_bn_gate_context.py`

Sequence:

1. API calls `_finalize_player_facing_for_turn`.
2. Production-facing delegate should be `final_emission_runtime.finalize_player_facing_emission`.
3. Delegate calls `final_emission_gate.apply_final_emission_gate`.
4. Gate initializes execution context and preflight state, runs strict-social/non-strict/generic layer stacks, consumes upstream prepared emissions/fallbacks, and calls finalize.
5. `final_emission_finalize.finalize_emission_output` performs packaging-only normalization, metadata merge, provenance containment, final mutation lineage refresh, and opening-candidate reseal where applicable.
6. API persists/logs the canonical GM object and response payload.

Assessment:

- Governed but transitional. The target is legality + packaging only at final emission, but current code still has semantic mutation/fallback pressure.

### Replay / Projection

Files involved:

- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/protected_replay_registry.py`
- `tests/helpers/golden_replay_trend.py`
- `game/final_emission_replay_projection.py`
- `docs/testing/protected_replay_manifest.md`
- `tests/test_golden_replay_structural_invariants.py`
- `tests/test_protected_replay_registry.py`
- `tests/test_replay_boundary_governance.py`

Sequence:

1. `run_golden_replay` patches transcript storage, seeds bootstrap scenes, starts a clean campaign, runs chat turns, snapshots payloads.
2. Each turn payload is passed to `project_turn_observation`.
3. `project_turn_observation` reads payload, snapshot, resolution, FEM, runtime lineage events, sanitizer trace/debug, social trace, and speaker observations.
4. Protected fields come from `PROTECTED_OBSERVATION_FIELDS`.
5. Protected replay corpus is exactly the six short structural scenarios in `protected_replay_corpus`.
6. Trend tooling executes the protected corpus and compares normalized route/speaker/source/owner/mutation/final-text dimensions.

Assessment:

- Stable. Acceptance projection is test-only and intentionally separate from runtime diagnostic lineage.

### Provenance / Evidence Capture

Files involved:

- `game/fallback_provenance_debug.py`
- `game/realization_provenance.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/stage_diff_telemetry.py`
- `game/runtime_lineage_telemetry.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_dashboard_*`
- `tools/realization_provenance_audit.py`
- `tools/fallback_incidence_report.py`
- `tools/run_protected_replay_trend.py`

Sequence:

1. Runtime stamps provenance on fallback/realization metadata at selection/packaging sites.
2. Final emission records gate entry/exit snapshots and mismatch/containment metadata.
3. FEM stores final route/source/mutation/fallback/provenance fields.
4. Runtime read-side projection can build `fem_runtime_lineage_events`.
5. Golden replay acceptance projection reads payload/snap/FEM into protected observation fields.
6. Tools aggregate incidence, drift, recurrence, and provenance audit artifacts.

Assessment:

- Stable but evidence-heavy. Evidence capture is rich enough to support reconciliation, but it contributes to corrective locality fanout.

## 5. Replay and Evidence Surfaces

### Determinism

Files / tests / docs:

- `docs/testing/protected_replay_manifest.md`
- `tests/test_runtime_drift_seed_audit.py`
- `tests/helpers/protected_replay_registry.py`
- `tests/helpers/golden_replay_trend.py`
- `tests/test_golden_replay_structural_invariants.py`
- `tests/test_bz_protected_replay_trend_window_2.py`
- `tools/run_protected_replay_trend.py`

Evidence:

- Protected corpus registry has stable ordering and exactly six compact protected scenarios.
- Drift trend tooling compares normalized fields across reruns.
- Seed audit protects replay-sensitive paths from unstable seed material.

### Replay Boundaries

Files / tests / docs:

- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- `tests/test_replay_boundary_governance.py`
- `tests/ownership_guard_bi8_golden_replay_boundary.py`
- `tests/helpers/golden_replay_projection.py`
- `game/final_emission_replay_projection.py`

Evidence:

- AO5 boundary explicitly says runtime lineage projection and acceptance projection must not be merged.
- Governance docs separate replay execution, classification, and governance decisions.

### Final Emission Projection

Files / tests / docs:

- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/test_golden_replay_projection*.py`
- `docs/testing/protected_replay_manifest.md`
- `docs/audits/CF_replay_projection_responsibility_discovery.md`
- `docs/audits/CF1_projection_precedence_matrix.md`

Evidence:

- Runtime lineage events are diagnostic/read-side.
- Protected observation fields are acceptance authority.
- Dual fallback family projection is read-side compatibility only.

### Provenance

Files / tests / docs:

- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_meta.py`
- `docs/realization_provenance_audit.md`
- `tools/realization_provenance_audit.py`
- `tests/test_realization_authority.py`
- `tests/test_realization_provenance.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_attribution_contract.py`

Evidence:

- Fallback/realization family vocabulary is declarative.
- Upstream fast-fallback provenance packager fingerprints selector text and records gate entry/exit mismatch.
- Provenance audit is advisory, not CI-failing.

### Evidence Capture

Files / tests / docs:

- `docs/audits/foundation_stabilization_closeout_discovery.md`
- `CT_runtime_fallback_incidence_baseline_discovery.md`
- `CT_projection_fidelity_audit.md`
- `CV_corrective_locality_confirmation_discovery.md`
- `docs/audits/CU_semantic_mutation_write_site_attribution_discovery.md`
- `artifacts/golden_replay/*`
- `tools/fallback_incidence_report.py`
- `tools/regenerate_bug_recurrence_history.py`
- `tools/run_protected_replay_trend.py`

Evidence:

- Foundation closeout documents replay recurrence separation, fallback incidence baseline, semantic mutation write-site attribution, corrective locality, and architecture reconciliation readiness.

### Runtime-vs-Replay Separation

Files / tests / docs:

- `docs/testing/protected_replay_manifest.md`
- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_replay_boundary_governance.py`
- `tests/test_golden_replay_projection_governance.py`
- `tests/test_golden_replay_projection_metadata.py`

Evidence:

- Runtime lineage projection does not define protected fields or acceptance locks.
- Protected replay acceptance lives in test helpers and manifest.

## 6. Architectural Tensions

### 1. `game.api` Is a Runtime Spine and a Coordination Hotspot

Evidence:

- `game.api` owns start campaign, action/chat flow, authoritative mutation, CTIR timing, prompt/GPT/retry, fast fallback, final emission handoff, persistence, log append, and trace construction.

Tension:

- This is operationally coherent but makes changes diffuse. Architecture Reconciliation should distinguish runtime-locality from evidence-locality and avoid pretending all broad changes are runtime complexity.

### 2. Final Emission Has Clear Doctrine but Still Carries Semantic Repair Pressure

Evidence:

- `docs/final_emission_ownership_convergence.md` says final emission should converge to legality + packaging.
- `game/final_emission_gate.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py`, and `game/social_exchange_emission.py` still contain or invoke semantic repair/fallback behavior.

Tension:

- The current code is not undocumented chaos; it is a transitional boundary with explicit target state. AR-AA should map current vs target authority.

### 3. Fallback Ownership Has Multiple Valid Axes

Evidence:

- API may select fast fallback.
- `gm_retry` may select retry terminal fallback.
- `fallback_provenance_debug` packages provenance only.
- `social_exchange_emission` owns strict-social fallback content.
- `upstream_response_repairs` packages upstream prepared emissions.
- Final emission gate selects/consumes prepared/sealed paths.
- Replay projection may report selection/content owners separately.

Tension:

- A single "fallback owner" field is often insufficient. The architecture needs a ledger separating content author, selector, packager, final applier, and projection owner.

### 4. Runtime Lineage Projection and Protected Replay Projection Are Intentionally Separate

Evidence:

- `docs/testing/protected_replay_manifest.md` and module docstrings explicitly forbid merging `game.final_emission_replay_projection` with `tests.helpers.golden_replay_projection`.

Tension:

- The split is correct but easy to violate because test projection imports runtime lineage helpers for diagnostics. AR-AA should document the direction of dependency: acceptance may consume runtime diagnostics; runtime must not consume acceptance schema.

### 5. Dual Fallback-Family Vocabulary Is Documented but Still a Cognitive Load

Evidence:

- Runtime FEM may carry `fallback_family_used` and `realization_fallback_family`.
- Golden replay projects one observed `fallback_family` with diegetic-first precedence.

Tension:

- This is a compatibility projection, not runtime topology collapse. Future work must avoid rewriting runtime fields just to satisfy replay field simplicity.

### 6. Opening Scene Ownership Is Split Across Planning, Realization Helpers, Upstream Prepared Fallback, and Gate Selection

Evidence:

- `opening_scene_realization.py` says structural opening obligations are owned by `narrative_planning`.
- API creates `scene_opening` resolution and start-campaign bootstrap.
- Opening deterministic fallback/upstream prepared payloads feed final emission.
- Gate selects accepted/prepared/fallback opening text.

Tension:

- Opening has many surfaces because it crosses first-turn state, prompt planning, GPT prose, fallback, and final text invariants. This needs a flow map more than a refactor-first approach.

### 7. Evidence Artifacts Are Strong but Heavy

Evidence:

- Foundation closeout and CV corrective locality note high evidence-bearing file fanout.
- Replay, fallback incidence, semantic mutation, provenance, recurrence, and ownership artifacts are all active.

Tension:

- More stabilization-style evidence could increase maintenance cost. Architecture Reconciliation should reduce coordination cost and clarify which evidence surfaces are canonical vs advisory.

### 8. Documentation Mostly Agrees with Implementation, but Some Docs Are Target-State Ledgers

Evidence:

- `docs/architecture_ownership_ledger.md` explicitly says ownership declarations establish cleanup targets and do not prove current code is already clean.

Tension:

- Next-cycle GPT instructions should avoid treating ledgers as proof that implementation fully conforms. Use them as target-state authority and compare against current call paths.

## 7. Candidate File List for GPT

Highest-priority architecture files:

- `game/api.py`
- `game/final_emission_runtime.py`
- `game/final_emission_gate.py`
- `game/final_emission_finalize.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/prompt_context.py`
- `game/narration_plan_bundle.py`
- `game/state_authority.py`
- `game/storage.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/fallback_provenance_debug.py`
- `game/opening_scene_realization.py`
- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/social_exchange_emission.py`

Highest-priority docs:

- `docs/architecture_ownership_ledger.md`
- `docs/ctir_prompt_adapter_architecture.md`
- `docs/final_emission_ownership_convergence.md`
- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- `docs/runtime_persistence_envelope.md`
- `docs/realization_provenance_audit.md`
- `docs/audits/foundation_stabilization_closeout_discovery.md`

Highest-priority tests / test helpers:

- `tests/test_start_campaign_api.py`
- `tests/test_opening_scene_realization.py`
- `tests/test_realization_authority.py`
- `tests/test_realization_provenance.py`
- `tests/test_ctir_runtime_lifecycle.py`
- `tests/test_ctir_retry_stability.py`
- `tests/test_ctir_turn_packet_boundary.py`
- `tests/test_final_emission_gate_orchestration_order.py`
- `tests/test_final_emission_meta.py`
- `tests/test_replay_boundary_governance.py`
- `tests/test_protected_replay_registry.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/protected_replay_registry.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_trend.py`

Optional if GPT has more budget:

- `game/output_sanitizer.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/noncombat_resolution.py`
- `tests/ownership_guard_bn_gate_context.py`
- `tests/ownership_guard_bi8_golden_replay_boundary.py`
- `tools/realization_provenance_audit.py`
- `tools/fallback_incidence_report.py`
- `tools/run_protected_replay_trend.py`

## 8. Suggested AR-AA Cycle Focus

Recommended primary focus:

1. **Authority / ownership ledger**
2. **Runtime flow map**

Recommended secondary focus:

3. **Replay / evidence map**
4. **Architectural tension audit**

Rationale:

- The implementation already contains many ownership declarations. The next useful cycle should reconcile them into a compact current-state map rather than add more isolated audits.
- Runtime flow mapping should start with `/api/start_campaign` and the shared resolved-turn pipeline because that is the Campaign 1 entrypoint and it crosses CTIR, opening realization, GPT/retry, final emission, persistence, and replay evidence.
- Replay/evidence mapping should be included, but as a boundary map: runtime diagnostic projection vs protected acceptance projection vs governance docs vs advisory reports.

Suggested AR-AA cycle title:

**AR-AA1: Runtime Authority and Replay Boundary Map**

Suggested GPT instruction emphasis:

- Do not refactor first.
- Produce a compact owner ledger that separates:
  - runtime owner
  - content author
  - selector/applicator
  - provenance packager
  - replay projection owner
  - protected acceptance owner
- Use `/api/start_campaign` as the first concrete flow.
- Treat `docs/architecture_ownership_ledger.md` as target-state authority, not proof of full implementation conformity.
- Preserve the AO5 runtime-vs-acceptance replay split.
- Preserve the dual fallback-family contract until a future cycle explicitly collapses it with replay proof.

## 9. Validation Notes

No pytest suite was run for this discovery pass. The report is based on targeted static inspection of runtime modules, ownership docs, replay manifests, and relevant tests. Existing untracked files present before this report were left untouched.
