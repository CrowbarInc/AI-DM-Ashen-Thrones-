# AR-AD Target Architecture Doctrine

Date: 2026-07-14  
Scope: documentation-only target architecture doctrine for Architecture Reconciliation cycle 4  
Inputs: `AR-AA_architectural_mapping_discovery.md`, `AR-AB_runtime_authority_and_replay_boundary_map.md`, `AR-AC_architectural_ownership_reconciliation.md`  
Non-goal: runtime refactor, behavior change, schema promotion, replay policy change

## Executive Summary

The target architecture is a single-turn runtime transaction surrounded by clear domain owners, bounded narration adapters, final-emission legality/packaging, durable persistence, and one-way replay/evidence projection.

The architecture is not organized around a single file becoming small. It is organized around ownership clarity:

- Runtime truth is established before narration.
- `game.api` remains the single transaction spine for a turn.
- Domain modules own simulation truth.
- CTIR owns resolved-turn meaning for narration.
- Prompt construction adapts approved state and CTIR into model context.
- GPT authors candidate prose, not authoritative state.
- Final emission owns final legality, selection, packaging, metadata, and sealed terminal exceptions.
- Persistence stores runtime documents and logs; it does not decide runtime semantics.
- Runtime diagnostic projection and protected replay acceptance remain separate, with one-way dependency from runtime outputs toward replay/evidence.
- Governance declares target ownership and drift checks; it must not become hidden runtime behavior.

The system intentionally uses multi-axis ownership where one observable outcome has several legitimate owners. Fallback, opening narration, final emission, provenance, and replay cannot be described by one owner field without losing important architecture. The durable vocabulary is: runtime owner, domain owner, content author, selector, applicator, provenance packager, runtime diagnostic owner, and protected replay owner.

The main transitional areas are final-emission semantic repair pressure, fallback/provenance field complexity, opening fallback compatibility fields, CTIR-absent prompt compatibility, evidence artifact fanout, and broad but necessary API coordination. These are not immediate refactor mandates. They are evolution registers: future simplification should occur only when it improves architectural understanding, preserves behavior, and maintains replay evidence.

## Target Architecture Doctrine

### Permanent Architectural Principles

1. Runtime truth comes before narration.

   Player input is normalized and resolved into authoritative domain outcomes before GPT prose is requested. GPT narration expresses runtime truth; it does not create it.

2. A turn has one transaction spine.

   `game.api` owns the end-to-end runtime transaction for start, chat, and action flows: request entry, state loading, eligibility, authoritative mutation orchestration, CTIR lifecycle placement, GPT/retry orchestration, final-emission handoff, persistence, logging, traces, and response construction.

3. Domain truth remains with domain owners.

   Domain modules own simulation state and outcomes. `game.state_authority` declares domains and guard vocabulary, but does not become a persistence engine or universal mutator.

4. CTIR is the narration meaning boundary.

   CTIR is the bounded, retry-stable resolved-turn meaning object for narration. Prompt construction consumes CTIR when present and must not re-decide CTIR-owned semantics.

5. Prompt construction is an adapter layer.

   Prompt modules package CTIR, visibility, response contracts, narrative plans, and read models into GPT context. They do not own authoritative game outcomes.

6. GPT owns expression, not truth.

   Model routing and GPT call/guard modules own model I/O, route metadata, and output normalization. Runtime retry/fallback decisions remain with the runtime transaction spine.

7. Final emission is the last-mile legality and packaging boundary.

   Final emission selects, sanitizes, legalizes, packages, and records final player-facing text. Semantic synthesis at this boundary is transitional unless explicitly treated as a sealed terminal exception.

8. Replay dependency is one-way.

   Runtime emits finalized payloads, logs, snapshots, FEM, trace, and provenance. Runtime diagnostic projection may read those outputs. Protected replay may consume runtime diagnostics. Runtime must not import protected replay acceptance schemas.

9. Evidence does not automatically own behavior.

   Reports, dashboards, trend windows, recurrence files, and audit artifacts can explain behavior. They do not become runtime policy or protected acceptance unless explicitly classified as such.

10. Governance is doctrine and drift-watch, not gameplay.

    Ownership ledgers, governance tests, and audit tools declare and watch target architecture. They should not be interpreted as proof that implementation is already clean, nor as a second runtime policy stack.

### Stable Ownership Boundaries

| Boundary | Stable owner |
|---|---|
| API-visible turn transaction | `game.api` |
| State-domain registry and guard vocabulary | `game.state_authority` |
| Persistence mechanics and runtime envelopes | `game.storage` |
| Fresh/reset runtime document factories | `game.campaign_state`, `game.session`, `game.campaign_reset` |
| Domain simulation outcomes | Domain modules such as `game.noncombat_resolution`, `game.exploration`, `game.social`, `game.combat`, `game.world_progression`, `game.interaction_context` |
| CTIR meaning shape and runtime attachment | `game.ctir`, `game.ctir_runtime`, with lifecycle placement by `game.api` |
| Prompt context assembly | `game.prompt_context`, `game.narration_plan_bundle`, related narrative/policy read models |
| GPT call and guard mechanics | `game.gm`, model routing modules |
| Final-emission orchestration and packaging | `game.final_emission_runtime`, `game.final_emission_gate`, `game.final_emission_finalize`, `game.final_emission_meta` |
| Runtime diagnostic lineage projection | `game.final_emission_replay_projection` |
| Protected replay projection and acceptance fields | `tests.helpers.golden_replay_projection`, `tests.helpers.golden_replay_projection_fields`, protected registry, protected manifest |
| Replay governance doctrine | `docs/testing/protected_replay_manifest.md`, `docs/testing/replay_governance_authority.md`, replay governance tests |
| Architecture ownership doctrine | `docs/architecture_ownership_ledger.md` plus AR doctrine reports |

### Intentional Overlaps

| Overlap | Why it is intentional |
|---|---|
| API and storage both appear in persistence flows | API owns transaction timing; storage owns load/save mechanics. |
| API and CTIR runtime both appear in CTIR lifecycle | API owns when CTIR is detached/attached; CTIR modules own shape and attachment helpers. |
| Prompt construction and CTIR both touch narration meaning | CTIR owns resolved-turn meaning; prompt construction adapts it into model context. |
| Fallback content author, selector, applicator, and recorder differ | Fallback is both runtime safety and evidence-bearing behavior. These roles answer different questions. |
| Opening scene spans API, planning, realization, fallback, final emission, persistence, and replay | Campaign start is both bootstrap and first emitted turn. Split ownership preserves each responsibility. |
| Final emission and strict-social emission both affect final text | Strict-social modules own dialogue semantics; final emission owns last-mile legality/packaging. |
| Runtime diagnostic projection and protected replay projection both read FEM/provenance | Runtime diagnostics explain lineage; protected replay defines acceptance observations. |
| Governance docs and implementation both name owners | Governance states target architecture; implementation performs runtime behavior. |

### Transitional Responsibilities

| Responsibility | Transitional reason |
|---|---|
| Final-emission semantic repairs | Target doctrine is legality and packaging, but current behavior still includes guarded semantic repair/fallback paths. |
| Dual fallback-family vocabulary | Runtime and protected replay still need compatibility projection until consumer precedence is fully clarified. |
| Opening fallback owner buckets | Protected replay observes compatibility fields while runtime has multiple opening fallback axes. |
| CTIR-absent prompt semantic fallbacks | Useful compatibility residue, but not a long-term co-owner of resolved-turn meaning. |
| Evidence artifact fanout | Reports are useful, but canonical/generated/advisory status needs clearer long-term indexing. |
| Broad API coordination | API breadth is permanent as a transaction spine; some delegate seams remain candidates for documentation or later extraction. |

## Canonical Layer Specification

### Request/API

Purpose:

- Accept external player/API requests and expose response payloads.
- Establish request eligibility and user-visible response invariants.

Canonical owners:

- `game.api`
- API request/response models and API-facing preflight presentation helpers.

Allowed responsibilities:

- Route `/api/start_campaign`, chat, and action flows.
- Load initial runtime state through storage.
- Enforce start/action/chat eligibility.
- Invoke the runtime turn transaction.
- Construct API responses and preserve final text invariants.

Outside the layer:

- Domain simulation truth.
- GPT model call mechanics.
- Protected replay acceptance.
- Governance policy execution.

Allowed dependencies:

- Runtime orchestration helpers, storage, domain modules, CTIR runtime, prompt/GPT layer, final-emission delegate, logging helpers.

Forbidden dependencies:

- `tests.helpers.golden_replay_projection` and protected replay field definitions.
- Advisory report generators.
- Governance manifests as runtime decision engines.

### Runtime Orchestration

Purpose:

- Coordinate the full resolved-turn lifecycle as one transaction.

Canonical owners:

- `game.api` for transaction sequence.
- `game.ctir_runtime` for CTIR lifecycle helpers.
- Runtime packet/telemetry helpers for local contracts where used.

Allowed responsibilities:

- Detach stale CTIR.
- Apply authoritative mutation orchestration.
- Place CTIR construction after mutation and hygiene.
- Invoke prompt/GPT/retry/fallback flow.
- Hand candidate output to final emission.
- Persist, log, trace, and respond after finalization.

Outside the layer:

- Owning domain-specific truth.
- Owning GPT expression.
- Defining protected replay acceptance fields.

Allowed dependencies:

- Domain simulation, CTIR construction, prompt construction, GPT/model routing, fallback helpers, final emission, storage, provenance packagers.

Forbidden dependencies:

- Protected replay schemas.
- Offline governance registries as runtime policy engines.
- Generated/advisory artifacts as behavior inputs.

### Domain Simulation

Purpose:

- Convert player intent and current state into authoritative game outcomes.

Canonical owners:

- `game.noncombat_resolution`
- `game.exploration`
- `game.social`
- `game.combat`
- `game.world_progression`
- `game.interaction_context`
- `game.scene_actions`
- `game.skill_checks`
- Domain-specific state helpers.

Allowed responsibilities:

- Resolve actions and social/exploration/combat outcomes.
- Mutate or request mutation of authoritative world/session/scene/combat domains through declared seams.
- Produce machine-readable resolution data.
- Maintain interaction continuity and world progression truth.

Outside the layer:

- Narration prose authorship.
- Final player-facing text selection.
- Protected replay projection.
- Governance doctrine.

Allowed dependencies:

- Runtime state read models, storage-provided documents, domain contracts, state authority guards.

Forbidden dependencies:

- GPT output as a source of truth.
- Final-emission metadata as simulation input.
- Replay acceptance as runtime decision input.

### Narrative

Purpose:

- Translate authoritative state and resolved-turn meaning into model-ready narration context and candidate prose.

Canonical owners:

- `game.ctir`
- `game.prompt_context`
- `game.narration_plan_bundle`
- `game.narrative_planning`
- `game.opening_scene_realization`
- `game.opening_visible_fact_selection`
- `game.gm`
- `game.model_routing` and related route/runtime modules.

Allowed responsibilities:

- Build CTIR meaning shape from explicit post-mutation slices.
- Assemble prompt context from CTIR, visibility, response policy, plans, and read models.
- Curate opening diegetic basis lines and prompt obligations.
- Call and guard GPT.
- Preserve model route and upstream error metadata.

Outside the layer:

- Authoritative state mutation after domain resolution.
- Final text legality/packaging.
- Protected replay acceptance.
- Runtime retry/fallback loop ownership.

Allowed dependencies:

- CTIR, domain read models, response policy contracts, visibility/publication read models, narrative plans, model routing.

Forbidden dependencies:

- Rebuilding CTIR-owned turn meaning when CTIR exists.
- Using final-emission metadata as prompt truth.
- Importing protected replay fields.

### Final Emission

Purpose:

- Produce the canonical final player-facing text and final-emission metadata from candidate output.

Canonical owners:

- `game.final_emission_runtime`
- `game.final_emission_gate`
- `game.final_emission_finalize`
- `game.final_emission_meta`
- `game.final_emission_repairs`
- `game.final_emission_validators`
- `game.output_sanitizer`
- Strict-social emission owner where dialogue-specific semantics are involved.

Allowed responsibilities:

- Select accepted/prepared/fallback text.
- Apply legality, safety, visibility, response-shape, and sanitizer constraints.
- Package final output and `_final_emission_meta`.
- Record mutation/provenance/fallback lineage.
- Apply sealed deterministic terminal exceptions when candidate text cannot legally ship.

Outside the layer:

- Owning domain simulation truth.
- Owning ordinary semantic content synthesis.
- Defining replay acceptance fields.
- Treating diagnostics as selection policy.

Allowed dependencies:

- Candidate GM output, response contracts, strict-social emission output, sanitizer traces, turn packet/telemetry, provenance helpers, upstream prepared emission fields.

Forbidden dependencies:

- Protected replay projection modules.
- Advisory evidence tools.
- Governance docs as runtime rule sources.

### Persistence

Purpose:

- Store and retrieve runtime documents, scene overlays, snapshots, and logs.

Canonical owners:

- `game.storage`
- `game.campaign_state`
- `game.session`
- `game.campaign_reset`
- Runtime persistence envelope documentation.

Allowed responsibilities:

- Load/save session, world, combat, scene runtime, snapshots, and logs.
- Maintain runtime envelope mechanics.
- Create/reset runtime document shapes.
- Append/load/clear logs as storage operations.

Outside the layer:

- Deciding turn transaction completion.
- Authoring final text.
- Owning domain simulation semantics.
- Defining replay acceptance.

Allowed dependencies:

- Filesystem/runtime data envelopes, schema/default factories, transaction callers.

Forbidden dependencies:

- GPT/model behavior.
- Final-emission repair policy.
- Protected replay acceptance decisions.

### Replay/Evidence

Purpose:

- Observe finalized runtime outputs and project them into diagnostics, protected observations, trends, and reports.

Canonical owners:

- Runtime diagnostic projection: `game.final_emission_replay_projection`.
- Protected projection: `tests.helpers.golden_replay_projection`.
- Protected fields: `tests.helpers.golden_replay_projection_fields`.
- Protected corpus/registry: `tests.helpers.protected_replay_registry`.
- Replay execution/trend helpers and evidence tools.

Allowed responsibilities:

- Project finalized payloads, FEM, logs, snapshots, and traces.
- Produce runtime diagnostic lineage events.
- Produce protected replay observation rows.
- Generate trend, recurrence, incidence, provenance, and drift evidence.

Outside the layer:

- Runtime behavior selection.
- Final-emission write-time metadata stamping.
- Domain truth.
- Hidden pass/fail policy outside protected acceptance/governance.

Allowed dependencies:

- Finalized runtime payloads, logs, snapshots, FEM/provenance metadata, runtime diagnostic projection.

Forbidden dependencies:

- Runtime importing protected replay acceptance helpers.
- Advisory reports redefining governance or protected schema.
- Evidence projections mutating runtime outputs.

### Governance

Purpose:

- Declare ownership, target doctrine, protected replay policy, and drift-watch constraints.

Canonical owners:

- `docs/architecture_ownership_ledger.md`
- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- Replay governance tests.
- Ownership guard tests.
- Architecture/replay/final-emission audit tools as drift-watch aids.

Allowed responsibilities:

- Define target ownership.
- Define protected replay policy and governance decision vocabulary.
- Guard dependency direction.
- Flag drift and ownership confusion.

Outside the layer:

- Gameplay execution.
- Runtime selection/fallback behavior.
- Model routing.
- Persistence mechanics.

Allowed dependencies:

- Static source inspection, tests, generated inventories, documented owner declarations, replay/evidence outputs.

Forbidden dependencies:

- Becoming a runtime policy engine.
- Treating target ledgers as proof that implementation is clean.
- Promoting advisory artifacts into protected acceptance without explicit review.

## Multi-Axis Ownership Doctrine

The project uses multi-axis ownership because some outcomes are produced by a pipeline, not by a single semantic owner. This is especially true for fallback, opening narration, final emission, provenance, and replay. The correct architectural question is often not "who owns this?" but "which ownership axis are we asking about?"

| Axis | Definition | Typical owner | Use when asking |
|---|---|---|---|
| Runtime owner | The module responsible for coordinating a runtime transaction or runtime decision point. | `game.api`, final-emission runtime/gate delegates | Who controls the live execution sequence? |
| Domain owner | The module responsible for authoritative simulation truth in a domain. | World, scene, social, combat, interaction, state authority registry/domain modules | Who decides what actually happened in game state? |
| Content author | The source that authored candidate prose or deterministic fallback text. | GPT, `game.gm_retry`, opening/social/diegetic fallback modules | Who wrote the words or fallback content? |
| Selector | The module that chooses among normal, retry, prepared, fallback, or sealed candidates. | API retry loop, final-emission gate, strict-social selector paths | Who chose this candidate over alternatives? |
| Applicator | The module that applies the chosen candidate to the runtime GM output or final payload. | API, final-emission gate/finalize, sanitizer | Who put the selected result into the object that ships? |
| Provenance packager | The module that stamps source, family, owner, fingerprint, or trace metadata explaining the output. | `game.realization_provenance`, `game.fallback_provenance_debug`, `game.final_emission_meta`, finalize helpers | Who recorded why this output exists? |
| Runtime diagnostic owner | The read-side runtime module that projects finalized metadata into diagnostic lineage. | `game.final_emission_replay_projection` | Who explains runtime lineage after the fact? |
| Protected replay owner | The test/governance layer that defines protected observation fields and acceptance projection. | Golden replay projection helpers, protected fields, registry, manifest | Who decides what replay locks and compares? |

Rules for using these axes:

- Use runtime owner for live transaction sequencing.
- Use domain owner for authoritative game state.
- Use content author for prose/fallback authorship.
- Use selector and applicator separately when fallback or final emission is involved.
- Use provenance packager for write-time evidence, not behavior ownership.
- Use runtime diagnostic owner for read-side explanation of finalized runtime metadata.
- Use protected replay owner for acceptance schema and drift observation.
- Do not collapse axes into one field unless the behavior truly has one owner on all axes.

## Canonicality Index

| Surface | Classification | Authority |
|---|---|---|
| `game.api` turn transaction | Runtime truth | Canonical runtime sequence for start/chat/action turns. |
| Domain resolution modules | Runtime truth | Canonical simulation outcomes for their domains. |
| `game.state_authority` | Governance contract | Canonical domain registry and guard vocabulary, not the state itself. |
| `game.storage` runtime documents and envelopes | Runtime truth | Canonical persistence mechanics and stored runtime documents. |
| Session/world/combat/scene runtime state | Runtime truth | Authoritative persisted state after transaction completion. |
| `game.ctir` / `game.ctir_runtime` | Runtime truth for narration meaning | Canonical resolved-turn meaning object and runtime attachment lifecycle. |
| `game.prompt_context` / narration plan bundle | Runtime projection | Projection/adaptation of runtime truth into GPT prompt context. |
| `game.gm` / model routing | Runtime projection | Model I/O and candidate prose route metadata; not authoritative state. |
| GPT candidate output | Runtime projection | Candidate expression subject to retry/final emission, not truth. |
| `game.realization_authority` | Governance contract | Canonical realization/fallback vocabulary. |
| `game.realization_provenance` and `game.fallback_provenance_debug` | Runtime truth for provenance stamps | Write-time metadata explaining fallback/realization decisions. |
| `game.final_emission_runtime` / gate / finalize / meta | Runtime truth | Canonical final player-facing emission and FEM packaging. |
| `game.final_emission_replay_projection` | Runtime projection | Diagnostic read-side projection of finalized FEM/lineage. |
| API response payload | Runtime truth | Shipped turn response surface. |
| Session log entry | Runtime truth | Persisted turn record and replay input surface. |
| Debug trace / latency / telemetry | Runtime projection | Runtime diagnostics; useful evidence, not domain truth. |
| `tests.helpers.golden_replay_projection` | Protected acceptance | Canonical protected observation projection. |
| `tests.helpers.golden_replay_projection_fields` | Protected acceptance | Canonical protected field list/schema. |
| `tests.helpers.protected_replay_registry` | Protected acceptance | Canonical protected/supporting/advisory scenario identity. |
| `docs/testing/protected_replay_manifest.md` | Governance contract | Canonical protected replay policy and manifest doctrine. |
| Replay governance docs/tests | Governance contract | Canonical replay governance vocabulary and dependency rules. |
| `docs/architecture_ownership_ledger.md` | Governance contract | Target ownership ledger and drift-watch doctrine. |
| AR-AA / AR-AB / AR-AC / AR-AD reports | Governance contract | Reconciliation doctrine and architectural decision trail. |
| `artifacts/golden_replay/*` generated reports | Generated artifact | Evidence generated from replay/tooling; canonical only where explicitly promoted. |
| Fallback incidence, provenance, recurrence, drift reports | Advisory artifact | Diagnostic evidence unless explicitly named as protected/governance authority. |
| Architecture/final-emission/provenance audit tools | Advisory artifact | Drift-watch tools; not runtime behavior. |
| `tests/TEST_AUDIT.md` and test inventory governance | Governance contract | Canonical test ownership map and suite placement guidance. |

## Transitional Architecture Register

| Element | Current purpose | Reason transitional | Desired long-term direction | Preconditions before simplification |
|---|---|---|---|---|
| Final-emission semantic repairs | Preserve shipped response legality, shape, safety, and fallback behavior at the last mile. | Target doctrine is legality/packaging; some current paths still synthesize or reorder meaning. | Classify each repair as legality-only, packaging-only, sealed exception, or upstream-owned semantic synthesis. | Stable repair classification, protected replay coverage, clear upstream owner for any moved semantic responsibility. |
| Dual fallback-family vocabulary | Preserve runtime diegetic family and governed realization family while projecting replay compatibility fields. | Two fields answer related but different questions; protected replay currently compresses some observations. | Document field precedence and consumers before any schema simplification. | Consumer inventory, replay proof, migration plan, no loss of provenance meaning. |
| Fallback ownership field fanout | Explain content author, selector, applicator, provenance, recorder, and observer roles. | High evidence value but high cognitive load. | Keep multi-axis vocabulary, reduce duplicate interpretation. | Canonical fallback/provenance field map and agreement on write-time truth vs read-side projection. |
| Opening fallback owner buckets | Let protected replay observe opening fallback authorship/source while runtime carries multiple opening axes. | Opening crosses bootstrap, planning, fallback, final emission, persistence, and replay. | Preserve opening handoff doctrine; simplify only compatibility projection if evidence permits. | Opening handoff checklist, replay evidence, no hidden collapse of structural opening ownership. |
| CTIR-absent prompt fallbacks | Keep prompt construction tolerant of legacy/missing CTIR paths. | CTIR is intended canonical resolved-turn meaning when present. | Treat fallback reads as compatibility residue, not semantic co-ownership. | Confidence that all normal resolved-turn paths attach CTIR before prompt construction; regression coverage for absence behavior. |
| Evidence artifact fanout | Provide trend, recurrence, incidence, provenance, and drift evidence. | Many artifacts can blur canonical vs advisory authority. | Label surfaces as protected acceptance, governance contract, generated artifact, or advisory artifact. | Canonicality index adopted by future docs and report-generation cycles. |
| API coordination breadth | Keep the single turn transaction coherent. | API has many responsibilities because it owns transaction order, but local comprehension can suffer. | Preserve API as spine; document narrow delegate seams where ownership is already clear. | Doctrine agreement that delegate extraction must not split transaction authority or hide behavior. |
| Final-emission replay projection fanout | Produce diagnostic lineage from finalized FEM/provenance. | Read-side projection can become a magnet if it absorbs acceptance or governance concepts. | Keep as runtime diagnostic owner; use facades/read helpers only if they reduce confusion. | Explicit dependency direction tests/docs and no runtime import of protected acceptance schemas. |
| Generated/advisory reports as decision inputs | Support investigation and corrective locality work. | Repeated evidence may be mistaken for policy. | Require explicit promotion before advisory reports become protected or governance authority. | Canonicality labels and a promotion review convention. |

## Architectural Design Principles

1. Runtime truth before narration.
2. One turn, one transaction spine.
3. Domain modules own simulation truth.
4. CTIR is the resolved-turn meaning boundary for narration.
5. Prompt construction adapts truth; it does not create truth.
6. GPT authors candidate expression only.
7. Final emission legalizes, selects, packages, and records; it should not quietly become the semantic author.
8. Fallback ownership is multi-axis by design.
9. Provenance explains behavior without owning behavior.
10. Replay dependency flows from runtime output toward evidence, never backward into runtime.
11. Protected replay acceptance is separate from runtime diagnostic projection.
12. Governance declares and watches architecture; it does not execute gameplay.
13. Generated and advisory artifacts require explicit promotion before becoming authority.
14. Preserve behavior before simplifying architecture.
15. Prefer clear documentation over premature refactoring when the boundary is understandable but broad.

## Recommended Focus for AR-AE

AR-AE should be an architectural adoption and alignment pass, not a runtime refactor.

Recommended AR-AE focus:

1. Decide where this target doctrine should live long-term: root AR report only, `docs/` architecture page, or an update to the architecture ownership ledger.
2. Create a compact cross-reference from existing ownership docs to this doctrine so future cycles do not rediscover the same layer model.
3. Validate the canonicality index against the most-used replay/evidence artifacts and flag any surface whose authority status is ambiguous.
4. Draft a final-emission repair classification table using the categories in this doctrine, without changing code.
5. Draft a fallback/provenance field consumer map with write-time truth vs read-side projection labels, without changing code.

AR-AE should continue to avoid runtime behavior changes unless a later cycle explicitly scopes and validates an implementation change.

## Validation Notes

No runtime files were intentionally modified. This cycle produced this documentation artifact only.

Suggested validation:

- Run `git status --short`.
- Confirm only `AR-AD_target_architecture_doctrine.md` was added by this cycle, aside from pre-existing untracked AR-AA/AR-AB/AR-AC/foundation discovery artifacts.
