# AR-AG Final Vision Compatibility Discovery

Date: 2026-07-14  
Scope: repository-wide evidence discovery for Campaign 2 / Final Vision Compatibility  
Mode: documentation-only assessment preparation; no runtime behavior changes

## 1. Executive Summary

The reconciled architecture gives the long-term vision a strong baseline, especially for low-context runtime operation, repository handoff evidence, feature-locality discipline, UI/tooling foundations, and player trust/provenance. The system should not be treated as architecturally broken. Campaign 1 established a coherent target architecture and AR-AE found the implementation mostly conformant.

This cycle does not make the final compatibility verdict. It gathers evidence for that later judgment.

Provisional findings:

- `SUPPORTED`: Low-context runtime operation; player trust, provenance, and explainability.
- `PARTIALLY SUPPORTED`: Modular ruleset support; multiple AI backend support; clean repository handoff; straightforward feature extensibility; UI and tooling readiness.
- No objective currently has enough evidence to justify `ARCHITECTURAL EVOLUTION REQUIRED`, but several would need local architectural refinement before they could be called fully supported.

The largest cross-cutting gaps are:

- No explicit ruleset packaging/selection/version contract.
- No provider-neutral AI backend interface, despite strong model-routing foundations.
- No durable short-form handoff index that separates current authority docs from historical campaign reports.
- No versioned public application API/event model, despite a usable FastAPI/browser UI surface.
- Evidence and governance surfaces remain numerous enough that external review still needs a curated file set.

## 2. Scope and Method

This pass reviewed:

- Campaign 1 Architecture Reconciliation outputs: `AR-AA` through `AR-AF`.
- Foundation Stabilization closeout artifacts.
- Durable architecture docs under `docs/`.
- Runtime modules under `game/`.
- Relevant test and replay governance surfaces under `tests/` and `tools/`.
- Static UI and setup surfaces.

No tests were run. No runtime files were changed.

The classification scale is provisional:

- `SUPPORTED`: Architecture already contains required boundaries, contracts, ownership model, and extension points.
- `PARTIALLY SUPPORTED`: Viable foundation exists, but contracts, abstractions, documentation, or local boundaries need refinement.
- `ARCHITECTURAL EVOLUTION REQUIRED`: Required structural capability is absent.
- `INSUFFICIENT EVIDENCE`: Repository does not provide enough evidence for a reliable classification.

## 3. Architectural Baseline

The baseline is the AR-AF synthesis: a single-turn runtime transaction with explicit domain ownership, CTIR-backed narration meaning, final-emission legality/packaging, durable persistence, one-way replay projection, and governance as doctrine.

Major layers:

- Request/API: `game.api` owns FastAPI routes, request eligibility, turn transaction entry/exit, response payloads.
- Runtime orchestration: `game.api._run_resolved_turn_pipeline`, `_build_gpt_narration_from_authoritative_state`, `_complete_opening_turn_persistence_like_chat`, CTIR lifecycle placement.
- Domain simulation: `game.noncombat_resolution`, `game.exploration`, `game.social`, `game.combat`, `game.world_progression`, `game.interaction_context`, `game.scene_actions`, `game.skill_checks`.
- Narrative/AI: `game.ctir`, `game.ctir_runtime`, `game.prompt_context`, `game.narration_plan_bundle`, `game.gm`, `game.model_routing`.
- Final emission: `game.final_emission_runtime`, `game.final_emission_gate`, `game.final_emission_finalize`, `game.final_emission_meta`, repair/validator/sanitizer modules.
- Persistence: `game.storage`, `game.campaign_state`, `game.session`, `game.campaign_reset`.
- Replay/evidence: `game.final_emission_replay_projection`, `tests.helpers.golden_replay_projection`, protected replay registry/fields, replay trend tools.
- Governance: `docs/architecture_ownership_ledger.md`, `docs/testing/protected_replay_manifest.md`, replay governance docs/tests, ownership guard tests.

Runtime flow:

1. API loads persisted state.
2. Intent/action is normalized and resolved by engine/domain modules.
3. Authoritative state mutation occurs before narration.
4. CTIR is attached once per resolved turn.
5. Prompt context adapts CTIR, visibility, plans, and read models.
6. `game.gm.call_gpt` calls the selected model and normalizes/guards output.
7. API retry/fallback orchestration handles validation/upstream failures.
8. Final emission selects/legalizes/packages final player-facing text and FEM.
9. Storage persists session/world/combat/logs; API returns payload.
10. Replay/evidence layers observe finalized payloads, logs, snapshots, FEM, and traces.

Authority boundaries:

- GPT/model output never mutates runtime truth directly (`game.state_authority`, `docs/state_authority_model.md`).
- CTIR owns resolved-turn meaning for narration, not canonical state (`game.ctir`, `game.ctir_runtime`).
- Prompt context is an adapter, not semantic authority (`docs/ctir_prompt_adapter_architecture.md`).
- Final emission owns last-mile legality/packaging/FEM, with remaining semantic repair pressure classified as transitional (`AR-AD`, `AR-AE`).
- Runtime diagnostic projection and protected replay acceptance are intentionally separate (`game.final_emission_replay_projection`, `docs/testing/protected_replay_manifest.md`).

Core extension points:

- Domain modules and standardized engine result schemas in `game.models`.
- Non-combat contract seam in `game.noncombat_resolution`.
- State-domain registry and cross-domain allow-list in `game.state_authority`.
- CTIR schema/lifecycle in `game.ctir` and `game.ctir_runtime`.
- Model routing in `game.model_routing`.
- Final-emission layer stack and ownership modules.
- UI mode policy/projection in `game.ui_mode_policy` and `game.state_channels`.
- Replay/provenance projection and protected replay fields.

Repository-level assumptions:

- Local Python/FastAPI app with browser UI (`docs/README.md`, `run.py`, `static/`).
- OpenAI API key required for live upstream narration (`game.config`, `.env.example`).
- JSON files under `data/` are local persistence roots; session/combat use versioned envelopes (`docs/runtime_persistence_envelope.md`).
- Protected replay, audit, and governance evidence are first-class, but many artifacts are advisory/generated.

Areas intentionally constrained during Foundation Stabilization:

- No broad feature expansion through final emission, fallback, sanitizer, protected replay schema, recurrence, or speaker/finalization seams.
- Preserve runtime-vs-acceptance replay separation.
- Preserve multi-axis fallback/provenance ownership.
- Treat generated/advisory artifacts as evidence unless explicitly promoted.

## 4. Evidence Sources Reviewed

Primary Campaign 1 baseline:

- `AR-AA_architectural_mapping_discovery.md`
- `AR-AB_runtime_authority_and_replay_boundary_map.md`
- `AR-AC_architectural_ownership_reconciliation.md`
- `AR-AD_target_architecture_doctrine.md`
- `AR-AE_architecture_conformance_assessment.md`
- `AR-AF_architecture_reconciliation_synthesis.md`

Foundation and stabilization:

- `CX_final_foundation_stabilization_closeout_discovery.md`
- `docs/audits/foundation_stabilization_closeout_discovery.md`
- `CV_corrective_locality_confirmation_discovery.md`
- `CT_runtime_fallback_incidence_baseline_discovery.md`
- `CT_projection_fidelity_audit.md`

Architecture and runtime docs:

- `docs/README.md`
- `docs/system_overview.md`
- `docs/architecture_ownership_ledger.md`
- `docs/state_authority_model.md`
- `docs/ctir_prompt_adapter_architecture.md`
- `docs/model_routing_architecture.md`
- `docs/runtime_persistence_envelope.md`
- `docs/world_simulation_backbone.md`
- `docs/objective15_ui_mode_separation.md`
- `docs/testing/protected_replay_manifest.md`

Key runtime modules:

- `game/api.py`
- `game/models.py`
- `game/storage.py`
- `game/state_authority.py`
- `game/noncombat_resolution.py`
- `game/combat.py`
- `game/skill_checks.py`
- `game/world_progression.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/gm.py`
- `game/model_routing.py`
- `game/config.py`
- `game/api_upstream_preflight.py`
- `game/upstream_dependent_run_gate.py`
- `game/ui_mode_policy.py`
- `game/state_channels.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`

UI/setup surfaces:

- `static/app.js`
- `static/index.html`
- `.env.example`
- `requirements.txt`
- `run.py`
- `Makefile`

## 5. Vision Compatibility Matrix

| Vision Objective | Provisional Status | Strongest Supporting Evidence | Principal Limitation | Likely Work Type | Confidence |
|---|---|---|---|---|---|
| Modular ruleset support | PARTIALLY SUPPORTED | Domain modules, standardized engine result schemas, state authority domains, non-combat contract, scene/config-driven checks | No ruleset registry/package/selection/version contract; PF1e-inspired assumptions in combat, skills, spells, docs | Local architectural refinement plus implementation | Medium |
| Multiple AI backend support | PARTIALLY SUPPORTED | `game.model_routing.resolve_model_route`, env model lanes, route metadata, upstream error normalization, fakeable tests | `game.gm.call_gpt` directly imports OpenAI client and Responses API; no provider-neutral backend protocol | Local architectural refinement plus adapter implementation | High |
| Clean repository handoff | PARTIALLY SUPPORTED | `docs/README.md`, setup/env docs, persistence docs, ownership ledger, Campaign 1 synthesis, tests/tools | Critical current architecture context is spread across root campaign reports and many audits; no concise handoff map | Documentation and repo hygiene | High |
| Low-context runtime operation | SUPPORTED | Durable JSON state, CTIR, bounded prompt context, session logs, snapshots, replay projections, state authority | Token budgeting/retrieval/instrumentation are not fully productized | Implementation/optimization, not broad architecture | High |
| Straightforward feature extensibility | PARTIALLY SUPPORTED | Domain owners, final-emission layer stack, state authority, CTIR, replay guards, feature-readiness pilots | `game.api` and final-emission/fallback/provenance fields remain coordination hotspots | Documentation and local architectural refinement | Medium-High |
| UI and tooling readiness | PARTIALLY SUPPORTED | FastAPI endpoints, static browser UI, `GET /api/state?ui_mode=...`, ui_mode lanes, snapshots, debug projection | API is internal dict-oriented; no versioned public command/query/event model | Local architectural refinement plus implementation | High |
| Player trust, provenance, and explainability | SUPPORTED | Provenance taxonomy, FEM, runtime lineage projection, protected replay manifest, state authority, visibility/channel separation | Player-facing challenge/inspection UX and hidden-info redaction policy are not fully specified | Implementation/product decision plus documentation | High |

## 6. Modular Ruleset Support

Provisional classification: `PARTIALLY SUPPORTED`.

Supporting evidence:

- `game.models` defines standardized `ExplorationEngineResult`, `CombatEngineResult`, `SocialEngineResult`, `make_check_request`, and runtime normalization helpers. These provide common downstream result shapes.
- `game.noncombat_resolution` defines a contract-first non-combat taxonomy with explicit authority domains and fail-closed unsupported outcomes. It delegates to `game.exploration` and `game.social` when routable.
- `game.skill_checks` centralizes deterministic skill-check triggering and resolution. Scene/interactable config can supply skill/DC requirements.
- `game.combat` isolates basic combat mechanics such as initiative, attacks, spells, conditions, and turn advancement behind combat resolver functions.
- `game.state_authority` names runtime state domains and prevents GPT/model-originated output from becoming authoritative mutation.
- `docs/ctir_prompt_adapter_architecture.md` explicitly says future downtime/new non-combat categories need a real engine owner and contract fields, not prompt heuristics.

Limiting evidence:

- No file or symbol found for a ruleset registry, ruleset protocol, ruleset package manifest, or runtime ruleset selection.
- The app is documented as "PF1e-inspired" in `docs/README.md`; current supported mechanics include specific actions/spells such as Daze, Magic Missile, Shield, Risky Strike, Defensive Stance.
- `game.skill_checks` embeds skill names and DC conventions directly (`diplomacy`, `intimidate`, `bluff`, DC bands).
- `game.combat` reads character attacks/spells/conditions directly and contains mechanics-specific assumptions.
- Ruleset identity/version is visible for some subsystems (`NONCOMBAT_FRAMEWORK_VERSION`, CTIR version, narrative plan versions), but not as a global runtime/replay/provenance ruleset identity.
- No evidence that multiple rulesets can coexist or be independently initialized/tested.

Existing abstractions or extension points:

- Engine result schemas.
- Non-combat framework contract.
- Scene/interactable-driven skill check configuration.
- Conditions data loaded from `data/conditions.json`.
- State authority domains and mutation traces.
- CTIR bounded projection.

Missing abstractions or contracts:

- `Ruleset` interface/protocol.
- Ruleset package layout and registry.
- Ruleset selection/configuration.
- Ruleset identity/version in session, CTIR, replay, and provenance.
- Ruleset-owned combat/skill/spell/action adapters.
- Tests demonstrating a second ruleset or a fake ruleset.

Likely remaining work:

- Local architectural refinement for the ruleset boundary.
- Implementation for actual alternate ruleset adapters.
- Documentation for packaging, selection, versioning, and test strategy.

Confidence: Medium.

Open questions:

- Should the product support multiple d20-family variants only, or genuinely different game systems?
- Must multiple rulesets coexist in one campaign repository, or is one active ruleset per deployment enough?
- Should authored scene content be ruleset-neutral or ruleset-specific?

## 7. Multiple AI Backend Support

Provisional classification: `PARTIALLY SUPPORTED`.

Supporting evidence:

- `game.model_routing.ModelRouteDecision` and `resolve_model_route` provide deterministic model selection from explicit runtime inputs.
- `game.config` supports `MODEL_NAME`, `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, `RETRY_ESCALATION_MODEL_NAME`, and `ENABLE_MODEL_ROUTING`.
- `docs/model_routing_architecture.md` documents route inputs, escalation triggers, and unchanged player-facing schema.
- `game.gm._attach_model_route_metadata` records selected model, route reason/family/purpose, retry attempt, and escalation trigger.
- `game.gm._classify_upstream_gpt_error` normalizes auth, model, rate-limit, timeout, server, and connection failures.
- `game.api_upstream_preflight` probes upstream health and maps exceptions into a canonical preflight status.
- `tests/test_model_routing_runtime.py` uses monkeypatch/fake clients to prove routed model names flow through `call_gpt` and metadata is preserved.

Limiting evidence:

- `game.gm.call_gpt` directly imports `OpenAI`, constructs `OpenAI(api_key=get_openai_api_key())`, and calls `client.responses.create(...)`.
- `game.api_upstream_preflight` also assumes the OpenAI Responses API path.
- No provider-neutral request/response protocol exists for backends.
- No tool-call normalization, streaming abstraction, capability negotiation, local-inference adapter, or backend registry was found.
- Backend identity is captured as selected model/route metadata, not as a provider/backend contract.

Existing abstractions or extension points:

- Deterministic model routing by purpose/retry/social precision.
- Error classification and upstream gate.
- Metadata preservation through fallback paths.
- Tests that can substitute fake clients via monkeypatching.

Missing abstractions or contracts:

- Backend protocol such as `generate(messages, options) -> NormalizedModelResponse`.
- Backend registry/configuration including provider, model, capabilities, streaming/tool support, timeout/retry defaults.
- Provider identity in provenance and replay.
- Provider-specific error normalization boundary outside `game.gm`.
- Local backend and deterministic fake backend adapters.

Likely remaining work:

- Local architectural refinement: extract provider-neutral adapter boundary.
- Adapter implementation for OpenAI first, then other providers/local inference.
- Documentation for capability negotiation, retries, timeouts, structured outputs, and provenance fields.

Confidence: High.

Open questions:

- Which providers/backends are in scope: OpenAI-compatible APIs, local models, tool-calling providers, or all of them?
- Is streaming required for UI/tooling readiness?
- What backend capabilities must be recorded for trust/provenance?

## 8. Clean Repository Handoff

Provisional classification: `PARTIALLY SUPPORTED`.

Supporting evidence:

- `docs/README.md` provides features, requirements, setup, model configuration, supported mechanics, and project layout.
- `.env.example` documents required/optional env vars.
- `run.py` starts the FastAPI app and reports OpenAI key/reload/preflight information.
- `docs/runtime_persistence_envelope.md` documents versioned envelopes, atomic saves, snapshots, and runtime/static file separation.
- `docs/architecture_ownership_ledger.md`, `AR-AF`, and `AR-AD` provide architecture baseline and ownership doctrine.
- `docs/testing/protected_replay_manifest.md` documents protected replay commands and acceptance authority.
- `pytest.ini`, `Makefile`, `tests/conftest.py`, and many test docs provide test-entry evidence.

Limiting evidence:

- The most current architecture baseline is in untracked root `AR-*` campaign reports, not folded into a stable `docs/architecture/current.md` or similar.
- There is no short "start here" external reviewer index that separates current authority from historical/advisory artifacts.
- The repo contains many generated artifacts, audit reports, old compatibility docs, and temporary pytest directories, raising discovery cost.
- Handoff docs explain local operation, but not deployment topology, secret rotation, production mode, data migration policy, or repo distribution constraints.
- Some critical evidence exists as campaign reports rather than durable docs; Foundation closeout explicitly noted artifact inventory is hard to scan.

Existing abstractions or extension points:

- Setup/run docs.
- Environment template.
- Architecture doctrine and ownership docs.
- Protected replay and scenario-spine docs.
- Persistence/snapshot docs.

Missing abstractions or contracts:

- Current architecture index.
- Handoff checklist for new engineer/agent.
- Generated/transient artifact retention policy.
- Deployment/production runbook.
- Data initialization and migration guide.
- Secrets/security policy.

Likely remaining work:

- Documentation and repository hygiene.
- Possibly move or summarize AR-AF/AR-AD into durable docs.

Confidence: High.

Open questions:

- Is handoff intended for local-only solo development, hosted deployment, or both?
- Which artifacts should ship with a clean handoff?
- Should untracked AR reports be committed as long-term architecture docs?

## 9. Low-Context Runtime Operation

Provisional classification: `SUPPORTED`.

Supporting evidence:

- Runtime state is explicit and durable in JSON persistence roots (`game.storage`, `docs/runtime_persistence_envelope.md`).
- `compose_state` assembles state from campaign, character, session, world, combat, conditions, scene, journal, debug traces, save summary, and snapshots.
- `game.ctir` defines a bounded, deterministic, JSON-serializable resolved-turn meaning object with no prose.
- `game.ctir_runtime` attaches CTIR to session with a retry-stable stamp and detaches stale CTIR at resolved-turn entry.
- `docs/ctir_prompt_adapter_architecture.md` states prompt context consumes CTIR and must not reconstruct turn meaning when CTIR exists.
- `game.world_progression` builds bounded CTIR/prompt progression slices from native world roots and session fingerprints, not full event-log replay.
- `game.storage.create_snapshot`, `list_snapshots`, and `load_snapshot` support save/load and validate-before-commit restore.
- Session logs (`append_log`, `load_log`) and protected replay observations provide reconstruction/evidence surfaces.
- `game.conversational_memory_window` exists as a context-window component, and prompt construction is explicitly bounded by contracts/read models in Campaign 1 docs.

Limiting evidence:

- No full retrieval architecture or long-term memory store was found beyond persisted runtime documents, logs, CTIR, and memory-window helpers.
- Token/context budget instrumentation appears present in pieces, but not as a consolidated budget policy.
- Deterministic reconstruction from canonical state appears architecturally supported, but full product-level context regeneration requirements are not specified.

Existing abstractions or extension points:

- CTIR.
- Prompt context adapter.
- Runtime persistence envelopes.
- Snapshots/logs.
- World progression bounded export.
- State authority domains.
- Replay projections.

Missing abstractions or contracts:

- Explicit context budgeting policy.
- Retrieval/indexing contract if long campaigns require semantic search.
- Operator tooling to inspect exactly which context slices were used per turn.

Likely remaining work:

- Implementation/optimization and instrumentation, not broad architecture.

Confidence: High.

Open questions:

- How long is "low-context" expected to scale: dozens, hundreds, or thousands of turns?
- Is semantic retrieval required, or is canonical-state reconstruction sufficient?

## 10. Feature Extensibility

Provisional classification: `PARTIALLY SUPPORTED`.

Supporting evidence:

- AR-AD/AR-AF define stable layers and extension principles.
- `game.models` provides standardized engine result shapes.
- `game.noncombat_resolution` shows how a new structured contract can be added without making prompt heuristics authoritative.
- `game.state_authority` gives domain ownership and cross-domain write seams.
- Final-emission behavior is split across many owner modules rather than one unstructured gate.
- UI modes and state channels support future tools without leaking author/debug data into player surfaces.
- Replay/provenance/governance tools provide strong regression evidence for changes.
- Foundation/CQ-era feature-readiness docs show safe-domain feature pilots were possible, while high-risk seams were named.

Limiting evidence:

- `game.api` remains a broad transaction spine and a coordination hotspot.
- Final emission, fallback, provenance, and replay fields remain complex multi-axis surfaces.
- Adding major capabilities such as maps, portraits, economy, research/construction, new output formats, or new tools would likely require repeated API/UI/state/provenance/replay edits unless a feature-specific boundary is defined first.
- No plugin architecture or feature registry was found.
- Schema evolution practices exist locally, but not as a global migration/version policy.

Existing abstractions or extension points:

- Domain modules.
- State authority registry.
- Engine result schemas.
- CTIR and prompt adapter.
- Final-emission layer stack.
- UI mode/state channel projection.
- Replay/provenance protected fields.

Missing abstractions or contracts:

- Feature registry or capability registry.
- Public command/query application boundary.
- Schema migration/versioning policy across runtime docs, CTIR, replay, and UI.
- Dormant-feature configuration pattern.

Likely remaining work:

- Local architectural refinement and documentation.
- Implementation per feature.

Confidence: Medium-High.

Open questions:

- Which feature class is next: rules subsystem, UI inspector, maps, economy, or output format?
- Should future features be repo-native modules only, or separately packaged plugins?

## 11. UI and Tooling Readiness

Provisional classification: `PARTIALLY SUPPORTED`.

Supporting evidence:

- FastAPI app exists in `game.api`, with endpoints for state, log, campaign, scene, character, world, import, response mode, reset, new campaign, snapshots, start campaign, chat, and action.
- Static browser UI exists under `static/`.
- `docs/objective15_ui_mode_separation.md` declares `GET /api/state?ui_mode=...` as the authoritative frontend render source.
- `game.ui_mode_policy` defines fail-closed player/author/debug modes, visible tabs, state channels, and capability flags.
- `game.state_channels` projects public/debug/author payloads and strips disallowed keys.
- `compose_state` builds a single internal state snapshot before mode projection.
- Snapshot APIs and debug traces support tooling and inspection.
- `static/app.js` reloads render state from `/api/state` and clears forbidden DOM content on mode changes.

Limiting evidence:

- The API appears primarily internal to the current browser UI and uses dict payloads rather than versioned public schemas for all commands/queries.
- No event/update model or streaming response contract was found.
- No explicit command/query separation beyond endpoint naming and `GET /api/state`.
- No stable external tool API/versioning guarantee was found.
- Debug/author modes are useful, but administrative controls and inspectors are not yet a full tooling platform.

Existing abstractions or extension points:

- UI mode policy.
- Public/author/debug state channels.
- FastAPI endpoints.
- Snapshots and logs.
- Debug traces and FEM metadata.

Missing abstractions or contracts:

- Versioned public API schema.
- Event or incremental update stream.
- Idempotent command contract.
- Error model across endpoints.
- External tool auth/security model.
- Campaign/session resource boundary for multi-campaign or hosted use.

Likely remaining work:

- Local architectural refinement plus implementation.

Confidence: High.

Open questions:

- Is the target UI a local single-user app, hosted multi-user app, or operator/debug cockpit?
- Should external tools read raw internal payloads or a stable API facade?

## 12. Player Trust, Provenance, and Explainability

Provisional classification: `SUPPORTED`.

Supporting evidence:

- `game.state_authority` and `docs/state_authority_model.md` define domains, owners, forbidden model mutation, cross-domain write seams, and mutation traces.
- `game.realization_authority` declares allowed/forbidden authority for GPT realization, prompt context, final emission, retry, upstream prepared emission, diegetic fallback, and API emergency realization.
- `game.realization_provenance` stamps governed fallback family metadata and explicitly preserves dual runtime/replay vocabulary.
- `game.final_emission_replay_projection` derives diagnostic runtime lineage events from finalized FEM and records split ownership for selection/content/provenance paths.
- `docs/testing/protected_replay_manifest.md` documents protected replay fields, runtime-vs-acceptance projection separation, dual fallback-family contract, and drift policy.
- Final-emission metadata, stage diff telemetry, sanitizer traces, response-type contracts, speaker traces, and replay projections give rich "what happened and who changed it" evidence.
- UI mode/channel separation guards hidden/debug/author data from player surfaces.
- Foundation closeout reports stable protected replay drift and fallback/provenance evidence.

Limiting evidence:

- Player-facing explainability UX is not yet a product surface. The architecture can explain, but the player may not have a polished challenge/inspect workflow.
- Hidden-versus-player-visible redaction policy exists structurally through channels/visibility, but a player-safe ruling explanation contract is not fully specified.
- Backend/provider identity provenance is model-level today, not provider/capability-level.
- Ruleset identity/version provenance is not globally represented.

Existing abstractions or extension points:

- FEM and runtime lineage events.
- Realization/provenance taxonomy.
- State mutation traces.
- Protected replay observations.
- UI channels and visibility contracts.
- Logs/snapshots.

Missing abstractions or contracts:

- Player-facing ruling explanation schema.
- Challenge/correction workflow.
- Redaction policy for hidden information in explanations.
- Backend/ruleset/prompt/tool version bundle.

Likely remaining work:

- Implementation/product decision and documentation, not broad architectural evolution.

Confidence: High.

Open questions:

- How much provenance should players see versus operators?
- Should challenge workflows be reversible state transactions, annotations, or replay branches?

## 13. Cross-Cutting Architectural Gaps

1. Ruleset identity and packaging.

   Affects modular rulesets, provenance, replay, feature extensibility, and handoff. Current domain boundaries are useful, but no global ruleset contract exists.

2. Provider-neutral AI backend boundary.

   Affects multiple AI backends, provenance, UI/tooling, low-context operation, and handoff. Model routing is strong but provider client code is still OpenAI-specific.

3. Versioning and migration strategy.

   Affects rulesets, UI APIs, replay fields, CTIR, runtime envelopes, snapshots, and external tooling. Local versions exist; global policy is not evident.

4. Public application boundary.

   Affects UI/tooling, feature extensibility, clean handoff, and external review. FastAPI endpoints exist, but a stable public command/query/event API is not defined.

5. Evidence canonicality and handoff index.

   Affects handoff, external review, trust, and feature extensibility. Campaign reports and audits are strong but numerous.

6. Capability negotiation.

   Affects AI backends, tools, rulesets, and UI. No consolidated capability description exists for models, rulesets, output modes, or tools.

These gaps should not be inflated into a redesign claim. They are mostly local architectural refinements over an otherwise coherent baseline.

## 14. Architecture vs. Implementation Distinction

| Limitation | Classification |
|---|---|
| No alternate ruleset implementation | Missing implementation on top of partial architecture |
| No ruleset registry/selection/version identity | Local architectural refinement |
| PF1e-inspired skill/combat assumptions | Local architectural refinement plus implementation |
| No non-OpenAI backend implementation | Missing implementation |
| Direct OpenAI client in `game.gm.call_gpt` | Local architectural refinement |
| No streaming/tool-call backend abstraction | Local architectural refinement or product decision |
| AR doctrine mostly in root reports | Documentation/handoff gap |
| Large generated/audit artifact surface | Repository hygiene/documentation gap |
| No public versioned API/event model | Local architectural refinement |
| No player-facing ruling challenge UX | Missing implementation/product decision |
| No global ruleset/backend version provenance bundle | Local architectural refinement |
| Final-emission semantic repair pressure | Known transitional responsibility, not a fresh vision blocker |
| Broad `game.api` spine | Intentional architecture with delegate/documentation refinement candidates |

## 15. Missing Evidence and Requested Inputs

Requested from project owner:

- Ruleset scope: which systems must be supported, whether multiple rulesets coexist, and whether rulesets are packages/plugins or in-repo modules.
- Backend scope: required AI providers, local inference expectations, streaming/tool-call requirements, and acceptable fallback/degradation behavior.
- Deployment target: local-only, hosted single-user, hosted multi-user, or hybrid.
- UI/tooling target: player UI only, authoring tools, debug/operator console, external API, or all of them.
- Explainability target: what players may inspect, how hidden info is redacted, and what challenge/correction flow should exist.
- Repository distribution constraints: whether generated artifacts should ship, be archived, or be regenerated.
- Version/migration expectations for saved campaigns, snapshots, rulesets, backend configs, and replay/provenance schemas.

The repository may already contain some of this under historical docs, but no concise current product-vision document was found during this pass.

## 16. Candidate Priorities for Later Campaign Cycles

1. Ruleset compatibility decision record.
2. AI backend adapter boundary design.
3. Current architecture handoff index under `docs/`.
4. Public API/tooling boundary inventory.
5. Provenance version bundle inventory: backend, model, ruleset, prompt/policy, runtime, CTIR, final-emission schema.
6. Evidence/artifact retention and canonicality index.
7. Player-safe explanation/challenge workflow discovery.

## 17. Recommended Next Cycle

Recommended next cycle: **AR-AH - Vision Compatibility Assessment**.

Purpose:

- Use this evidence matrix to issue the actual compatibility verdict.
- Decide which `PARTIALLY SUPPORTED` objectives are local refinement versus broader evolution.
- Prioritize ruleset packaging, backend provider abstraction, handoff docs, and public UI/tooling API according to product goals.

Non-goals:

- Do not implement a ruleset or backend plugin system yet.
- Do not refactor `game.api` broadly.
- Do not collapse replay/provenance fields.
- Do not promote advisory evidence into protected acceptance without governance review.

## 18. Files Most Useful for External Review

First-pass architecture:

- `AR-AF_architecture_reconciliation_synthesis.md`
- `AR-AD_target_architecture_doctrine.md`
- `AR-AE_architecture_conformance_assessment.md`
- `AR-AG_final_vision_compatibility_discovery.md`

Runtime flow and ownership:

- `game/api.py`
- `game/state_authority.py`
- `docs/state_authority_model.md`
- `game/models.py`
- `game/noncombat_resolution.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `docs/ctir_prompt_adapter_architecture.md`

AI/backend:

- `game/gm.py`
- `game/model_routing.py`
- `game/config.py`
- `game/api_upstream_preflight.py`
- `docs/model_routing_architecture.md`
- `tests/test_model_routing_runtime.py`

Persistence/UI/tooling:

- `docs/README.md`
- `docs/runtime_persistence_envelope.md`
- `game/storage.py`
- `game/ui_mode_policy.py`
- `game/state_channels.py`
- `docs/objective15_ui_mode_separation.md`
- `static/app.js`

Trust/replay/provenance:

- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`
- `docs/testing/protected_replay_manifest.md`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_fields.py`

Foundation context:

- `docs/audits/foundation_stabilization_closeout_discovery.md`
- `CX_final_foundation_stabilization_closeout_discovery.md`
- `CT_runtime_fallback_incidence_baseline_discovery.md`
- `CT_projection_fidelity_audit.md`
- `CV_corrective_locality_confirmation_discovery.md`

## Validation Notes

This report is based on static repository inspection and prior campaign artifacts. No pytest suite was run. No implementation or behavior changes were made.
