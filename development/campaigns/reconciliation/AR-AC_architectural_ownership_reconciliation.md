# AR-AC Architectural Ownership Reconciliation

Date: 2026-07-01  
Scope: documentation-only architectural reconciliation for Architecture Reconciliation cycle 3  
Inputs: `AR-AA_architectural_mapping_discovery.md`, `AR-AB_runtime_authority_and_replay_boundary_map.md`  
Non-goal: runtime refactor, behavior change, schema promotion, replay policy change

## Executive Summary

The current architecture should be treated as stable, governed, and intentionally evidence-rich, not broken. The main reconciliation outcome is that several broad ownership boundaries should become permanent architecture, while their internal coordination costs should be documented as future simplification targets.

The permanent architecture is:

- `game.api` owns the single-turn runtime transaction: request entry, authoritative mutation orchestration, CTIR lifecycle placement, GPT/retry orchestration, final-emission handoff, persistence, logging, and response construction.
- Domain modules own domain truth and simulation. `game.state_authority` owns the declarative registry and guard vocabulary, not the state itself.
- CTIR owns resolved-turn meaning for narration once per turn. Prompt construction consumes CTIR and other approved read models; it does not re-decide authoritative semantics when CTIR exists.
- Final emission owns legality, last-mile orchestration, and packaging. Its remaining semantic repair pressure is transitional.
- Runtime diagnostic projection and protected replay projection are intentionally separate. Protected replay may consume runtime diagnostics, but runtime must not depend on protected replay acceptance structures.
- Provenance and replay evidence are first-class architecture, but some generated/advisory artifact fanout should be simplified by clearer canonicality labels.

The most important reconciliation rule is that ownership is multi-axis. For fallback, opening realization, final emission, and replay, a single owner field is misleading. The permanent vocabulary should distinguish runtime owner, content author, selector/applicator, provenance packager, runtime diagnostic projection owner, and protected replay acceptance owner.

Recommended AR-AD focus: define a compact target architecture doctrine and canonicality map for runtime spine, final emission, fallback/provenance fields, and replay/evidence surfaces. AR-AD should not begin by moving code; it should first specify which transitional responsibilities are allowed to remain, which are upstream-movable, and which documentation/evidence surfaces are canonical.

## Ownership Reconciliation Matrix

| Subsystem | Current owner | Intended long-term owner | Current implementation quality | Boundary classification | Architectural justification | Recommendation |
|---|---|---|---|---|---|---|
| Runtime orchestration | `game.api` | `game.api` as transaction spine, supported by narrow delegates | Stable but broad | Permanent with consolidation candidates | A turn is an atomic transaction crossing state, CTIR, narration, final emission, persistence, and logging. Central orchestration is coherent. | Preserve API as runtime owner. Future simplification should clarify delegate seams for preflight, trace/log assembly, and persistence tail without splitting transaction authority. |
| State authority | `game.state_authority` registry plus domain mutators in storage/world/interaction/API/etc. | Same split: registry/guards in `game.state_authority`, real mutation in domain owners | Stable, declarative | Permanent | State authority is a governance model, not a persistence or simulation engine. Domain modules must remain semantic owners of their state. | Keep as permanent architecture. Document that partial guard adoption is drift-watch, not evidence of competing ownership. |
| CTIR lifecycle | `game.ctir`, `game.ctir_runtime`, lifecycle placement in `game.api` | Same | Stable and well documented | Permanent | CTIR is canonical resolved-turn meaning for narration, built after authoritative mutation and reused through retries. | Preserve lifecycle. Treat CTIR absence fallbacks in prompt construction as compatibility residue. |
| Prompt construction | `game.prompt_context`, `game.narration_plan_bundle`, response policy/read-model helpers | `game.prompt_context` as adapter/packager over CTIR and approved read models | Stable with compatibility residue | Permanent with retirement candidates | Prompt construction should translate authoritative state into model context, not own turn truth. | Keep prompt ownership narrow. Future docs should mark CTIR-absent semantic fallback paths as compatibility-only where applicable. |
| GPT execution | `game.gm`, model routing modules, upstream preflight helpers | `game.gm` and model routing modules for call/guard/route mechanics | Stable | Permanent | Model call mechanics are separate from runtime retry/fallback policy. | Preserve split: GPT layer calls and normalizes; API orchestrates retry and fallback. |
| Retry/fallback | API retry loop, `game.gm_retry`, `game.fallback_behavior`, diegetic/opening/social fallback modules, provenance helpers | Multi-axis ownership: API selects runtime strategy; fallback-family modules author content; provenance helpers package evidence; final emission records/applies final text | Stable but high-pressure | Transitional with extraction/consolidation candidates | Fallback is both runtime safety and evidence-bearing behavior. A single owner would hide important distinctions. | Preserve split-owner vocabulary. Simplify by documenting field consumers and canonical precedence, not by collapsing runtime fields. |
| Opening realization | `game.api`, `game.narrative_planning`, `game.opening_scene_realization`, `game.opening_visible_fact_selection`, `game.opening_deterministic_fallback`, final emission | Same split | Stable but boundary-sensitive | Permanent with transitional pressure | Opening crosses bootstrap state, public scene facts, planning obligations, GPT prose, deterministic fallback, final text invariants, and replay evidence. | Keep split. Add/maintain an opening handoff checklist so helper modules are not mistaken for structural opening authorities. |
| Final emission | `game.final_emission_runtime`, `game.final_emission_gate`, `game.final_emission_finalize`, `game.final_emission_meta`, repairs/sanitizer | Final emission gate/runtime/finalize/meta for legality, orchestration, packaging, and sealed terminal exceptions | Governed but transitional | Transitional | Doctrine says final emission should converge toward legality and packaging; current repairs still carry semantic pressure. | Do not move code in AR-AC. Classify remaining repairs in AR-AD as essential guardrail, sealed exception, or upstream-movable. |
| Replay projection | Runtime: `game.final_emission_replay_projection`; protected: test helpers and protected manifest | Same split | Stable | Permanent | Runtime diagnostic lineage and protected acceptance projection answer different questions and must remain one-way. | Keep boundary explicit. Consolidation, if any, should be facade/read-helper only and must not import test acceptance schema into runtime. |
| Protected replay | `tests.helpers.golden_replay_projection`, protected fields, registry, manifest, governance tests/docs | Same | Stable | Permanent | Protected replay is acceptance authority for replay observations, not runtime behavior. | Preserve as test/governance layer. Label protected fields as acceptance schema, not runtime schema. |
| Provenance | `game.realization_authority`, `game.realization_provenance`, `game.fallback_provenance_debug`, final-emission metadata, replay projection readers | Same, with clearer source/selector/content/packager vocabulary | Stable but evidence-heavy | Permanent with consolidation candidates | Provenance is essential to explain fallback and final-emission outcomes, especially under replay. | Keep provenance first-class. Simplify duplicate terminology and document which fields are write-time truth vs read-side projection. |
| Persistence | `game.storage`, API persistence tail, runtime envelope docs | `game.storage` for mechanics; API tail for transaction timing and response/log invariants | Stable | Permanent | Persistence mechanics and transaction timing are distinct; API must decide when a turn is complete enough to save/log. | Preserve split. Future documentation can clarify persistence-tail invariants without moving state write mechanics. |
| Logging | `game.storage.append_log` called by API tail | API owns log content timing; storage owns append/load mechanics | Stable | Permanent with consolidation candidates | Logs are part of the runtime transaction and replay input surface, but file mechanics belong in storage. | Keep current split. Consider documenting canonical log-entry assembly ownership in AR-AD. |

## Architectural Layer Model

### Request/API Layer

Primary modules:

- `game.api`
- Request/response models and API-facing preflight helpers

Primary responsibilities:

- Accept player/API requests.
- Enforce start/chat/action entry conditions.
- Own the runtime transaction boundary and response payload construction.

Allowed dependencies:

- Runtime orchestration helpers, domain simulation modules, storage, CTIR runtime, prompt/GPT layer, final emission delegate, logging helpers.

Forbidden dependencies:

- Protected replay acceptance helpers.
- Governance-only docs/tests as runtime inputs.
- Advisory report generators.

Canonical ownership:

- `game.api` owns API-visible turn orchestration and final response invariants.

### Runtime Orchestration Layer

Primary modules:

- `game.api`
- `game.ctir_runtime`
- Runtime turn-packet/stage telemetry helpers where used by the turn pipeline

Primary responsibilities:

- Coordinate the resolved-turn lifecycle: detach stale CTIR, mutate authoritative state, attach CTIR, build narration context, invoke GPT/retry, finalize, persist, log.

Allowed dependencies:

- Domain simulation, CTIR construction, prompt/GPT, final emission, storage, provenance packagers.

Forbidden dependencies:

- Protected replay acceptance schemas.
- Offline governance decision registries as runtime policy engines.

Canonical ownership:

- API remains the canonical transaction spine; helper modules own local lifecycle or telemetry contracts.

### Domain Simulation Layer

Primary modules:

- `game.noncombat_resolution`
- `game.exploration`
- `game.social`
- `game.combat`
- `game.world_progression`
- `game.interaction_context`
- `game.scene_actions`
- `game.skill_checks`
- Domain-specific state helpers

Primary responsibilities:

- Resolve player intent into authoritative outcomes and state mutations.
- Own domain truth before narration.

Allowed dependencies:

- Storage read models, state authority guards, world/scene/session data structures, domain contracts.

Forbidden dependencies:

- GPT narration as truth.
- Final emission as a source of authoritative simulation.
- Protected replay acceptance as a runtime decision source.

Canonical ownership:

- Domain modules own semantic game outcomes; `game.state_authority` governs domain boundaries.

### Narrative Layer

Primary modules:

- `game.ctir`
- `game.prompt_context`
- `game.narration_plan_bundle`
- `game.narrative_planning`
- `game.opening_scene_realization`
- `game.opening_visible_fact_selection`
- `game.gm`
- `game.model_routing`

Primary responsibilities:

- Convert authoritative turn meaning and read models into promptable narrative context.
- Call/guard GPT and preserve model route metadata.
- Curate opening basis facts and narration obligations without becoming state authority.

Allowed dependencies:

- CTIR, domain read models, response policy contracts, visibility/publication read models, model routing.

Forbidden dependencies:

- Mutating authoritative simulation after the domain layer except through declared runtime seams.
- Reconstructing CTIR-owned semantics when CTIR exists.
- Final emission metadata as prompt truth.

Canonical ownership:

- CTIR owns resolved-turn meaning; prompt context owns narration payload assembly; GPT layer owns model I/O.

### Emission Layer

Primary modules:

- `game.final_emission_runtime`
- `game.final_emission_gate`
- `game.final_emission_finalize`
- `game.final_emission_meta`
- `game.final_emission_repairs`
- `game.final_emission_validators`
- `game.output_sanitizer`
- `game.social_exchange_emission`
- Upstream prepared emission/fallback modules where consumed

Primary responsibilities:

- Select, legalize, sanitize, package, and record final player-facing text.
- Preserve final text/log/response invariants.
- Stamp final-emission metadata and mutation/provenance lineage.

Allowed dependencies:

- Candidate GM output, response contracts, sanitizer traces, provenance helpers, strict-social emission owner, runtime turn packet/telemetry.

Forbidden dependencies:

- Owning new semantic domain outcomes.
- Treating replay projection as runtime selection policy.
- Rewriting protected replay fields directly.

Canonical ownership:

- Final emission owns last-mile legality and packaging. Remaining semantic repair is transitional unless explicitly classified as sealed terminal exception.

### Persistence Layer

Primary modules:

- `game.storage`
- `game.campaign_state`
- `game.session`
- `game.campaign_reset`

Primary responsibilities:

- Load/save runtime documents, envelopes, snapshots, scene runtime overlays, and logs.
- Create/reset fresh runtime document shapes.

Allowed dependencies:

- Filesystem/runtime data envelopes, schema/default factories, transaction callers.

Forbidden dependencies:

- GPT/model behavior.
- Protected replay acceptance decisions.
- Final emission semantic repair policy.

Canonical ownership:

- `game.storage` owns persistence mechanics; API owns when transaction state is saved and logged.

### Replay/Evidence Layer

Primary modules:

- `game.final_emission_replay_projection`
- `tests.helpers.golden_replay`
- `tests.helpers.golden_replay_projection`
- `tests.helpers.golden_replay_projection_fields`
- `tests.helpers.protected_replay_registry`
- `tests.helpers.golden_replay_trend`
- Evidence aggregation tools

Primary responsibilities:

- Project finalized runtime surfaces into diagnostic lineage, protected observation rows, drift reports, and advisory evidence.

Allowed dependencies:

- Finalized runtime payloads, logs, snapshots, FEM/provenance metadata, runtime diagnostic projection.

Forbidden dependencies:

- Runtime importing protected replay acceptance fields.
- Evidence tooling owning runtime behavior.
- Advisory reports redefining canonical governance policy.

Canonical ownership:

- Runtime diagnostic projection belongs to runtime code; protected acceptance belongs to test helpers/manifest; advisory tools remain report-only.

### Governance Layer

Primary modules/docs:

- `docs/architecture_ownership_ledger.md`
- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- Replay governance tests
- Ownership guard tests and audit tools

Primary responsibilities:

- Declare target ownership, allowed dependency directions, protected replay policy, and guardrail checks.

Allowed dependencies:

- Static source inspection, test helpers, generated inventories, documented runtime owner declarations.

Forbidden dependencies:

- Becoming a hidden runtime policy engine.
- Treating target-state ledgers as proof that implementation is already clean.

Canonical ownership:

- Governance defines doctrine and drift checks; it does not execute gameplay.

## Architectural Dependency Review

### Appropriate Dependencies

| Dependency | Assessment |
|---|---|
| `game.api` -> storage/domain/CTIR/prompt/GPT/final emission | Appropriate. API is the transaction spine and must coordinate these layers. |
| `game.prompt_context` -> CTIR/read models/response policy contracts | Appropriate. Prompt context adapts authoritative meaning into model context. |
| Final emission -> validators/repairs/sanitizer/meta/provenance helpers | Appropriate with transitional caveat. This is the last-mile legality and packaging boundary. |
| Protected replay projection -> finalized payloads/FEM/runtime diagnostics | Appropriate. Protected replay may consume runtime diagnostics read-only. |
| Governance docs/tests -> runtime modules via static checks | Appropriate. Governance should observe and enforce boundaries without participating in runtime. |

### Transitional Dependencies

| Dependency | Assessment |
|---|---|
| Final emission -> semantic repair/fallback behavior | Transitional. Some paths are still needed as guardrails, but target doctrine is legality and packaging. |
| Prompt context -> non-CTIR semantic fallback sources | Transitional compatibility. Acceptable when CTIR is absent, but not a second semantic authority. |
| Opening fallback fields across API, upstream repairs, final emission, and replay | Transitional pressure around a permanent multi-step opening flow. |
| Dual fallback-family projection into one replay field | Transitional read-side compatibility, not a runtime target. |

### Potentially Circular Dependencies

| Relationship | Risk |
|---|---|
| Final emission metadata -> replay projection -> protected replay interpretation -> future final emission expectations | Conceptual loop risk. Runtime must not shape behavior to satisfy projected acceptance fields without explicit governance review. |
| Ownership ledger target state -> tests -> runtime changes -> ledger proof claims | Documentation loop risk. Ledgers are targets, not proof of conformance. |
| Opening realization -> prompt obligations -> final emission selection -> opening debug copied back into metadata | Boundary confusion risk. The data path is valid, but ownership language must stay precise. |

### Too Broad Dependencies

| Dependency | Assessment |
|---|---|
| `game.api` dependence on many helper concerns | Broad but mostly architectural. It is acceptable as orchestration, but local readability suffers. |
| Replay/evidence tools reading many provenance/fallback fields | Broad because evidence must correlate multiple surfaces. Needs canonicality labels more than code movement. |
| Final emission projection reading ownership/meta/provenance facades | Broad but read-only. Watch for magnet growth. |

### Too Tightly Coupled Dependencies

| Dependency | Assessment |
|---|---|
| Final emission gate/finalize/repairs/meta | Tight but expected for last-mile output. Coupling becomes problematic only when semantic content authorship hides there. |
| Opening start-campaign path and final text/log/payload invariants | Tight by necessity because campaign start is both bootstrap and first emitted turn. |
| Fallback selector/provenance/final recorder fields | Tight because evidence must explain safety behavior. Simplify terminology before considering implementation moves. |

## Permanent vs Transitional Architecture

| AR-AB tension | Decision | Rationale |
|---|---|---|
| `game.api` breadth | Permanent architecture with future simplification target | A turn transaction needs a single runtime spine. The simplification target is delegate clarity, not splitting authority. |
| Final emission semantic pressure | Transitional architecture | Current behavior is tested and governed, but target doctrine is legality plus packaging, with semantic synthesis upstream. |
| Opening-scene ownership split | Permanent architecture with transitional pressure | Opening inherently crosses bootstrap, planning, GPT, fallback, gate, persistence, and replay. The split is correct; the handoff needs sharper documentation. |
| Fallback ownership fanout | Permanent multi-axis model with transitional field complexity | Content author, selector, applicator, packager, recorder, and observer are genuinely different roles. Field duplication/consumer interpretation is the simplification target. |
| Runtime vs replay separation | Permanent architecture | Diagnostic projection and protected acceptance projection must remain separate with one-way dependency. |
| Evidence artifact fanout | Future simplification target | Evidence is valuable, but canonical/generated/advisory surfaces need clearer labels to reduce maintenance drag. |
| Dual fallback-family vocabulary | Transitional architecture | Runtime fields and replay compatibility projection should remain until consumer precedence and migration value are explicitly reviewed. |
| Protected replay consuming runtime lineage diagnostics | Permanent architecture if one-way | This is useful and safe only while runtime remains independent of protected acceptance schema. |
| Final emission replay projection import fanout | Candidate for consolidation | Read-side helper/facade consolidation may improve clarity if it does not move acceptance logic into runtime. |
| Opening fallback owner buckets in protected fields | Transitional architecture | Protected replay observes compatibility fields while runtime carries multiple opening fallback ownership axes. |

## Candidate Simplification Opportunities

These are architectural clarity opportunities only. They are not implementation instructions.

1. Publish a compact target-architecture doctrine.

   A short document could define the permanent layer model, multi-axis ownership vocabulary, and dependency direction rules. This would reduce the need to infer target architecture from many cycle reports.

2. Add canonicality labels to evidence surfaces.

   Replay/evidence docs and artifacts should be labeled as one of: runtime diagnostic, protected acceptance, governance contract, generated report, or advisory audit. This would reduce accidental promotion of advisory data into policy.

3. Create a fallback field consumer map.

   The project would benefit from one authoritative read-side map for `fallback_family_used`, `realization_fallback_family`, selector/content/owner fields, provenance traces, and protected projection precedence.

4. Create an opening handoff checklist.

   A concise checklist should state: API bootstraps the opening turn; narrative planning owns structural opening obligations; opening realization owns public diegetic basis; fallback modules author deterministic backup; final emission selects/packages; API persists/logs; replay observes.

5. Separate final-emission repair categories in documentation.

   AR-AD should classify final-emission repairs into legality-only, packaging-only, sealed terminal exception, and upstream-movable semantic repair. This improves architecture without demanding immediate code movement.

6. Clarify log-entry assembly ownership.

   Persistence mechanics are clear, but log content/timing is part of the API transaction. A short ownership note would help distinguish storage append mechanics from runtime log semantics.

7. Keep `game.api` broad, but document delegate seams.

   The API spine should remain canonical. Future simplification should focus on named delegate responsibilities rather than reducing file size for its own sake.

8. Prefer facade/read-helper consolidation over owner migration.

   Where replay/evidence reads many final-emission/provenance fields, clarity may improve through read helpers. This should not collapse protected replay acceptance into runtime projection.

## Recommended Focus for AR-AD

AR-AD should be a target-architecture doctrine and canonicality pass.

Recommended AR-AD outputs:

1. A concise permanent layer doctrine for request/API, runtime orchestration, domain simulation, narrative, emission, persistence, replay/evidence, and governance.
2. A multi-axis ownership vocabulary for fallback, opening, final emission, provenance, and replay.
3. A final-emission repair classification table: legality-only, packaging-only, sealed exception, upstream-movable.
4. A fallback/provenance field consumer map with write-time truth vs read-side projection labels.
5. A replay/evidence canonicality index labeling each major artifact as protected acceptance, runtime diagnostic, governance contract, generated report, or advisory audit.

AR-AD should continue to avoid runtime refactors unless the doctrine identifies a concrete ownership ambiguity that cannot be resolved by documentation or tests.

## Validation Notes

No runtime files were intentionally modified. This cycle produced this documentation artifact only.

Suggested validation:

- Run `git status --short`.
- Confirm only `AR-AC_architectural_ownership_reconciliation.md` was added by this cycle, aside from pre-existing untracked AR-AA/AR-AB/foundation discovery artifacts.
