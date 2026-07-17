# AR-AB Runtime Authority and Replay Boundary Map

Date: 2026-07-01  
Scope: documentation-only current-state architecture map for Architecture Reconciliation cycle 2  
Inputs: `AR-AA_architectural_mapping_discovery.md`, targeted static inspection of runtime, final-emission, fallback, CTIR, and replay projection modules  
Non-goal: refactor, behavior change, schema promotion, replay policy change

## Executive Summary

The current runtime architecture is stable, but its authority is broad and heavily governed. `game.api` is the real runtime spine: it owns request entry, state loading, campaign-start gating, authoritative mutation orchestration, CTIR timing, GPT/retry orchestration, final-emission handoff, persistence, logging, trace capture, and response construction. That breadth is not accidental by itself; it is the coordination point where first-turn bootstrap and ordinary resolved turns converge.

The key reconciliation finding is that ownership is multi-axis. "Fallback owner", "opening owner", and "replay owner" are not single fields. The implementation distinguishes runtime owner, content author, selector/applicator, provenance packager, runtime diagnostic projection, and protected replay acceptance owner. The design is currently healthiest when those axes stay separate.

Replay boundaries are explicit and should remain so:

- Runtime diagnostic projection is `game.final_emission_replay_projection`.
- Protected replay projection and acceptance schema are `tests.helpers.golden_replay_projection`, `tests.helpers.golden_replay_projection_fields`, the protected replay registry, and `docs/testing/protected_replay_manifest.md`.
- Protected replay may consume runtime diagnostics.
- Runtime must not depend on protected replay acceptance structures.

AR-AC should focus on reducing coordination cost around the broad runtime spine and final-emission/fallback evidence fanout without collapsing intentionally separate ownership axes.

## Runtime Authority Ledger

| Surface | Runtime owner | Content author | Selector / applicator | Provenance packager | Replay projection owner | Protected replay acceptance owner | Relevant files | Architectural notes |
|---|---|---|---|---|---|---|---|---|
| Campaign start | `game.api.start_campaign` | Opening content comes from scene/public visibility, narrative plan, GPT output, and deterministic opening fallback when needed | `game.api` builds bootstrap resolution and invokes shared resolved-turn pipeline; final selection passes through final-emission delegate | Final emission metadata plus opening debug copied by `_complete_opening_turn_persistence_like_chat`; fallback family stamp may come from realization provenance | `game.final_emission_replay_projection` reads finalized FEM and lineage | `tests.helpers.golden_replay_projection`, `tests.helpers.protected_replay_registry`, protected manifest | `game/api.py`, `game/opening_scene_realization.py`, `game/opening_deterministic_fallback.py`, `game/final_emission_runtime.py`, `tests/test_start_campaign_api.py` | Start campaign is not a separate story generator. It bootstraps `scene_opening` into the same resolved-turn narration and final-emission tail as chat. |
| Shared resolved-turn pipeline | `game.api._run_resolved_turn_pipeline` | Domain resolution modules own action meaning before pipeline entry; GPT authors candidate prose after prompt construction | `game.api` detaches stale CTIR, applies authoritative mutation, derives response contract, then calls GPT narration builder | State mutation traces are appended through `build_state_mutation_trace`; later fallback/final-emission packagers add their own provenance | Runtime diagnostic projection observes final payload/FEM, not pipeline internals directly | Protected replay observes response/log/snapshot surfaces after execution | `game/api.py`, `game/noncombat_resolution.py`, `game/exploration.py`, `game/social.py`, `game/ctir_runtime.py` | The pipeline is the spine for `/api/action`, resolved `/api/chat`, and campaign opening. CTIR build intentionally happens after mutation and hygiene. |
| CTIR lifecycle | `game.ctir_runtime` with lifecycle placement owned by `game.api` | `game.ctir` constructs bounded resolved-turn meaning from explicit slices; engine state remains canonical elsewhere | `game.api` detaches at resolved-turn entry and ensures one CTIR for the narration stamp | CTIR stamp and attached session keys are lifecycle metadata, not fallback provenance | Runtime projection may indirectly observe downstream FEM effects, not define CTIR | Protected replay may observe resulting route/source/field outcomes, not CTIR authority | `game/ctir.py`, `game/ctir_runtime.py`, `game/api.py`, `docs/ctir_prompt_adapter_architecture.md` | CTIR is canonical resolved-turn meaning for narration, not canonical state. Prompt context consumes it; it must not reconstruct semantic meaning when CTIR exists. |
| Opening scene realization | Runtime entry is `game.api`; helper authority is `game.opening_scene_realization` for renderer/basis payloads | Structural opening obligations: `game.narrative_planning`; diegetic basis lines: `game.opening_scene_realization`; deterministic fallback: `game.opening_deterministic_fallback`; GPT candidate prose when healthy | `game.api` constructs `scene_opening`; final-emission gate/delegate selects accepted/prepared/fallback text | Opening debug and fallback fields are packed into metadata/FEM by final-emission and persistence tail | `game.final_emission_replay_projection` projects opening fallback ownership and lineage | Golden replay protected fields include opening fallback owner/authorship/source fields | `game/opening_scene_realization.py`, `game/opening_visible_fact_selection.py`, `game/opening_deterministic_fallback.py`, `game/upstream_response_repairs.py`, `game/final_emission_gate.py` | Boundary-sensitive but stable. Realization curates public diegetic basis; it is not a parallel structural opener authority. |
| GPT retry pipeline | `game.api._build_gpt_narration_from_authoritative_state` orchestrates; `game.gm` owns model call/guard mechanics | GPT authors normal candidate prose; `game.gm_retry` and diegetic fallback modules author deterministic terminal fallback prose | `game.api` chooses retry strategy and applies terminal fallback when budget/validation requires it | Retry terminal fallback stamps through `game.realization_provenance` and `game.final_emission_meta`; upstream fast-fallback provenance is separate | Runtime lineage projection reads FEM/provenance after finalization | Protected replay projects observed route/source/fallback fields | `game/api.py`, `game/gm.py`, `game/gm_retry.py`, `game/fallback_behavior.py`, `game/diegetic_fallback_narration.py` | GPT call/guarding and retry orchestration are intentionally split. API owns loop control; model layer owns call normalization. |
| Upstream fallback handling | `game.api._fast_fallback_for_upstream_error` | Terminal retry fallback prose usually comes from `game.gm_retry` and diegetic fallback helpers | `game.api` selects and applies fast fallback after upstream API error handling | `game.fallback_provenance_debug.attach_upstream_fast_fallback_provenance` packages selector-boundary fingerprints; `game.realization_provenance` stamps governed family | `game.final_emission_replay_projection` projects selection/content/provenance packager splits | Protected replay observes projected fallback family/source/owner fields | `game/api.py`, `game/fallback_provenance_debug.py`, `game/gm_retry.py`, `game/realization_provenance.py`, `game/final_emission_replay_projection.py` | Highest-pressure fallback surface. Selection/application, content authorship, and provenance packaging intentionally differ. |
| Final emission | Runtime caller surface is `game.final_emission_runtime.finalize_player_facing_emission`; canonical orchestration owner is `game.final_emission_gate` | Candidate prose comes from GPT/upstream/fallback modules; final emission should not own new semantic content except sealed deterministic terminal paths | Gate applies legality/repair/layer orchestration; finalize normalizes and packages output | `game.final_emission_meta`, `game.final_emission_finalize`, and provenance helpers package FEM, mutation lineage, gate entry/exit, fallback fields | `game.final_emission_replay_projection` derives runtime lineage events from finalized FEM | Golden replay acceptance reads normalized FEM and protected fields | `game/final_emission_runtime.py`, `game/final_emission_gate.py`, `game/final_emission_finalize.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py` | Governed transitional boundary. Target doctrine is legality plus packaging, but semantic repair pressure still exists and is tested. |
| Runtime lineage projection | `game.final_emission_replay_projection` | None; it must not author runtime content or mutate output | Read-side projection only from finalized FEM | It reads packaged provenance but does not package write-time provenance | This module owns `fem_runtime_lineage_events`, sealed sub-kinds, runtime lineage owner splits | Not acceptance authority; may feed diagnostics consumed by protected replay | `game/final_emission_replay_projection.py`, `game/runtime_lineage_telemetry.py` | Diagnostic/read-side only. Do not merge with protected acceptance projection. |
| Protected replay projection | Test-side replay helpers and manifest | None for runtime; scenarios/fixtures author replay inputs | `tests.helpers.golden_replay_projection.project_turn_observation` projects payload/snapshot into observation rows | It reads runtime provenance/FEM but does not stamp runtime metadata | May consume runtime lineage for diagnostics | `tests.helpers.golden_replay_projection_fields.PROTECTED_OBSERVATION_FIELDS`, protected registry, manifest | `tests/helpers/golden_replay_projection.py`, `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/protected_replay_registry.py`, `docs/testing/protected_replay_manifest.md` | Test-only CI acceptance schema. It must not become a runtime dependency or redefine runtime lineage semantics. |

## Start Campaign Runtime Flow Map

This is the current `/api/start_campaign` ownership trace from request to response.

| Stage | Current implementation owner | What happens | Replay/evidence surfaces touched |
|---|---|---|---|
| Request entry | `game.api.start_campaign` | FastAPI route resolves UI mode and asserts runtime action permission. | None yet. |
| Preflight validation | `game.api` plus upstream gate modules | Calls `compute_upstream_dependent_run_gate` and `build_upstream_dependent_run_gate_operator`; returns 503 if manual testing is blocked. | Response may include upstream gate diagnostic payload. |
| Runtime state loading | `game.storage` called by `game.api` | Loads campaign, character, session, recent log, then world/combat/conditions/active scene after eligibility passes. Synchronizes scene addressability and mirrors session scene state into scene envelope. | Later trace records starting scene and incoming payload. |
| Campaign-start eligibility | `game.api._session_allows_structured_start_campaign` | Allows only if `campaign_started` is false, recent log is empty, and `turn_counter` is 0. Otherwise returns 409 with projected state. | No replay mutation; response includes current state projection. |
| Opening-scene bootstrap | `game.api` | Starts turn timing, snapshots interlocutor, increments `turn_counter`, advances world tick and time pressure, segments empty bootstrap input, resolves directed-social entry, prepares interaction context, and builds normalized `scene_opening` action/resolution. | Trace source/action is `start_campaign`; bootstrap request log payload is prepared. |
| Authoritative state mutation | `game.api._run_resolved_turn_pipeline` and `_apply_authoritative_resolution_state_mutation` | Detaches stale CTIR, normalizes runtime engine result, applies deterministic world/session/scene/combat updates, records clue/lead updates, and appends mutation trace. | Debug trace gets state mutation trace; resolution later carries world tick events. |
| CTIR construction | `game.ctir_runtime`, placed by `game.api._build_gpt_narration_from_authoritative_state` | After mutation and resolution-facing hygiene, computes narration stamp, builds bounded CTIR via `build_runtime_ctir_for_narration`, attaches it to session, and ensures narration plan bundle for the same stamp. | CTIR itself is runtime session state, not a protected replay schema. |
| Prompt construction | `game.prompt_context`, `game.narration_plan_bundle`, `game.gm.build_messages` via API orchestration | Collects narration context from authoritative state, CTIR, plan bundle, visibility, response policy, and compact context. | Prompt/debug payloads may later appear in trace/FEM-adjacent diagnostics. |
| GPT execution | `game.gm.call_gpt` and `guard_gm_output`, invoked by API | Calls model with route context, guards output, preserves route/upstream metadata. | Model route/upstream error metadata may be preserved into GM output. |
| Retry/fallback handling | `game.api` orchestration; `game.gm_retry`, `game.fallback_behavior`, fallback content modules | Detects upstream errors or validation failures; retries where allowed; applies forced terminal fallback or upstream fast fallback when needed. | Fallback tags, metadata, realization family, and emergency nonplan output records may be attached. |
| Final emission | API tail calls `_finalize_player_facing_for_turn`, which delegates through `game.final_emission_runtime` to `game.final_emission_gate` | Sanitizes candidate text, promotes valid upstream prepared opening text when applicable, runs final-emission layers, reconciles state consistency, and marks GM output finalized. | `_final_emission_meta`, emission debug, mutation lineage, fallback fields, sanitizer/final gate traces. |
| Persistence | `game.api._complete_opening_turn_persistence_like_chat` and `game.storage` | Applies post-GM updates, interaction context updates, speaker adoption/invalidation, saves world/session/combat, and sets `session["campaign_started"] = True`. | Session debug traces and last action debug persist. |
| Logging | `game.storage.append_log` called by API tail | Builds canonical log entry with request, resolution, canonical GM object, log metadata, clue updates, response type contract, clock changes. | Log entry becomes replay/test input surface. |
| Response construction | `game.api._build_turn_response_payload` plus opening invariant handling | Builds response payload. For structured start, response `gm_output` is the canonical GM object and text invariants are asserted against log/canonical GM. | Response payload is a replay observation source. |
| Replay/evidence surfaces touched | Runtime modules write; test modules read later | Runtime emits trace, FEM, debug metadata, final text, log entry, session snapshot data. Protected replay later projects payload/snapshot into observation rows. | Runtime diagnostic projection may derive lineage events; protected replay projects protected fields from response/log/snapshot/FEM. |

## Replay Boundary Map

### Runtime Diagnostic Projection

Owner: `game.final_emission_replay_projection`

Owns:

- Read-side `fem_runtime_lineage_events` derivation from finalized FEM.
- Sealed replacement sub-kind projection.
- Runtime lineage event split fields such as selection owner, content owner, fallback kind, mutation kind, and source family.
- Diagnostic vocabulary for finalized final-emission metadata.

Does not own:

- Protected observation field paths.
- Golden replay acceptance schema.
- Replay pass/fail policy.
- Runtime fallback selection, output mutation, or write-time FEM stamping.

### Protected Replay Projection

Owners:

- `tests.helpers.golden_replay_projection`
- `tests.helpers.golden_replay_projection_fields`
- `tests.helpers.protected_replay_registry`
- `docs/testing/protected_replay_manifest.md`

Owns:

- `project_turn_observation`.
- `PROTECTED_OBSERVATION_FIELDS`.
- Structural and semantic protected drift buckets.
- Protected/supporting/advisory scenario identity through the registry and manifest.
- Read-side compatibility projection of a single observed `fallback_family`.

Does not own:

- Runtime lineage vocabulary.
- Runtime FEM write schema.
- Final emission behavior.
- Fallback content, selection, or provenance packaging.

### Governance Surfaces

Owners:

- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_authority.md`
- `tests/replay_governance_contract.py`
- `tests/replay_governance_registry.py`
- `tests/replay_governance_approval_contract.py`
- `tests/replay_governance_traceability_contract.py`

Owns:

- Governance decision vocabulary and records.
- Static governance decision mapping.
- Approval metadata shape.
- Governance traceability identifiers.
- Documentation of protected replay policy and generated protected field paths.

Does not own:

- Runtime execution.
- Replay runners.
- Failure classifiers.
- Dashboards.
- Threshold promotion unless explicitly reviewed in a future cycle.

### Advisory / Audit Tooling

Examples:

- `tools/run_protected_replay_trend.py`
- `tools/fallback_incidence_report.py`
- `tools/realization_provenance_audit.py`
- `tools/projection_drift_watch.py`
- Failure dashboard helpers and corrective locality reports

Owns:

- Report-only aggregation, diagnostics, trend windows, incidence counts, and audit artifacts.

Does not own:

- Runtime behavior.
- Protected acceptance schema.
- Governance vocabulary.
- Hidden pass/fail thresholds.

### Dependency Direction

Allowed direction:

```text
Runtime execution
  -> finalized GM/FEM/trace/log/session surfaces
  -> runtime diagnostic projection
  -> protected replay projection may consume diagnostics
  -> governance/advisory reports may read protected and diagnostic outputs
```

Forbidden direction:

```text
Runtime execution
  -> tests.helpers.golden_replay_projection
  -> protected replay acceptance fields
  -> governance registry / manifest
```

Protected replay may consume runtime diagnostics. Runtime should never depend on protected replay acceptance structures.

## Fallback Ownership Map

| Fallback path | Fallback content author | Fallback selector | Fallback applicator | Provenance packager | Final emission recorder | Replay observer | Intentional overlap |
|---|---|---|---|---|---|---|---|
| Upstream API fast fallback | `game.gm_retry` / diegetic fallback helpers via terminal retry fallback | `game.api._fast_fallback_for_upstream_error` | `game.api`, then final emission gate consumes candidate | `game.fallback_provenance_debug`; `game.realization_provenance` for family stamp | `game.final_emission_meta`, `game.final_emission_finalize`, gate/finalize metadata | Runtime: `game.final_emission_replay_projection`; protected: golden replay projection | API both selects and applies because upstream failure is runtime orchestration. Content and provenance remain separate. |
| Retry terminal fallback after validation failures | `game.gm_retry`, `game.diegetic_fallback_narration`, targeted fallback helpers | `game.api` retry loop via `choose_retry_strategy` and budget escape hatch | `game.api` swaps GM output before final emission | `game.realization_provenance`; retry producer metadata in FEM helpers | Final emission packages resulting source/fallback/mutation fields | Runtime lineage and protected replay read final FEM/log payload | Retry selection lives in API because retry budget and route state are runtime concerns. |
| Opening deterministic/prepared fallback | `game.opening_deterministic_fallback`, `game.upstream_response_repairs`, visible fact/realization helpers | API/upstream repair path prepares; final emission gate may select accepted prepared opening text | `game.final_emission_gate`/delegate finalizes; API tail preserves opening debug fields | Realization provenance and final emission metadata | `_complete_opening_turn_persistence_like_chat` copies opening debug to FEM when needed | Protected replay observes `opening_fallback_*` fields | Opening crosses bootstrap, prompt, fallback, gate, and payload invariants; overlap is structural rather than necessarily accidental. |
| Strict-social fallback | `game.social_exchange_emission` and related strict-social modules | Strict-social emission/gate path | Final emission gate/sanitizer path applies legal final text | FEM and gate metadata | Final emission metadata and sanitizer/gate traces | Runtime lineage projects split strict-social owner fields; protected replay observes speaker/source fields | Social fallback content and gate legality naturally overlap at the final emission boundary. |
| Sanitizer empty/strict-social fallback | `game.output_sanitizer` and strict-social fallback content owner where knowable | Sanitizer/final-emission boundary | Sanitizer and final-emission gate | Sanitizer trace plus FEM packaging | Final emission metadata | Runtime lineage reads sanitizer trace; protected replay observes sanitizer fallback fields | Sanitizer owns local emergency text only where candidate text is unusable; final emission records it. |
| Sealed final-emission fallback | Final-emission sealed fallback modules and specific layer owners | `game.final_emission_gate` layer orchestration | `game.final_emission_gate` / `game.final_emission_finalize` | FEM/finalize metadata | Final emission metadata, mutation lineage, sealed fallback owner buckets | Runtime lineage sealed sub-kind projection; protected replay selected protected fields | This is the clearest intentional final-emission overlap: legality enforcement may require sealed deterministic terminal replacement. |

Ownership boundaries intentionally overlap at the point where a fallback candidate becomes final player-facing text. The overlap is acceptable when:

- Content author is identifiable separately from selector/applicator.
- Provenance packaging records selector-boundary evidence rather than reselecting text.
- Final emission records and constrains the result without pretending to own all upstream semantics.
- Replay projection observes finalized fields without rewriting runtime ownership.

## Architectural Tension Classification

| Tension | Classification | Rationale | AR-AC implication |
|---|---|---|---|
| `game.api` breadth | Essential design with future cleanup candidates | It is the runtime spine for request entry, authoritative mutation, CTIR timing, GPT/retry orchestration, final-emission handoff, persistence, logging, and response payloads. That is coherent for a single turn transaction, but some helper extraction may reduce local pressure. | Do not split the spine blindly. Identify narrow delegate seams where ownership is already clear, especially preflight, persistence tail, and trace construction. |
| Final emission semantic pressure | Transitional design | Doctrine says final emission should converge toward legality and packaging, but current gate/finalize/repair layers still carry semantic repair and sealed fallback responsibilities. | Map which semantic repairs are still essential guardrails versus candidates to move upstream. |
| Opening-scene ownership | Essential design with transitional pressure | Opening crosses first-turn state, public scene facts, narrative planning, GPT prose, deterministic fallback, gate selection, persistence, and replay invariants. Split ownership is necessary, but the handoffs remain sensitive. | Keep the flow map as a guardrail. Consider only small clarifying docs/tests or delegate extraction if it reduces confusion. |
| Fallback ownership fanout | Transitional design | Content author, selector, applicator, packager, recorder, and replay observer are already distinct. Fanout is high because fallback is both runtime safety and evidence-bearing behavior. | AR-AC should preserve split-owner vocabulary while reducing duplicate field interpretation. |
| Runtime vs replay separation | Essential design | The AO5 split is correct. Runtime diagnostic projection and protected acceptance projection answer different questions and have allowed one-way dependency. | Protect the boundary. Any consolidation should be facade-level only and must not make runtime import test acceptance structures. |
| Evidence artifact fanout | Future cleanup candidate | Evidence is strong and useful, but replay, provenance, incidence, recurrence, mutation attribution, and governance artifacts create coordination cost. | Classify evidence surfaces as canonical, generated, or advisory before adding more reports. |
| Dual fallback-family vocabulary | Transitional design | Runtime has diegetic `fallback_family_used` and governed `realization_fallback_family`; protected replay projects one observed field for compatibility. | Do not collapse fields in runtime during AR-AC. Consider documenting read precedence near any future field consumer. |
| Protected replay consuming runtime lineage diagnostics | Essential design if one-way | Protected replay can use runtime lineage for diagnostics while excluding lineage owner mismatch from protected drift unless promoted later. | Keep dependency direction explicit in tests/docs. |
| Final emission replay projection import fanout | Future cleanup candidate | Runtime projection reads several ownership/metadata facades to build diagnostics. The fanout is acceptable but can become a magnet. | Prefer facade consolidation/read helpers over moving acceptance logic into runtime. |
| Opening fallback owner buckets in protected fields | Transitional design | Protected replay locks selected opening fallback owner/authorship/source observations while runtime still carries multiple opening fallback fields. | Keep protected projection as read-side compatibility. Avoid changing runtime write fields just to simplify protected rows. |

## Recommended Focus for AR-AC

1. **Runtime-spine pressure map for `game.api`**  
   Identify which parts are essential transaction orchestration and which are extractable delegates. Prioritize low-risk delegate boundaries already implied by code: preflight response construction, opening persistence tail helpers, and trace/log assembly.

2. **Final-emission semantic pressure audit**  
   Separate final-emission legality/packaging from semantic repair/fallback behavior. Classify each remaining repair as essential guardrail, upstream-movable, or sealed fallback exception.

3. **Fallback field consumer inventory**  
   Trace who reads `fallback_family_used`, `realization_fallback_family`, `fallback_owner_bucket`, `fallback_content_owner`, `fallback_selection_owner`, and provenance trace fields. Goal: reduce duplicate interpretation, not collapse the fields.

4. **Replay/evidence canonicality pass**  
   Label replay and evidence surfaces as canonical acceptance, runtime diagnostic, governance-only, generated, or advisory. This should prevent future cycles from adding new reports where an existing canonical surface already answers the question.

5. **Opening-scene handoff checklist**  
   Preserve the current split: narrative planning owns structural obligation; opening realization owns public diegetic basis; fallback modules author deterministic backup; final emission selects/packages; API persists and logs canonical output.

## Validation Notes

This cycle made no implementation changes. The deliverable is this documentation file only.

Lightweight validation target:

- Check `git status --short` after writing this file.
- Confirm the only AR-AB change is `AR-AB_runtime_authority_and_replay_boundary_map.md`; pre-existing untracked discovery docs should remain untouched.
