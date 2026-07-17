# AR-AF Architecture Reconciliation Synthesis

Date: 2026-07-14  
Scope: documentation-only synthesis of Architecture Reconciliation Campaign 1  
Inputs: `AR-AA_architectural_mapping_discovery.md`, `AR-AB_runtime_authority_and_replay_boundary_map.md`, `AR-AC_architectural_ownership_reconciliation.md`, `AR-AD_target_architecture_doctrine.md`, `AR-AE_architecture_conformance_assessment.md`  
Non-goal: runtime refactor, behavior change, schema promotion, replay policy change

## Executive Summary

The baseline architecture is a single-turn runtime transaction with stable domain ownership, CTIR-backed narration meaning, final-emission legality and packaging, durable persistence, one-way replay projection, and governance as doctrine rather than gameplay.

Future implementation work should assume this architecture as the current baseline:

- `game.api` is the runtime transaction spine for start, chat, and action turns.
- Domain modules own simulation truth; `game.state_authority` owns the registry and guard vocabulary.
- CTIR is the resolved-turn meaning boundary for narration.
- Prompt construction adapts authoritative state and CTIR into GPT context.
- GPT/model routing owns expression and model I/O, not game truth.
- Retry/fallback is intentionally multi-axis: content author, selector, applicator, provenance packager, final recorder, runtime diagnostic owner, and protected replay owner may differ.
- Final emission owns final selection, legality, packaging, metadata, and sealed terminal exceptions.
- Persistence stores runtime documents and logs; API owns transaction timing.
- Runtime diagnostic projection and protected replay acceptance are separate, with dependency flowing from runtime output toward evidence.
- Governance documents and tests declare target ownership and drift-watch rules; they do not execute gameplay.

Campaign 1 answered the architectural question: the project understands the architecture well enough to begin refinement work. The roadmap should adapt from discovery/reconciliation toward targeted refinement-readiness: final-emission repair classification, fallback/provenance field consumer mapping, evidence canonicality labeling, and durable documentation placement.

## Architectural Baseline

### Runtime Transaction Model

The runtime is organized around one turn transaction.

`game.api` owns the transaction sequence:

1. Accept request and establish route eligibility.
2. Load runtime state through storage.
3. Normalize intent and invoke domain resolution.
4. Apply authoritative state mutation.
5. Detach stale CTIR and attach one post-mutation CTIR for narration.
6. Build prompt context from CTIR, visibility, response policy, plans, and read models.
7. Invoke GPT/model routing and guard returned candidate output.
8. Orchestrate retry/fallback selection when model output or upstream availability fails.
9. Hand candidate/prepared/fallback output to final emission.
10. Persist finalized state and append logs.
11. Build API response and trace/debug surfaces.

This broad API ownership is architectural, not accidental. Future work may clarify delegate seams, but should not split the single transaction spine unless a later campaign explicitly changes the doctrine.

### Layer Model

| Layer | Baseline responsibility | Canonical owners |
|---|---|---|
| Request/API | Request routing, eligibility, API response invariants, transaction entry/exit. | `game.api` |
| Runtime orchestration | Turn sequence, CTIR lifecycle placement, GPT/retry/fallback orchestration, finalization handoff, persistence/log timing. | `game.api`, `game.ctir_runtime`, runtime packet/telemetry helpers |
| Domain simulation | Authoritative game outcomes and state transition semantics. | `game.noncombat_resolution`, `game.exploration`, `game.social`, `game.combat`, `game.world_progression`, `game.interaction_context`, related domain modules |
| Narrative | CTIR meaning shape, prompt construction, narrative plans, opening basis facts, GPT/model I/O. | `game.ctir`, `game.prompt_context`, `game.narration_plan_bundle`, `game.narrative_planning`, `game.opening_scene_realization`, `game.gm`, model routing modules |
| Final emission | Final player-facing text selection, legality, sanitizer/validator constraints, metadata packaging, sealed terminal exceptions. | `game.final_emission_runtime`, `game.final_emission_gate`, `game.final_emission_finalize`, `game.final_emission_meta`, repair/validator/sanitizer modules |
| Persistence | Runtime document load/save, envelopes, snapshots, logs, reset/factory shapes. | `game.storage`, `game.campaign_state`, `game.session`, `game.campaign_reset` |
| Replay/evidence | Runtime diagnostic projection, protected observation projection, replay trend/incidence/provenance artifacts. | `game.final_emission_replay_projection`, `tests.helpers.golden_replay_projection`, protected replay helpers, evidence tools |
| Governance | Ownership doctrine, replay policy, dependency guards, drift-watch. | `docs/architecture_ownership_ledger.md`, protected replay docs, governance tests, audit tools |

### Permanent Ownership Boundaries

These boundaries should be assumed stable:

- `game.api` owns runtime transaction order.
- Domain modules own simulation truth.
- `game.state_authority` owns state-domain registry and guard vocabulary, not actual domain state.
- `game.storage` owns persistence mechanics.
- `game.ctir` and `game.ctir_runtime` own resolved-turn meaning shape and CTIR runtime lifecycle helpers.
- `game.prompt_context` owns prompt/adaptation assembly, not authoritative semantics.
- `game.gm` and model routing own model I/O and route metadata.
- Final-emission modules own last-mile selection, legality, packaging, and FEM.
- `game.realization_authority` and provenance helpers own fallback/provenance vocabulary and write-time stamps.
- `game.final_emission_replay_projection` owns runtime diagnostic lineage projection.
- Golden/protected replay helpers and manifest own protected acceptance projection.
- Governance docs/tests own target ownership and drift-watch doctrine.

### Replay Boundaries

Replay uses a one-way dependency model:

```text
Runtime execution
  -> finalized payloads, logs, snapshots, FEM, traces, provenance
  -> runtime diagnostic projection
  -> protected replay projection and evidence tooling
  -> governance/advisory review
```

Runtime may emit diagnostics. Protected replay may consume runtime diagnostics. Runtime must not import protected replay acceptance fields, protected replay projection helpers, or governance manifests as behavior inputs.

Runtime diagnostic projection and protected acceptance projection answer different questions:

- Runtime diagnostic projection explains what finalized runtime metadata says.
- Protected replay projection defines what replay observes and locks.

They should remain separate.

### Evidence Model

Evidence is first-class but not automatically authoritative.

| Evidence surface | Baseline status |
|---|---|
| Runtime payloads/logs/snapshots/FEM | Runtime truth |
| Debug trace, latency, telemetry, lineage projection | Runtime projection |
| Protected replay fields/projection/registry | Protected acceptance |
| Ownership ledger, protected replay manifest, governance tests | Governance contract |
| Generated replay reports and artifact manifests | Generated artifacts |
| Fallback incidence, recurrence, provenance, drift, audit reports | Advisory artifacts unless explicitly promoted |

Future work should preserve evidence without confusing evidence with runtime ownership.

### Governance Model

Governance states doctrine and checks drift. It does not execute gameplay.

Governance surfaces may:

- declare canonical owners,
- define protected replay policy,
- guard dependency direction,
- classify evidence,
- flag drift.

Governance surfaces may not:

- mutate runtime state,
- select fallback behavior,
- define GPT/model outputs,
- silently promote advisory reports into protected acceptance,
- treat target ledgers as proof that implementation is already clean.

## Architectural Invariants

Future work should preserve these rules:

1. Runtime truth is established before narration.
2. A turn has one runtime transaction spine.
3. `game.api` owns transaction order.
4. Domain modules own authoritative simulation outcomes.
5. `game.state_authority` is registry and guard vocabulary, not a universal state engine.
6. CTIR is the resolved-turn meaning boundary for narration.
7. Prompt construction adapts CTIR and approved read models; it does not recreate turn truth when CTIR exists.
8. GPT authors candidate expression only.
9. Retry/fallback ownership is multi-axis by design.
10. Final emission owns final selection, legality, packaging, FEM, and sealed terminal exceptions.
11. Persistence mechanics belong to storage; transaction timing belongs to API.
12. Runtime diagnostic projection and protected replay acceptance remain separate.
13. Replay dependency flows from runtime outputs toward evidence, never back into runtime.
14. Provenance explains behavior without owning behavior.
15. Governance declares and watches architecture; it does not execute gameplay.
16. Generated/advisory artifacts require explicit promotion before becoming authority.
17. Documentation should clarify broad but coherent boundaries before implementation refactors are attempted.

## Architectural Flexibility Register

| Area | Why flexibility exists | Future work may safely change | Must remain fixed |
|---|---|---|---|
| API delegate seams | `game.api` is broad because it owns transaction order. | Helper/delegate structure for preflight, trace/log assembly, persistence tail, or response construction. | `game.api` remains transaction spine unless doctrine changes explicitly. |
| Final-emission repair categories | Some final-emission repairs are transitional semantic pressure. | Classification and eventual ownership of specific repairs after evidence review. | Final emission remains last-mile legality/packaging/FEM boundary. |
| Fallback/provenance fields | Fallback needs multi-axis evidence. | Field consumer documentation, read-side projection helpers, precedence docs. | Content author, selector, applicator, provenance, recorder, and observer axes remain distinct. |
| Dual fallback-family vocabulary | Runtime and replay currently answer different family questions. | Consumer precedence, compatibility projection, possible future schema simplification. | Runtime schema should not be collapsed solely to simplify replay rows without replay proof. |
| Opening realization handoff | Opening crosses bootstrap, planning, realization, fallback, final emission, persistence, and replay. | Handoff documentation, checklist structure, compatibility field interpretation. | Opening realization does not become structural opening authority; planning/API/final-emission roles remain distinct. |
| CTIR-absent prompt compatibility | Legacy/missing CTIR tolerance remains useful. | Documentation or retirement assessment for compatibility fallback reads. | CTIR remains canonical resolved-turn meaning when present. |
| Evidence artifact set | Many generated/advisory reports exist from stabilization work. | Canonicality labels, report retention/promotion rules, artifact organization. | Protected acceptance, runtime diagnostics, governance contracts, generated artifacts, and advisory artifacts remain separate categories. |
| Runtime diagnostic projection helpers | Read-side projection has broad field fanout. | Facades/read helpers that reduce conceptual load. | Runtime projection must not import protected acceptance schema or own runtime behavior. |
| Governance placement | AR reports and existing docs overlap in authority. | Cross-references, durable doc placement, summary pages. | Governance remains doctrine/drift-watch, not runtime policy execution. |

## Durable Campaign Outputs

| Output | Long-term status | Use |
|---|---|---|
| `AR-AA_architectural_mapping_discovery.md` | Historical reference | Broad discovery map and file inventory. Useful when rechecking original architectural evidence. |
| `AR-AB_runtime_authority_and_replay_boundary_map.md` | Long-term reference | Runtime authority ledger, start-campaign flow map, replay boundary map, fallback ownership map. |
| `AR-AC_architectural_ownership_reconciliation.md` | Long-term reference | Permanent vs transitional ownership classification and layer reconciliation. |
| `AR-AD_target_architecture_doctrine.md` | Long-term reference | Target doctrine, canonical layer specification, multi-axis ownership vocabulary, canonicality index. |
| `AR-AE_architecture_conformance_assessment.md` | Long-term reference | Current implementation conformance assessment and refinement readiness. |
| `AR-AF_architecture_reconciliation_synthesis.md` | Baseline reference | Concise architecture baseline for future implementation campaigns. |

Recommended durable reference order:

1. Use AR-AF as the first-stop baseline.
2. Use AR-AD when doctrine details are needed.
3. Use AR-AE when assessing whether implementation conformance has already been reviewed.
4. Use AR-AB for concrete runtime/replay ownership maps.
5. Use AR-AC for permanent/transitional reconciliation rationale.
6. Use AR-AA for original discovery context and file inventory.

AR-AA should mostly remain historical. AR-AB through AR-AF should remain active long-term references until their content is folded into durable `docs/` architecture pages.

## Campaign Closeout Assessment

### What Campaign 1 Taught Us

Campaign 1 showed that the architecture is substantially coherent and already governed. The central issue was not missing architecture; it was broad, evidence-heavy ownership that needed reconciliation into a stable doctrine.

The project has a clear runtime pipeline, stable persistence and state authority model, explicit CTIR boundary, coherent prompt/GPT split, mature final-emission boundary, strong replay separation, and rich evidence surfaces.

### Architectural Decisions Resulting From Campaign 1

Campaign 1 established these decisions:

- Keep `game.api` as the single transaction spine.
- Treat CTIR as the resolved-turn meaning boundary for narration.
- Keep prompt construction as adapter/packager, not semantic authority.
- Keep GPT/model routing as expression and model I/O, not state truth.
- Keep final emission as final selection, legality, packaging, metadata, and sealed exception boundary.
- Preserve multi-axis fallback/provenance ownership.
- Preserve runtime diagnostic projection and protected replay acceptance as separate surfaces.
- Treat governance as doctrine and drift-watch, not runtime behavior.
- Treat generated/advisory artifacts as evidence unless explicitly promoted.
- Begin refinement only after transitional responsibilities are classified and evidence-backed.

### What Question Naturally Comes Next

The next question is:

Which transitional responsibilities are ready to be simplified without changing behavior or weakening evidence?

That question should be answered by classification and consumer mapping before implementation work:

- Which final-emission repairs are legality-only, packaging-only, sealed exceptions, or upstream semantic synthesis?
- Which fallback/provenance fields are write-time truth, runtime projection, protected acceptance, generated artifact, or advisory reads?
- Which evidence artifacts are canonical, generated, or advisory?
- Which documentation location should carry the baseline doctrine permanently?

### Should The Roadmap Continue Unchanged Or Adapt?

The roadmap should adapt.

The project no longer needs broad architecture discovery as the next step. It should move into refinement-readiness: targeted documentation that prepares narrow future implementation campaigns. Runtime refactoring should remain out of scope until a later campaign has classified the relevant transitional responsibility, mapped its consumers, and identified replay/evidence proof.

## Recommendation For The Next Campaign

The next campaign should be **Architectural Refinement Readiness**, still documentation-first.

Recommended focus:

1. Final-emission repair classification.
2. Fallback/provenance field consumer map.
3. Evidence canonicality inventory.
4. Durable docs placement for the AR-AF baseline and AR-AD doctrine.
5. Readiness criteria for future implementation-level simplification.

Suggested next cycle title:

**AR-AG - Refinement Readiness and Canonicality Index**

Suggested non-goals:

- Do not move runtime code.
- Do not collapse fallback fields.
- Do not merge runtime diagnostic projection with protected replay projection.
- Do not promote advisory artifacts without explicit governance review.

## Validation Notes

No runtime files were intentionally modified. This cycle produced this documentation artifact only.

Suggested validation:

- Run `git status --short`.
- Confirm only `AR-AF_architecture_reconciliation_synthesis.md` was added by this cycle, aside from pre-existing untracked AR-AA/AR-AB/AR-AC/AR-AD/AR-AE/foundation discovery artifacts.
