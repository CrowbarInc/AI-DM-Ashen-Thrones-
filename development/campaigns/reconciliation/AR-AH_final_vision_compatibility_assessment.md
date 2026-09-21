# AR-AH Final Vision Compatibility Assessment

Date: 2026-07-14  
Scope: final architectural assessment for Campaign 2 / Final Vision Compatibility  
Inputs: `AR-AG_final_vision_compatibility_discovery.md`, `AR-AF_architecture_reconciliation_synthesis.md`, `AR-AD_target_architecture_doctrine.md`, `AR-AE_architecture_conformance_assessment.md`  
Mode: documentation-only architectural judgment; no implementation changes

## 1. Executive Verdict

The reconciled architecture is compatible with the long-term vision under the working assumptions in this cycle.

Final classifications:

- `ARCHITECTURALLY ENABLED`
  - Clean repository handoff
  - Low-context runtime operation
  - Straightforward feature extensibility
  - Player trust, provenance, and explainability
- `ENABLED WITH LOCAL REFINEMENT`
  - Modular ruleset support
  - Multiple AI backend support
  - UI and tooling readiness
- `REQUIRES ARCHITECTURAL EVOLUTION`
  - None.
- `DECISION DEPENDENT`
  - None as the final classification, though several implementation designs remain product-decision dependent.

Architectural judgment:

The current architecture already contains the durable foundations Campaign 2 needed to evaluate: one runtime transaction spine, domain-owned simulation truth, CTIR as the narration meaning boundary, prompt construction as an adapter, GPT/model routing as expression rather than truth, final emission as legality/packaging/provenance, durable persistence, one-way replay projection, and governance as doctrine. AR-AE found no significant divergence from AR-AD doctrine, and AR-AG found no objective that justified architectural evolution.

The remaining work is real, but it is mostly bounded: a ruleset contract, a provider-neutral backend adapter, a durable handoff index, public/tooling API decisions, a provenance/version bundle, and player-safe explanation schemas. These are local refinements and implementation prerequisites for affected feature classes, not a return to broad Architecture Reconciliation.

Roadmap recommendation: `CONTINUE WITH TARGETED PREREQUISITES`.

Controlled feature expansion is appropriate after a small set of prerequisites are produced for the feature class being attempted. Large-scale feature expansion across rulesets, backends, public APIs, and player-facing explainability should wait for the relevant local seams, but safe bounded features can proceed without redesigning the architecture.

## 2. Assessment Scope and Working Assumptions

This assessment uses AR-AG as the primary evidence inventory and Campaign 1 doctrine/conformance reports as the architectural baseline. It does not repeat repository-wide discovery.

Working assumptions from the cycle brief:

- Rulesets: one active ruleset per campaign; selected at campaign creation; long-term includes systems beyond PF1e; multiple unrelated rulesets do not need to execute in the same turn.
- AI backends: OpenAI, one additional remote provider, and local inference should eventually be possible; streaming and tool calling are desirable but not first-boundary requirements; deterministic fake backends are required for tests; backend/model identity belongs in provenance.
- Deployment: local single-user remains primary near-term; hosted or multi-user is possible future scope; local-only and online-backed modes should remain possible.
- UI/tooling: player UI and author/debug tools are desirable; third-party integrations are not immediate; hosted multi-user control plane is outside this campaign scope.
- Explainability: players should inspect safe explanations of mechanical outcomes; hidden information remains protected; operators may access deeper provenance; formal dispute reversal or replay branching is later product scope.

Product-dependent conclusions:

- Simultaneous multi-ruleset execution, hosted multi-user deployment, real-time collaborative tooling, and fully general third-party API integrations would need additional design. Under this cycle's assumptions, they do not change the final classifications.

## 3. Final Vision Compatibility Matrix

| Vision Objective | Final Classification | Existing Architectural Strength | Remaining Gap | Work Type | Blocks What? | Confidence |
|---|---|---|---|---|---|---|
| Modular ruleset support | ENABLED WITH LOCAL REFINEMENT | Domain modules, state authority, engine result schemas, CTIR, non-combat contract | No ruleset interface, registry, selection, package layout, or version identity | Local architectural refinement + implementation | Alternate ruleset implementation | Medium-High |
| Multiple AI backend support | ENABLED WITH LOCAL REFINEMENT | Model routing, route metadata, error normalization, retry/fallback separation, fake-client tests | OpenAI client/Responses path is direct in `game.gm.call_gpt` and preflight | Local architectural refinement + adapter implementation | Additional provider/local backend implementation | High |
| Clean repository handoff | ARCHITECTURALLY ENABLED | Setup docs, env template, persistence docs, ownership doctrine, replay manifest, AR-AF baseline | Current authority is spread across reports/audits; no concise durable "start here" index | Documentation + operational hygiene | External review and efficient onboarding, not feature work | High |
| Low-context runtime operation | ARCHITECTURALLY ENABLED | Explicit durable state, CTIR, bounded prompt context, logs, snapshots, replay projection, world progression slices | Retrieval, token budgeting, and long-campaign instrumentation are not consolidated | Implementation/optimization | Very long campaigns or semantic-memory features | High |
| Straightforward feature extensibility | ARCHITECTURALLY ENABLED | Stable layer doctrine, domain owners, state authority, CTIR, final-emission stack, UI lanes, replay guards | Some feature classes need local seams before broad work | Mostly implementation; local refinement for high-impact classes | Broad ruleset/backend/public-tooling features | Medium-High |
| UI and tooling readiness | ENABLED WITH LOCAL REFINEMENT | FastAPI, static UI, `GET /api/state?ui_mode=...`, UI modes, state channels, snapshots, logs, debug lanes | No versioned public command/query API, event stream, or hosted security model | Local architectural refinement + implementation | External tooling and hosted/multi-user UI | High |
| Player trust, provenance, and explainability | ARCHITECTURALLY ENABLED | State authority, CTIR, realization authority, FEM, runtime lineage, protected replay, visibility separation | Player-safe explanation schema, redaction policy, and challenge UX are not productized | Product decision + implementation + local schema refinement | Player-facing explanation/challenge UI | High |

## 4. Modular Ruleset Compatibility

Final classification: `ENABLED WITH LOCAL REFINEMENT`.

Fact:

AR-AG found strong ruleset-adjacent foundations: `game.models` standardizes exploration/combat/social result schemas; `game.noncombat_resolution` defines a contract-first non-combat seam; `game.skill_checks` centralizes deterministic checks; `game.combat` isolates current combat mechanics; `game.state_authority` separates runtime domains; CTIR consumes bounded engine-owned meaning rather than prompt prose.

Campaign 1 doctrine supports this: AR-AD assigns authoritative outcomes to domain simulation modules and forbids GPT/prompt/final emission from owning game truth. AR-AF says domain modules own simulation truth and CTIR is a resolved-turn meaning boundary.

Architectural judgment:

The current architecture can support modular rulesets, but the first alternate ruleset should not be implemented by scattering conditional PF1e-vs-other behavior through `game.api`, `game.combat`, `game.skill_checks`, and prompt code. A bounded ruleset contract is needed first.

Scope A: one active ruleset per campaign or deployment.

Under the working assumption of one active ruleset per campaign, the architecture is close. The minimum architecture is local:

- A ruleset identity/version stored on campaign/session creation.
- A ruleset registry or resolver that maps identity to domain adapters.
- A minimal `Ruleset` contract covering action taxonomy, skill/check model, combat resolver hooks, condition data, character import expectations, and CTIR/provenance identity fields.
- Tests with a fake/minimal ruleset, not necessarily a full second commercial-grade ruleset.

This preserves the current transaction spine: `game.api` would still orchestrate the turn, domain modules/adapters would still own mechanics, CTIR would still carry bounded resolved meaning, and replay/provenance would observe finalized results.

Scope B: multiple rulesets or materially different game systems.

For systems materially unlike PF1e, the current architecture remains directionally compatible, but the ruleset contract must be more explicit. Combat, skill checks, spells, progression, inventory, and character sheet assumptions are currently PF1e-inspired implementation details. That is not architectural incompatibility, but it means broad ruleset work should begin with adapter boundaries rather than central switches.

Limitation type:

- No alternate ruleset: implementation absence.
- No ruleset registry/interface/version identity: local architectural refinement.
- PF1e assumptions in combat/skills/spells: implementation plus local refinement.
- Simultaneous unrelated rulesets in one turn: product decision; likely future architecture if ever required, but outside current assumptions.

Would implementation be safe before resolving it?

- Safe for small same-family rule additions inside current PF1e-inspired mechanics.
- Not safe for an alternate ruleset until a ruleset identity/adapter seam exists.

Minimum architectural action:

Create a short ruleset decision record and minimal ruleset contract before implementing the first alternate ruleset.

What should not be redesigned:

- Do not replace `game.api` as transaction spine.
- Do not make prompt construction or GPT own mechanics.
- Do not create a generic plugin framework before a concrete second ruleset proves it necessary.
- Do not collapse state authority domains into ruleset-specific stores.

Priority:

`P1 - Required before the affected feature class`.

## 5. Multiple AI Backend Compatibility

Final classification: `ENABLED WITH LOCAL REFINEMENT`.

Fact:

AR-AG found a strong model-routing foundation: `game.model_routing.resolve_model_route`, environment model lanes in `game.config`, route metadata stamping in `game.gm`, upstream error classification, preflight gating, and fake-client tests in `tests/test_model_routing_runtime.py`. AR-AD already says GPT/model routing owns expression and model I/O, while runtime retry/fallback remains with the transaction spine.

Limitation:

The provider client is not abstracted. `game.gm.call_gpt` directly imports `OpenAI`, constructs an OpenAI client, and calls `client.responses.create(...)`. `game.api_upstream_preflight` is also OpenAI Responses API specific.

Architectural judgment:

Extracting a provider-neutral backend protocol is a local adapter-boundary refinement, not architectural evolution. It preserves the existing authority model:

- `game.api` keeps retry/fallback orchestration.
- `game.gm` or a nearby backend module keeps model I/O normalization.
- GPT/model output remains candidate expression, not runtime truth.
- Final emission and provenance continue to stamp/observe outcomes.

Minimum first backend contract:

- Input: normalized messages, route decision, purpose, retry metadata, response/structured-output requirements where applicable, timeout/options.
- Output: normalized candidate text or structured dict, backend/provider identity, model identity, route metadata, usage/latency if available, normalized error object.
- Error model: retryable/nonretryable, failure class, status/code/message excerpt, provider identity.
- Test backend: deterministic fake implementation.
- Provenance fields: provider, model, backend adapter, route family/reason, capability flags used.

Capabilities that can be deferred:

- Streaming.
- Tool calling.
- Rich capability negotiation.
- Multi-modal input/output.
- Local batching/queueing.
- Advanced fallback policies across providers.

Capabilities that should be in the first seam:

- Provider/model identity.
- Text/structured-output normalization sufficient for current `guard_gm_output`.
- Error normalization.
- Deterministic fake backend.
- Configuration-driven selection.

Limitation type:

- No non-OpenAI implementation: implementation absence.
- Direct OpenAI client: local architectural refinement.
- Streaming/tool calling/capability negotiation: later local refinements, product-dependent.

Would implementation be safe before resolving it?

- Safe to add additional OpenAI model lanes under current routing.
- Not safe to add a second provider by branching inside `call_gpt`; introduce the adapter seam first.

Minimum architectural action:

Write a backend adapter design note and extract the OpenAI behavior behind it before adding another provider.

What should not be redesigned:

- Do not move retry/fallback ownership out of `game.api`.
- Do not let backend adapters mutate game state.
- Do not entangle protected replay acceptance with backend provider logic.

Priority:

`P1 - Required before the affected feature class`.

## 6. Repository Handoff Compatibility

Final classification: `ARCHITECTURALLY ENABLED`.

Fact:

AR-AG found setup docs, `.env.example`, `run.py`, model config docs, persistence envelope docs, ownership ledgers, protected replay manifest, test/governance docs, and Campaign 1 architecture synthesis. AR-AF names itself the first-stop baseline and AR-AD names the target doctrine.

Architectural judgment:

The repository has enough runtime structure and authority documentation for handoff. The limitation is not inability to identify architectural ownership; it is that the current evidence is distributed across root AR reports, docs, audits, tools, artifacts, and historical notes.

Limitation type:

- Durable "start here" doc: documentation.
- Current architecture index: documentation/governance hygiene.
- Canonical-vs-historical artifact index: documentation/governance hygiene.
- Setup/test checklist: documentation/operational.
- Deployment assumptions and secrets guidance: operational/product decision.
- Data initialization/migration guidance: operational, with future local schema refinement.
- Generated artifact retention policy: documentation/governance.

Would implementation be safe before resolving it?

Yes for controlled local features. Handoff cleanup improves onboarding and review but does not block bounded implementation except where an external reviewer or new agent needs to operate independently.

Minimum architectural action:

No architecture change required. Create a durable handoff index under `docs/` that points to AR-AF/AR-AD, setup, tests, persistence, replay, and current canonical artifacts.

What should not be redesigned:

- Do not reorganize all historical audits before feature work.
- Do not treat documentation sprawl as evidence of architecture failure.
- Do not promote advisory artifacts into governance authority merely to simplify handoff.

Priority:

`P0 - Required before controlled feature expansion` only if another engineer/agent will take over immediately. Otherwise `P2 - Valuable during implementation`.

## 7. Low-Context Runtime Compatibility

Final classification: `ARCHITECTURALLY ENABLED`.

Fact:

AR-AG found explicit durable JSON state, versioned runtime envelopes, `compose_state`, CTIR, CTIR runtime stamps, prompt-context consumption rules, bounded world progression slices, snapshots, logs, replay projections, and context-window helpers. AR-AD doctrine makes runtime truth before narration and CTIR-as-meaning-boundary permanent principles. AR-AE found CTIR lifecycle fully aligned and prompt construction mostly aligned.

Architectural judgment:

Low-context runtime operation is architecturally enabled for local single-user play and campaign lengths where canonical state, bounded CTIR, logs, snapshots, and prompt-context adapters remain sufficient. The system does not rely on implicit model memory as the source of truth. Runtime decisions are grounded in persisted state and engine-owned resolution, with GPT constrained to expression.

Scale assumptions:

- Sufficient for near-term local campaigns and controlled long-session validation where canonical state remains compact enough for bounded projections.
- Very long campaigns, semantic search over history, or large asset/world corpora may require retrieval and context-budget instrumentation. That is scaling implementation unless product requirements demand semantic retrieval as a core authority surface.

Limitation type:

- Semantic retrieval: optional scaling refinement/product-dependent implementation.
- Token budgeting: implementation/observability.
- Long-campaign instrumentation: implementation/tooling.
- State reconstruction policy: mostly already architecturally supported; may need documentation.

Would implementation be safe before resolving it?

Yes. Most feature work can proceed. Features that add large memory surfaces should define bounded projections and budget instrumentation as part of implementation.

Minimum architectural action:

No prerequisite architecture action. For large context-heavy features, add feature-local bounded read models and budget telemetry.

What should not be redesigned:

- Do not replace CTIR with conversation history.
- Do not let prompt context reconstruct authoritative state when CTIR/domain contracts exist.
- Do not make replay projection a runtime memory source.

Priority:

`P2 - Valuable during implementation` for token/context observability. `P3` for semantic retrieval until scale demands it.

## 8. Feature Extensibility Compatibility

Final classification: `ARCHITECTURALLY ENABLED`.

Fact:

AR-AG found stable layer doctrine, domain owners, state authority, engine schemas, CTIR, final-emission owner modules, UI modes, replay/provenance guardrails, and evidence from feature-readiness pilots. AR-AF says future work should assume the current baseline and avoid reopening stable ownership without contradictory evidence.

Architectural judgment:

Controlled feature expansion is compatible with the architecture. The coordination surfaces are real, but they are not blockers:

- `game.api` is intentionally broad because it owns transaction order.
- Final emission is a governed transitional boundary, not chaos.
- Fallback/provenance fields are complex because trust evidence needs multi-axis ownership.
- Replay protection is a guardrail, not a reason to stop features.
- State schemas can evolve locally if bounded and documented.

Feature class paths:

| Feature Class | Likely Architectural Path | Expected Touchpoints | Dependency Judgment |
|---|---|---|---|
| New rules subsystem | Add domain owner/contract, state-domain seam if needed, CTIR bounded slice, tests | Domain module, `game.models`, CTIR, prompt context, replay/provenance if emitted | Recommended before: local subsystem contract |
| Economy/investigation/research | Same pattern as non-combat/world progression: domain contract + bounded projection | Domain module, state authority, CTIR/prompt, UI state | Can proceed with feature-local contract |
| Map support | Treat as state projection/tooling surface first; avoid making map UI authoritative truth | Storage/read model, UI projection, maybe scene graph | Can proceed; no global architecture prerequisite |
| Portrait/media | Asset/reference projection; avoid model prose as asset truth | UI/static/assets, state projection, provenance if generated | Can proceed; media policy needed if generated |
| New output format | Add final-emission or response-payload format facade without changing domain truth | API response, final emission, UI | Can proceed if final text invariants preserved |
| Author/debug tool | Use UI modes/state channels/debug projection | `game.ui_mode_policy`, `game.state_channels`, API endpoints | Can proceed for local tools |
| New state projection | Add read model/projection; do not create parallel truth store | Domain owner, projection module, tests | Can proceed with ownership note |
| New model backend | Add backend adapter boundary first | `game.gm`, routing, preflight, provenance | Required before implementation |
| Player-facing explainability | Add player-safe explanation schema over existing provenance | FEM, lineage, state authority, UI channel | Recommended before UI implementation |

Limitation type:

- Missing feature implementations: implementation.
- Feature-specific contracts: local architectural refinement.
- Generic plugin system: not currently justified.

Would implementation be safe before resolving it?

Safe for bounded features that follow existing domain/CTIR/projection/final-emission patterns. Not safe for broad alternate ruleset, second AI backend, external public API, or player-facing challenge workflows without their local seams.

Minimum architectural action:

Use feature-specific decision records for high-impact features. Do not introduce a generic plugin system until repeated feature work proves common packaging needs.

What should not be redesigned:

- Do not split `game.api` transaction authority merely to make feature work feel modular.
- Do not move domain truth into final emission, prompt context, or UI.
- Do not relax protected replay separation.

Priority:

`P0` for a short feature-boundary checklist before broad feature expansion. Most individual features are `P1` only for their affected class.

## 9. UI and Tooling Compatibility

Final classification: `ENABLED WITH LOCAL REFINEMENT`.

Fact:

AR-AG found FastAPI endpoints, static browser UI, `GET /api/state?ui_mode=...`, fail-closed UI modes, state-channel projections, snapshots, logs, and debug lanes. `docs/objective15_ui_mode_separation.md` declares the frontend render source and mode boundaries.

Architectural judgment:

The architecture is ready for the existing local browser UI, improved local UI, and author/debug tooling. It is not yet ready to promise stable external integrations or hosted/multi-user operation without local refinements.

Scope distinctions:

- Existing local browser UI: architecturally enabled now.
- Improved local UI: architecturally enabled; use current state projection and endpoints.
- Author/debug tooling: architecturally enabled for local/operator tools through `author`/`debug` modes.
- External integrations: require a versioned public command/query facade and error model first.
- Hosted or multi-user operation: requires security/session/tenancy/deployment architecture later; outside immediate campaign scope.

Limitation type:

- Versioned public API: local architectural refinement for external tooling.
- Command/query facade: local architectural refinement.
- Event stream/streaming: useful implementation/refinement, required only for real-time external UI or streaming model output.
- Security model: future architecture concern for hosted/multi-user deployment.
- Multi-campaign/resource boundaries: future architecture concern if hosted/multi-user becomes immediate.

Would implementation be safe before resolving it?

- Safe for local UI improvements and local debug/author tools.
- Not safe to expose a stable third-party API or hosted multi-user surface before public API/security/resource boundaries are specified.

Minimum architectural action:

Before external tooling, define a versioned public application boundary: state query schema, command schema, error model, idempotency expectations, and provenance/debug visibility levels.

What should not be redesigned:

- Do not abandon `GET /api/state?ui_mode=...` as the local render source.
- Do not merge author/debug/player channels.
- Do not make UI state a second persistence root.

Priority:

`P1 - Required before the affected feature class` for external/hosted tooling. `P2` for local UI improvements.

## 10. Player Trust and Explainability Compatibility

Final classification: `ARCHITECTURALLY ENABLED`.

Fact:

AR-AG found state authority, CTIR meaning, realization authority, FEM, runtime lineage, protected replay, mutation traces, visibility separation, fallback attribution, model-route metadata, logs, and snapshots. AR-AD doctrine states provenance explains behavior without owning behavior, and replay dependency flows one way from runtime output to evidence.

Architectural judgment:

The architecture already supports trustworthy and inspectable operation internally and for operators. Player-facing explanations and challenges are product/UI/schema work on top of existing provenance, not a reason to change the core architecture.

Trust layers:

- Internal architectural explainability: enabled. State authority, CTIR, domain owners, final emission metadata, and replay boundaries explain the pipeline.
- Operator diagnostics: enabled. FEM, runtime lineage, debug traces, logs, snapshots, and protected replay provide rich inspection surfaces.
- Player-facing explanations: enabled but not implemented. Need a redacted schema that translates mechanical/provenance facts into safe player language.
- Player challenge/correction workflows: product-dependent. A simple explanation/challenge annotation can be local; reversible replay branching or adjudication rollback is later product design.

Provenance/version bundle:

A consolidated provenance/version bundle should be introduced locally before player-facing explanation UX or ruleset/backend expansion becomes broad. It should include, as applicable:

- runtime/app version or schema version,
- ruleset identity/version,
- backend/provider/model identity,
- prompt/policy/response contract versions,
- CTIR version,
- final-emission/provenance schema version,
- tool/capability flags used.

Limitation type:

- Missing player-facing UX: implementation/product design.
- Hidden-info redaction policy: product decision plus local schema refinement.
- Missing ruleset/backend version identity: local architectural refinement.
- Challenge workflow: product decision; simple version local, replay-branching later.

Would implementation be safe before resolving it?

- Safe to improve operator diagnostics.
- For player-facing explanations, define redaction/schema first.
- For formal challenge/reversal workflows, wait for product decision.

Minimum architectural action:

Define a player-safe explanation schema and provenance/version bundle. Do not change core runtime ownership.

What should not be redesigned:

- Do not expose raw debug/provenance wholesale to players.
- Do not let challenge workflows mutate hidden/world truth without domain owners.
- Do not collapse runtime diagnostic projection and protected replay acceptance.

Priority:

`P1 - Required before player-facing explanation UI`; provenance bundle is also `P1` before broad ruleset/backend work.

## 11. Cross-Cutting Gap Assessment

| Gap | Objectives Affected | Truly Architectural? | Local or Cross-Cutting | Blocks Implementation? | Minimum Resolution | Recommended Timing | Risk Too Early | Risk Delayed |
|---|---|---|---|---|---|---|---|---|
| Ruleset identity and packaging | Rulesets, feature extensibility, provenance, handoff | Yes, but bounded | Cross-cutting with local seam | Blocks alternate ruleset, not same-ruleset features | Ruleset decision record, identity/version field, registry/adapter sketch | P1 before alternate ruleset | Overbuilding generic plugins | PF1e assumptions spread into new systems |
| Provider-neutral backend boundary | AI backends, provenance, tests, UI | Yes, bounded adapter | Cross-cutting | Blocks additional provider/local inference | Backend protocol, OpenAI adapter, fake backend, provenance identity | P1 before second provider | Designing for every provider/tool too soon | Provider branching hardens in `call_gpt` |
| Versioning and migration strategy | Rulesets, backends, UI APIs, persistence, replay | Partly architectural | Cross-cutting | Does not block small local features; blocks broad schemas/external APIs | Version bundle and migration note for changed persisted/public schemas | P2 now, P1 before public API/rulesets | Bureaucratic schema process | Saved campaigns/provenance become ambiguous |
| Public application boundary | UI/tooling, external integrations, handoff | Yes for external use | Local facade with cross-cutting visibility | Blocks external tooling/hosted API | Versioned query/command/error/idempotency facade | P1 before external tooling | Freezing internal API too early | Third-party/internal UI couples to raw dicts |
| Evidence canonicality and handoff index | Handoff, governance, feature work | Documentation/governance | Cross-cutting operational | Does not block bounded implementation; helps expansion | Durable `docs/` start-here + canonical/advisory index | P0 if handoff imminent; otherwise P2 | Spending cycles cataloging everything | New contributors rediscover/contradict authority |
| Capability negotiation | Backends, rulesets, tools, UI | Product-dependent architecture | Cross-cutting | Blocks advanced provider/tools; not first adapter | Minimal capability flags in ruleset/backend/version bundle | P2; P1 for tool/streaming features | Abstracting unused capabilities | Hidden assumptions in adapters/features |
| Player-safe explanation/challenge workflow | Trust, UI, rulesets/backends | Local schema/product design | Cross-cutting | Blocks player-facing explanation/challenge UI | Redacted explanation schema, operator/player visibility split | P1 before explanation UI | Designing full dispute court too soon | Raw debug leaks or explanations mislead players |

Evolution threshold result:

Each gap can be addressed by bounded interfaces, adapters, registries, facades, schema fields, or documents while preserving current state authority, transaction flow, runtime behavior, replay/provenance boundaries, and incremental delivery. Therefore none requires `REQUIRES ARCHITECTURAL EVOLUTION`.

## 12. Architecture vs. Implementation Findings

| Finding | Category | Assessment |
|---|---|---|
| Alternate ruleset absent | Implementation | Does not prevent compatibility. First alternate ruleset needs local ruleset seam. |
| Ruleset registry/version absent | Local architectural refinement | Required before alternate ruleset implementation. |
| Direct OpenAI client in model call/preflight | Local architectural refinement | Backend adapter extraction, not redesign. |
| No local inference provider | Implementation | Add after backend boundary exists. |
| AR reports not folded into durable docs | Documentation | Handoff issue, not architecture failure. |
| No concise artifact canonicality index | Documentation/governance | Useful before handoff/broad expansion. |
| No public versioned API | Local architectural refinement | Needed for external tools/hosted UI, not local UI. |
| No event stream | Implementation/product decision | Not required until streaming/real-time UI scope. |
| No player explanation UX | Product decision + implementation | Existing provenance supports it. |
| No challenge/reversal workflow | Product decision | Simple challenge can be local; replay branching later. |
| Final-emission semantic repair pressure | Known transitional architecture | Needs classification before simplification, not redesign. |
| Broad `game.api` | Intentional architecture | Keep transaction spine; add delegates only where ownership is clear. |

## 13. Prioritized Remaining Work

| Work Item | Priority | Work Type | Objectives Affected | Minimum Resolution | Blocks | Risk if Deferred |
|---|---|---|---|---|---|---|
| Feature-boundary checklist for controlled expansion | P0 - Required before controlled feature expansion | Documentation / governance | Feature extensibility, handoff, trust | One short checklist: owner, state domain, CTIR/projection, UI/API, replay/provenance, tests | Broad feature batches | Moderate |
| Ruleset decision record and minimal contract | P1 - Required before affected feature class | Product decision / local architectural refinement | Rulesets, provenance, extensibility | One-active-ruleset assumption, registry shape, identity/version, adapter responsibilities | Alternate ruleset | High |
| Provider-neutral backend adapter design | P1 - Required before affected feature class | Local architectural refinement | AI backends, provenance, testing | Backend protocol, OpenAI adapter plan, fake backend, error/provenance fields | Additional provider/local inference | High |
| Player-safe explanation schema | P1 - Required before affected feature class | Product decision / local schema refinement | Trust, UI/tooling | Redaction levels, player vs operator fields, mechanical outcome explanation shape | Player-facing explanation UI | High |
| Public command/query API facade | P1 - Required before affected feature class | Local architectural refinement | UI/tooling, handoff | Versioned query/command/error/idempotency boundary | External tooling, hosted API | High |
| Provenance/version bundle | P1 before broad ruleset/backend/explanation work; P2 otherwise | Local architectural refinement | Rulesets, backends, trust, replay | Consolidated ruleset/backend/model/prompt/runtime/schema identity | Broad provenance-dependent features | Moderate |
| Durable handoff/start-here index | P0 if handoff imminent; P2 otherwise | Documentation / operational | Handoff, feature extensibility | `docs/` page pointing to current architecture, setup, tests, replay, artifacts | External review/onboarding | Moderate |
| Evidence canonicality/artifact retention index | P2 - Valuable during implementation | Documentation / governance | Handoff, trust, replay | Label canonical, generated, advisory, historical surfaces | Artifact cleanup and external review | Moderate |
| Context budget and long-campaign instrumentation | P2 | Implementation / observability | Low-context runtime | Budget telemetry and context-slice inspection | Very long campaigns | Moderate |
| Streaming/tool-calling/capability negotiation | P3 until provider/tool scope requires it | Product decision / implementation / local refinement | AI backends, UI/tooling | Capability flags and extension points after first backend seam | Streaming/tool features | Low now, high later |
| Hosted/multi-user security and tenancy model | P3 | Future architecture/product decision | UI/tooling, handoff | Auth/session/campaign-resource model | Hosted multi-user deployment | Low now, blocking later |

## 14. Implementation Dependency Map

Alternate ruleset implementation:

- Required before: ruleset decision record, ruleset identity/version, minimal registry/adapter contract.
- Recommended before: provenance/version bundle.
- Does not require: replacing `game.api`, changing CTIR authority, generic plugin framework.

Additional AI backend implementation:

- Required before: provider-neutral backend adapter boundary and deterministic fake backend.
- Recommended before: provenance/version bundle with provider/model/capability fields.
- Can defer: streaming, tool-calling, advanced capability negotiation unless the provider requires it.

UI expansion:

- Existing/improved local UI: can proceed using current FastAPI/state projection and UI modes.
- Author/debug local tools: can proceed with `ui_mode` and state-channel policy.
- Recommended before broad UI expansion: feature-boundary checklist for new state projections.

External tooling:

- Required before: versioned public command/query facade, error model, idempotency expectations, visibility levels.
- Can proceed in parallel: handoff index, artifact canonicality index.

Maps/media:

- Can proceed without global architecture work if treated as read models/assets/projections.
- Recommended before generated media: media provenance policy and visibility rules.
- Does not block: ruleset/backend adapter work.

Economy/investigation/research systems:

- Can proceed with feature-local domain contract, state authority mapping, CTIR/prompt bounded projection, and tests.
- Recommended before: feature-boundary checklist.
- Does not require: generic plugin framework.

Player-facing explanation UI:

- Required before: player-safe explanation schema and redaction policy.
- Recommended before: provenance/version bundle.
- Can reuse: state authority, CTIR, FEM, runtime lineage, logs, snapshots.

Hosted or multi-user deployment:

- Defer until needed.
- Required before implementation: security/auth model, session/campaign resource boundaries, persistence/deployment strategy, public API facade.
- Does not block: local single-user feature expansion.

## 15. Roadmap Recommendation

Recommendation: `CONTINUE WITH TARGETED PREREQUISITES`.

Why:

- The architecture is broadly compatible with the vision.
- No objective requires genuine architectural evolution.
- Several affected feature classes need small local seams before implementation: rulesets, multiple providers, external tooling, and player-facing explanation.
- Handoff/canonicality docs should improve onboarding and reduce rediscovery but need not block all local feature work.

What should occur next:

1. Produce a small Campaign 2 closeout/compatibility roadmap that commits these classifications and priorities.
2. Before implementing the first alternate ruleset, write the ruleset decision record and contract.
3. Before implementing another AI provider, write/extract the backend adapter boundary.
4. Before external tooling or hosted UI, define the public command/query facade.
5. Before player-facing explanation UI, define the redacted explanation schema and provenance/version bundle.

What should not block progress:

- Full hosted/multi-user architecture.
- Streaming/tool-calling support.
- Semantic retrieval.
- Generic plugin framework.
- Exhaustive cleanup of all historical audit artifacts.
- Broad refactor of `game.api`.

Large-scale feature expansion:

- Not recommended immediately across many high-impact surfaces at once.

Controlled feature expansion:

- Recommended, provided each feature class resolves its local prerequisite seam first and preserves Campaign 1 invariants.

## 16. Campaign Closeout Question Answers

1. Which parts of the long-term vision are already enabled by the current architecture?

   Clean repository handoff, low-context runtime operation, straightforward feature extensibility, and player trust/provenance/explainability are architecturally enabled. UI/tooling is enabled for local/browser/operator use. Ruleset and backend work are enabled once small local seams are introduced.

2. Which vision goals require only architectural refinement rather than redesign?

   Modular rulesets, multiple AI backends, and external/public UI/tooling require local refinement: ruleset contract, backend adapter, public API facade, provenance/version bundle, and player-safe explanation schema.

3. Which vision goals require genuine architectural evolution?

   None under the working assumptions. No objective requires reversing dependency direction, replacing the transaction spine, changing state authority, merging replay boundaries, or redesigning persistence.

4. What implementation priorities naturally emerge?

   Highest priority is not a feature implementation by itself; it is a small prerequisite set: feature-boundary checklist, ruleset decision record before alternate rulesets, backend adapter before new providers, explanation schema before player-facing explanations, and public API facade before external/hosted tooling.

5. Should the roadmap continue as planned, or should implementation priorities be reordered?

   Continue with targeted prerequisites. Do not return to broad Architecture Reconciliation. Reorder only if the next planned feature is an alternate ruleset, additional provider, external API, hosted UI, or player-facing explanation; those need their local seams first.

## 17. Recommended Next Cycle

Recommended next cycle: **AR-AI - Campaign 2 Closeout and Prerequisite Roadmap**.

Purpose:

- Close Campaign 2 by turning this assessment into a concise implementation-ordering roadmap.
- Select the first controlled feature expansion lane.
- Produce one prioritized prerequisite list tied to actual next work.

Why it is needed:

AR-AH answers the architectural compatibility question. One short closeout cycle would prevent the next implementation cycle from re-litigating vision compatibility or overbuilding abstractions. It should be a synthesis/decision artifact, not another discovery pass.

Required outputs:

- Campaign 2 closeout summary.
- Final classification table copied forward.
- First-feature recommendation.
- Prerequisite checklist for that feature class.
- Explicit non-goals: no runtime refactor, no plugin system, no backend/ruleset implementation yet unless a following implementation cycle scopes it.

Why it is not unnecessary architecture work:

It is the handoff from assessment to implementation ordering. It should be short and should end the campaign rather than extend architecture analysis indefinitely.

Alternative:

If the project owner already knows the next feature class, skip the closeout and move directly to that class's targeted prerequisite-design cycle.

## 18. Evidence and Confidence Notes

Evidence used:

- AR-AG provided the objective-by-objective evidence inventory and cross-cutting gaps.
- AR-AF established the current architectural baseline and invariants.
- AR-AD established target architecture doctrine, layer boundaries, multi-axis ownership, and canonicality.
- AR-AE confirmed implementation mostly conforms to AR-AD and identified transitional responsibilities as refinement inputs rather than foundational unknowns.

Confidence:

- High for AI backend, handoff, low-context runtime, UI/tooling, and trust/provenance classifications because AR-AG cites concrete files/symbols and AR-AE confirms doctrine alignment.
- Medium-High for ruleset support because AR-AG found strong domain boundaries but no second ruleset or ruleset contract.
- Medium-High for feature extensibility because evidence supports controlled expansion, while broad multi-surface features still need local decision records.

Contradictory evidence:

- None found that materially contradicts Campaign 1 doctrine.

Insufficient evidence:

- Product requirements remain incomplete for simultaneous multi-ruleset execution, hosted multi-user deployment, streaming/tool-calling urgency, and formal player dispute/replay-branching workflows. Under the working assumptions, these do not block final architectural classification.

Validation:

- No tests were run.
- No runtime behavior was changed.
- This report is assessment-only and should be reviewed against AR-AG before implementation planning.
