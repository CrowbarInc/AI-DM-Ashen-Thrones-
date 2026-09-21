# AR-BA Concept Inventory and Responsibility Discovery

Date: 2026-07-15

Scope: Campaign 3, Cycle 1 discovery report for architectural concepts and responsibility boundaries.

Inputs: repository documentation, runtime modules, governance tests, protected replay helpers, and representative test suites. This report does not modify runtime behavior, rename concepts, classify removals, or reopen Campaign 2's final-vision compatibility conclusion.

Naming note: `AR-BA` is the requested identifier and does not conflict with the active root-level Architecture Reconciliation sequence. The prior sequence ends at `AR-AI_final_vision_compatibility_closeout.md`.

## 1. Executive Summary

This cycle identified 23 major architectural concepts: runtime transaction, state authority, ownership, routing, domain simulation, CTIR, prompt/adaptation, GPT/model realization, opening realization, final emission, replay, projection, provenance, evidence, fallback, validators, repairs, sanitizers, diagnostics, telemetry/lineage, governance, canonicality, and compatibility residue.

The best-defined concepts are state authority, CTIR, final emission, replay/protected replay, governance, realization provenance, and validation-layer separation. They have explicit doctrine, owner modules, and direct-owner tests. The most ambiguous concepts are evidence versus diagnostics, provenance versus evidence, fallback versus repair, repair versus sanitization, and compatibility residue versus historical architecture. These are not necessarily duplicates; they are high-pressure boundaries with several valid axes.

The strongest apparent overlap is the final-emission/fallback/repair/sanitizer cluster. Repository evidence says the overlap is partly intentional and partly transitional: final emission owns last-mile legality and packaging, while several semantic repairs are documented as convergence targets rather than permanent boundary behavior (`docs/architecture_ownership_ledger.md:106`, `docs/architecture_ownership_ledger.md:108`, `docs/final_emission_ownership_convergence.md:21`).

Clearly transitional or historical candidates include final-emission semantic repair pressure, legacy diegetic fallback classification, CTIR-absent prompt compatibility reads, dual fallback-family vocabulary, opening fallback compatibility fields, and advisory/generated evidence artifact fanout. Evidence is sufficient to begin a classification cycle, but not sufficient for removal recommendations. The next cycle should focus on Validation, Repair, Sanitization, and Fallback Reconciliation because that cluster has the highest ambiguity and the most direct player-facing risk.

## 2. Source and Evidence Register

| File | Type | Status | Concepts Covered | Why It Matters |
| ---- | ---- | ------ | ---------------- | -------------- |
| `AR-AA_architectural_mapping_discovery.md` | Architecture analysis | Historical/current reference | API spine, state authority, CTIR, replay, evidence, fallback, realization, final emission | Broad original map with concept headings and tension list (`AR-AA_architectural_mapping_discovery.md:23`, `AR-AA_architectural_mapping_discovery.md:1024`). |
| `AR-AB_runtime_authority_and_replay_boundary_map.md` | Architecture analysis | Current reference | Runtime authority, replay, fallback, projection, governance | Maps runtime authority and explicitly separates runtime diagnostic projection from protected replay projection (`AR-AB_runtime_authority_and_replay_boundary_map.md:59`, `AR-AB_runtime_authority_and_replay_boundary_map.md:151`). |
| `AR-AC_architectural_ownership_reconciliation.md` | Architecture analysis | Current reference | Ownership, layer model, transitional dependencies | Defines architectural layers and permanent/transitional ownership review (`AR-AC_architectural_ownership_reconciliation.md:43`, `AR-AC_architectural_ownership_reconciliation.md:327`). |
| `AR-AD_target_architecture_doctrine.md` | Normative doctrine | Current | Target architecture, ownership, replay/evidence, governance, canonicality | Most explicit doctrine: runtime truth before narration, one-way replay dependency, evidence not behavior, governance not gameplay (`AR-AD_target_architecture_doctrine.md:31`, `AR-AD_target_architecture_doctrine.md:61`, `AR-AD_target_architecture_doctrine.md:65`, `AR-AD_target_architecture_doctrine.md:69`). |
| `AR-AE_architecture_conformance_assessment.md` | Architecture analysis | Current | Conformance, drift, transitional responsibility | Assesses whether implementation aligns with doctrine and flags generated/advisory artifact authority risk (`AR-AE_architecture_conformance_assessment.md:24`, `AR-AE_architecture_conformance_assessment.md:85`). |
| `AR-AF_architecture_reconciliation_synthesis.md` | Closeout/baseline | Current | Campaign 1 baseline, invariants, durable references | Concise baseline and invariant list for future cycles (`AR-AF_architecture_reconciliation_synthesis.md:29`, `AR-AF_architecture_reconciliation_synthesis.md:135`). |
| `AR-AG_final_vision_compatibility_discovery.md` | Architecture analysis | Current | Vision compatibility, provenance, explainability | Documents player trust/provenance/explainability and review inputs (`AR-AG_final_vision_compatibility_discovery.md:108`, `AR-AG_final_vision_compatibility_discovery.md:493`). |
| `AR-AH_final_vision_compatibility_assessment.md` | Architecture analysis | Current | Compatibility classification, implementation dependencies | Confirms local refinement rather than broad redesign (`AR-AH_final_vision_compatibility_assessment.md:8`, `AR-AH_final_vision_compatibility_assessment.md:469`). |
| `AR-AI_final_vision_compatibility_closeout.md` | Closeout | Current | Campaign 2 closeout, next work, invariants | Says broad architecture is compatible and remaining work is bounded (`AR-AI_final_vision_compatibility_closeout.md:8`, `AR-AI_final_vision_compatibility_closeout.md:227`). |
| `docs/architecture_ownership_ledger.md` | Ownership model | Current | Ownership, CTIR, final emission, repairs, governance, compatibility residue | Repo-facing declaration of ambiguous seam ownership (`docs/architecture_ownership_ledger.md:1`, `docs/architecture_ownership_ledger.md:23`, `docs/architecture_ownership_ledger.md:79`). |
| `docs/final_emission_ownership_convergence.md` | Normative/target doctrine | Current | Final emission, validators, repair, semantic mutation | Classifies what belongs at final emission versus upstream after convergence (`docs/final_emission_ownership_convergence.md:1`, `docs/final_emission_ownership_convergence.md:21`). |
| `docs/validation_layer_separation_block_b_residue.md` | Operational documentation | Current | Validation, diagnostics, residue | States tolerated compatibility-shaped seams and warns that gate file split is not duplicate ownership (`docs/validation_layer_separation_block_b_residue.md:3`, `docs/validation_layer_separation_block_b_residue.md:22`). |
| `docs/testing/protected_replay_manifest.md` | Normative governance | Current | Protected replay, protected fields, scenario status | Canonical protected replay policy; no deprecated scenarios declared (`docs/testing/protected_replay_manifest.md:391`). |
| `docs/testing/replay_governance_authority.md` | Normative governance | Current | Replay governance, authority hierarchy | Separates replay governance from replay execution, classification, diagnostics, dashboards, and thresholds (`docs/testing/replay_governance_authority.md:5`, `docs/testing/replay_governance_authority.md:12`, `docs/testing/replay_governance_authority.md:35`). |
| `docs/architecture_audit_readme.md` | Operational documentation | Current | Audit evidence, ownership mismatch interpretation, sediment layers | Explains how audit output should be interpreted and warns that ownership declarations are not proof code is clean (`docs/architecture_audit_readme.md:10`, `docs/architecture_audit_readme.md:39`, `docs/architecture_audit_readme.md:183`). |
| `game/state_authority.py` | Runtime/governance implementation | Current | State authority, ownership, read/write guards | Registry of state domains and mutation/read guards (`game/state_authority.py:1`, `game/state_authority.py:47`, `game/state_authority.py:52`). |
| `game/realization_authority.py` | Governance implementation | Current | Realization authority, fallback families, provenance requirements | Defines authority profiles and fallback-family ownership (`game/realization_authority.py:1`, `game/realization_authority.py:27`, `game/realization_authority.py:39`). |
| `game/realization_provenance.py` | Runtime implementation | Current | Provenance, fallback-family stamps | Stamps governed `realization_fallback_family` separately from diegetic fallback family (`game/realization_provenance.py:1`, `game/realization_provenance.py:3`, `game/realization_provenance.py:35`). |
| `game/fallback_provenance_debug.py` | Runtime implementation | Current with historical name | Fallback provenance, diagnostics, containment | Stable provenance owner despite debug name; does not select fallback prose or routing (`game/fallback_provenance_debug.py:1`, `game/fallback_provenance_debug.py:3`, `game/fallback_provenance_debug.py:71`). |
| `game/final_emission_replay_projection.py` | Runtime diagnostic projection | Current | Projection, lineage, diagnostics, replay adapters | Read-side runtime projection from finalized FEM; distinguishes selection/content owners (`game/final_emission_replay_projection.py:436`, `game/final_emission_replay_projection.py:774`, `game/final_emission_replay_projection.py:866`). |
| `game/final_emission_gate.py` | Runtime implementation | Current | Final emission, validators, repair, sanitizer integration | Orchestrates final player-facing legality and packaging; direct tests define ordering. |
| `game/final_emission_validators.py` | Runtime implementation | Current | Validators | Pure predicate/check layer used by gate and direct-owner tests. |
| `game/final_emission_repairs.py` | Runtime implementation | Current/transitional pressure | Repair | Runtime repair orchestration home but semantic mutation is transitional (`docs/architecture_ownership_ledger.md:125`, `docs/architecture_ownership_ledger.md:127`). |
| `game/output_sanitizer.py` | Runtime implementation | Current | Sanitizers | Last-mile text cleanup and strip-only behavior, tested by convergence and sanitizer suites (`tests/test_final_emission_boundary_convergence.py:130`, `tests/test_final_emission_boundary_convergence.py:394`). |
| `game/ctir.py`, `game/ctir_runtime.py` | Runtime implementation | Current | CTIR, lifecycle | Resolved-turn meaning object and runtime attachment lifecycle; docs say prompt is not semantic co-owner (`docs/architecture_ownership_ledger.md:79`, `docs/architecture_ownership_ledger.md:87`). |
| `tests/test_state_authority.py` | Test | Current direct-owner | State authority | Direct-owner tests for registry, mutation guards, read matrix (`tests/test_state_authority.py:1`, `tests/test_state_authority.py:44`, `tests/test_state_authority.py:87`, `tests/test_state_authority.py:105`). |
| `tests/test_replay_boundary_governance.py` | Test | Current governance | Replay/projection boundary | Locks replay/projection separation and protected manifest parity (`tests/test_replay_boundary_governance.py:1`, `tests/test_replay_boundary_governance.py:96`). |
| `tests/test_final_emission_boundary_convergence.py` | Test | Current direct-owner/convergence | Final emission, repair, sanitizer, upstream prepared repair | Locks no semantic boundary synthesis, strip-only sanitizer, and upstream prepared attribution (`tests/test_final_emission_boundary_convergence.py:1`, `tests/test_final_emission_boundary_convergence.py:46`, `tests/test_final_emission_boundary_convergence.py:103`, `tests/test_final_emission_boundary_convergence.py:151`). |
| `tests/test_fallback_behavior_gate.py` | Test | Current downstream owner | Fallback behavior through gate | Explicitly says it owns gate ordering/application, not validator/repair semantics (`tests/test_fallback_behavior_gate.py:1`, `tests/test_fallback_behavior_gate.py:15`, `tests/test_fallback_behavior_gate.py:178`). |

## 3. Concept Inventory

### Concept: Runtime Transaction

**Working definition:** The single-turn execution spine for start, chat, and action flows.

**Alternative terminology:** API spine, transaction spine, runtime orchestration, turn pipeline.

**Primary architectural responsibility:** Preserve ordering from request entry through authoritative mutation, CTIR placement, GPT/retry/fallback, final emission, persistence, logging, and response construction.

**Lifecycle position:** Whole turn lifecycle.

**Authority and ownership relationship:** `game.api` owns transaction order; domain modules own simulation truth; storage owns persistence mechanics.

**Primary producers:** API routes, request handlers, domain resolution helpers.

**Primary consumers:** Prompt construction, final emission, persistence, response payload, replay inputs.

**Inputs and outputs:** Requests and runtime state in; finalized GM/FEM/log/session/response surfaces out.

**Protected invariants:** Explicit: one turn has one runtime transaction spine (`AR-AF_architecture_reconciliation_synthesis.md:29`, `AR-AF_architecture_reconciliation_synthesis.md:139`). Inferred: CTIR must be built after mutation and before narration.

**Failure modes addressed:** Split transaction authority, stale CTIR, persistence before finalization, replay observing partial output.

**Implementation evidence:** `game/api.py`; `AR-AB_runtime_authority_and_replay_boundary_map.md:37` flow map.

**Test evidence:** API and pipeline tests, plus governance tests that prevent replay/gate imports from re-owning runtime behavior.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:14`, `AR-AF_architecture_reconciliation_synthesis.md:29`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Which helper seams can be extracted later without weakening the single transaction spine?

### Concept: State Authority

**Working definition:** A registry and guard vocabulary for non-overlapping state domains, mutation permissions, read relationships, and cross-domain write exceptions.

**Alternative terminology:** Unified state authority model, state-domain registry, mutation guard.

**Primary architectural responsibility:** Prevent unauthorized state mutation and clarify which modules may mutate which domain.

**Lifecycle position:** Runtime mutation and governance checks.

**Authority and ownership relationship:** `game.state_authority` owns registry and guards, not persistence or universal mutation.

**Primary producers:** State authority registry definitions.

**Primary consumers:** Domain modules and tests that call mutation/read guards.

**Inputs and outputs:** Domain id, owner module, operation; guard pass/fail or `StateAuthorityError`.

**Protected invariants:** Explicit: GPT may not mutate state and wrong modules cannot mutate domains (`tests/test_state_authority.py:52`, `tests/test_state_authority.py:96`). Explicit: read matrix controls cross-domain reads (`tests/test_state_authority.py:105`).

**Failure modes addressed:** Hidden owner mutation, pseudo-owner mutation, cross-domain writes without allowlist.

**Implementation evidence:** `game/state_authority.py:1`, `game/state_authority.py:47`, `game/state_authority.py:52`.

**Test evidence:** `tests/test_state_authority.py:44`, `tests/test_state_authority.py:87`, `tests/test_state_authority.py:124`.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:73`, `docs/architecture_ownership_ledger.md:182`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Whether future feature domains need additional domain ids or only feature-local contracts.

### Concept: Ownership

**Working definition:** The repo-facing assignment of runtime, direct-owner test, downstream, compatibility, and governance responsibilities for ambiguous seams.

**Alternative terminology:** Owner ledger, direct-owner suite, canonical owner, split-owner matrix.

**Primary architectural responsibility:** Localize responsibility and prevent downstream tests or compatibility paths from becoming rival semantic owners.

**Lifecycle position:** Governance, test placement, architectural review.

**Authority and ownership relationship:** `docs/architecture_ownership_ledger.md` is a governance contract; implementation remains runtime behavior.

**Primary producers:** Ownership ledger, test inventory, governance tests.

**Primary consumers:** Developers, audit tools, test placement guards.

**Inputs and outputs:** Concern names and owner declarations; review guidance and drift-watch expectations.

**Protected invariants:** Explicit: governance declarations do not prove code is clean (`docs/architecture_audit_readme.md:39`); compatibility residue must not reopen co-equal ownership (`docs/architecture_ownership_ledger.md:29`).

**Failure modes addressed:** Ownership smear, test magnet growth, treating support paths as semantic homes.

**Implementation evidence:** `docs/architecture_ownership_ledger.md:23`, `tests/test_gate_boundary_governance.py`, `tests/test_ownership_registry.py`.

**Test evidence:** `tests/test_fallback_behavior_gate.py:15` separates gate coverage from validator/repair semantics.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:432`, `docs/architecture_ownership_ledger.md:1`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Which advisory/generated artifacts should receive canonicality labels for external handoff?

### Concept: Authority

**Working definition:** The permission to decide, mutate, select, realize, or package a value within a specific layer or boundary.

**Alternative terminology:** Runtime authority, realization authority, replay authority, state authority.

**Primary architectural responsibility:** Separate who is allowed to decide behavior from who records, adapts, diagnoses, or observes it.

**Lifecycle position:** Runtime, realization/fallback, replay/governance.

**Authority and ownership relationship:** Authority varies by domain; it is not equivalent to ownership. Example: `game.fallback_provenance_debug` owns provenance packaging but not fallback selection (`game/fallback_provenance_debug.py:3`, `game/fallback_provenance_debug.py:5`).

**Primary producers:** Authority ledgers, profiles, runtime owners.

**Primary consumers:** Runtime modules, tests, governance audits.

**Inputs and outputs:** Owner/profile/fallback family ids; allowed/forbidden authority and metadata requirements.

**Protected invariants:** Explicit: GPT owns expression, not truth (`AR-AD_target_architecture_doctrine.md:49`); governance is not gameplay (`AR-AD_target_architecture_doctrine.md:69`).

**Failure modes addressed:** GPT-derived truth, replay-driven runtime behavior, provenance packagers selecting behavior.

**Implementation evidence:** `game/realization_authority.py:1`, `game/realization_authority.py:27`, `game/realization_authority.py:39`.

**Test evidence:** `tests/test_realization_authority.py`, `tests/test_state_authority.py`.

**Documentation evidence:** `AR-AA_architectural_mapping_discovery.md:546`, `AR-AB_runtime_authority_and_replay_boundary_map.md:23`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Whether "authority" should receive a durable glossary page because it spans several ledgers.

### Concept: Routing

**Working definition:** The selection of path, model route, interaction route, or legality path without necessarily owning domain truth.

**Alternative terminology:** Dispatch, route metadata, model routing, interaction routing, final route.

**Primary architectural responsibility:** Choose execution paths while preserving separate truth, expression, and legality responsibilities.

**Lifecycle position:** Pre-GPT model path, social/interaction path, retry/fallback route, final-emission route.

**Authority and ownership relationship:** Routing may be owned by API/model routing/final emission depending on layer; it is distinct from authority over state truth.

**Primary producers:** `game.model_routing`, `game.interaction_routing`, API route decisions, final-emission route metadata.

**Primary consumers:** GPT call layer, retry/fallback, final emission, replay projection.

**Inputs and outputs:** Intent/route context and route metadata; final route fields.

**Protected invariants:** Strongly inferred: route metadata must not become state truth. Explicit in doctrine: model routing owns model I/O and route metadata, not game truth (`AR-AD_target_architecture_doctrine.md:49`).

**Failure modes addressed:** Route selection reinterpreting authoritative outcomes, hidden route-driven state mutation.

**Implementation evidence:** `game/model_routing.py`, `game/interaction_routing.py`, `game/final_emission_replay_projection.py:827`.

**Test evidence:** `tests/test_model_routing_runtime.py`, `tests/test_dialogue_routing_lock.py`, `tests/test_cf1_route_and_trace_precedence.py`.

**Documentation evidence:** `AR-AA_architectural_mapping_discovery.md:269`, `AR-AI_final_vision_compatibility_closeout.md:54`.

**Current conceptual status:** Likely permanent candidate.

**Open questions:** Where routing ends and dispatch begins is not consistently documented.

### Concept: Domain Simulation

**Working definition:** Authoritative gameplay resolution and state transition semantics owned by domain modules before narration.

**Alternative terminology:** Domain truth, engine resolution, simulation outcome.

**Primary architectural responsibility:** Establish runtime truth before narration.

**Lifecycle position:** After request normalization and before CTIR/prompt/GPT.

**Authority and ownership relationship:** Domain modules own simulation outcomes; `game.api` orchestrates transaction timing.

**Primary producers:** `game.noncombat_resolution`, `game.exploration`, `game.social`, `game.combat`, `game.world_progression`, related modules.

**Primary consumers:** CTIR, prompt context, final emission, persistence, replay.

**Inputs and outputs:** Player intent and current state; resolution data and authoritative state updates.

**Protected invariants:** Explicit: runtime truth before narration (`AR-AD_target_architecture_doctrine.md:33`, `AR-AF_architecture_reconciliation_synthesis.md:139`).

**Failure modes addressed:** GPT creating state truth, prompt reconstruction replacing domain resolution.

**Implementation evidence:** Domain modules and API pipeline.

**Test evidence:** `tests/test_world_simulation_backbone_ownership.py`, `tests/test_noncombat_consumption` families, state authority tests.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:191`, `AR-AF_architecture_reconciliation_synthesis.md:49`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Which future feature domains need explicit feature-local contracts before implementation?

### Concept: CTIR

**Working definition:** A bounded, retry-stable resolved-turn meaning object for narration after authoritative mutation.

**Alternative terminology:** Resolved-turn meaning, CTIR runtime attachment, CTIR narration bundle.

**Primary architectural responsibility:** Carry resolved turn meaning into narration without letting prompt construction re-decide semantics.

**Lifecycle position:** After domain mutation/hygiene and before prompt construction/GPT.

**Authority and ownership relationship:** `game.ctir` owns shape; `game.ctir_runtime` owns attachment helpers; `game.api` owns lifecycle placement.

**Primary producers:** CTIR builders called by API after mutation.

**Primary consumers:** Prompt context, narration plan bundle, tests, later replay-visible effects.

**Inputs and outputs:** Resolution/state slices; session-attached CTIR and prompt-adapter data.

**Protected invariants:** Explicit: prompt context is not second semantic authority when CTIR exists (`docs/architecture_ownership_ledger.md:89`). Explicit: CTIR absent fallback reads are compatibility residue (`docs/architecture_ownership_ledger.md:87`).

**Failure modes addressed:** Prompt/pipeline reconstructing turn truth, stale CTIR, retry instability.

**Implementation evidence:** `game/ctir.py`, `game/ctir_runtime.py`.

**Test evidence:** `tests/test_ctir_runtime_lifecycle.py`, `tests/test_prompt_context_ctir_boundary.py`, `tests/test_ctir_retry_stability.py`.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:43`, `docs/architecture_ownership_ledger.md:79`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Retirement condition for CTIR-absent prompt compatibility reads.

### Concept: Prompt/Adaptation

**Working definition:** The layer that packages CTIR, visibility, response policy, narrative plans, and read models into model context.

**Alternative terminology:** Prompt context, prompt adapter, narration plan bundle.

**Primary architectural responsibility:** Adapt approved state and CTIR into GPT context without owning authoritative game outcomes.

**Lifecycle position:** Between CTIR and GPT/model call.

**Authority and ownership relationship:** Prompt context owns context assembly; CTIR/domain modules own meaning/truth.

**Primary producers:** `game.prompt_context`, `game.narration_plan_bundle`, related projection helpers.

**Primary consumers:** GPT/model layer.

**Inputs and outputs:** Runtime state/CTIR/contracts; message payloads/context.

**Protected invariants:** Explicit: prompt construction adapts CTIR and approved read models; it does not recreate turn truth (`AR-AF_architecture_reconciliation_synthesis.md:145`).

**Failure modes addressed:** Prompt-owned truth, stale compatibility reads becoming co-owner semantics.

**Implementation evidence:** `game/prompt_context.py`, `game/prompt_context_leads.py`.

**Test evidence:** `tests/test_prompt_context_ctir_boundary.py`, `tests/test_prompt_context_ctir_consumption.py`, `tests/test_build_messages_projection.py`.

**Documentation evidence:** `docs/architecture_ownership_ledger.md:64`, `docs/architecture_ownership_ledger.md:79`.

**Current conceptual status:** Likely permanent candidate, with transitional compatibility residue.

**Open questions:** Which prompt fallback reads remain necessary once CTIR is reliably present?

### Concept: Realization

**Working definition:** Turning already-authorized planner/CTIR content into player-facing or candidate prose while preserving truth/authority boundaries.

**Alternative terminology:** Narrative realization, prompt realization, opening realization, GPT realization.

**Primary architectural responsibility:** Separate expression from truth and from fallback/provenance legality.

**Lifecycle position:** Prompt/GPT/opening/fallback generation stages before final emission.

**Authority and ownership relationship:** `game.realization_authority` defines profiles; GPT may phrase but not create truth; specific fallback families have owners and provenance requirements.

**Primary producers:** GPT, opening realization helpers, upstream prepared emission, deterministic fallback modules.

**Primary consumers:** Final emission, provenance packagers, replay projection.

**Inputs and outputs:** Authorized content obligations and visible anchors; candidate prose plus metadata.

**Protected invariants:** Explicit: GPT may turn supplied Planner/CTIR contracts into prose but not truth/state/consequences/fallback semantics (`game/realization_authority.py:119`). Explicit: fallback families require provenance (`game/realization_authority.py:39`).

**Failure modes addressed:** GPT inventing facts, fallback prose masquerading as plan-backed narration, boundary repair writing new semantic content.

**Implementation evidence:** `game/realization_authority.py:1`, `game/opening_scene_realization.py`, `game/upstream_response_repairs.py`.

**Test evidence:** `tests/test_realization_authority.py`, `tests/test_opening_scene_realization.py`, `tests/test_upstream_response_repairs.py`.

**Documentation evidence:** `AR-AA_architectural_mapping_discovery.md:598`, `AR-AD_target_architecture_doctrine.md:233`.

**Current conceptual status:** Clearly permanent candidate, with legacy fallback family transitional.

**Open questions:** Whether "realization" and "generation" need glossary distinction in durable docs.

### Concept: Final Emission

**Working definition:** Last-mile legality, selection, packaging, metadata/FEM, and sealed terminal exception boundary for final player-facing text.

**Alternative terminology:** Final player-facing emission, emission gate, FEM packaging, terminal pipeline.

**Primary architectural responsibility:** Ensure shipped text is legal, packaged, traceable, and consistent with upstream authorized meaning.

**Lifecycle position:** After GPT/retry/fallback candidate and before persistence/log/response.

**Authority and ownership relationship:** Gate owns orchestration/selection; validators/repairs/sanitizer/meta are layer components; semantic synthesis at this boundary is transitional unless sealed.

**Primary producers:** `game.final_emission_runtime`, `game.final_emission_gate`, `game.final_emission_finalize`, `game.final_emission_meta`.

**Primary consumers:** Persistence, replay projection, response payload, tests.

**Inputs and outputs:** Candidate/prepared/fallback GM output; finalized text, FEM, debug lanes.

**Protected invariants:** Explicit: final emission owns final selection, legality, packaging, FEM, sealed terminal exceptions (`AR-AF_architecture_reconciliation_synthesis.md:149`). Explicit: semantic repair at boundary is convergence pressure (`docs/architecture_ownership_ledger.md:108`).

**Failure modes addressed:** Malformed or illegal player text, silent semantic repair, untraceable fallback selection.

**Implementation evidence:** `game/final_emission_gate.py`, `game/final_emission_runtime.py`, `game/final_emission_finalize.py`, `game/final_emission_meta.py`.

**Test evidence:** `tests/test_final_emission_gate_orchestration_order.py`, `tests/test_final_emission_boundary_convergence.py:151`, `tests/test_final_emission_meta.py`.

**Documentation evidence:** `docs/final_emission_ownership_convergence.md:21`, `AR-AD_target_architecture_doctrine.md:275`.

**Current conceptual status:** Clearly permanent candidate, with transitional semantic repair responsibilities.

**Open questions:** Which repair flags remain essential guardrails and which should move upstream?

### Concept: Replay

**Working definition:** Deterministic/protected observation of runtime outputs through golden replay, protected fields, registries, and manifests.

**Alternative terminology:** Golden replay, protected replay, replay acceptance, replay governance.

**Primary architectural responsibility:** Detect drift and preserve acceptance observations without governing runtime behavior.

**Lifecycle position:** Post-runtime test/evidence pipeline.

**Authority and ownership relationship:** Runtime emits; runtime projection diagnoses; protected replay consumes observations; governance declares policy.

**Primary producers:** Runtime response/log/session/FEM outputs and golden replay fixtures.

**Primary consumers:** Protected replay projection, governance tests, drift reports.

**Inputs and outputs:** Turn payloads/snapshots/logs; observation rows, protected fields, drift classifications.

**Protected invariants:** Explicit: replay dependency flows from runtime outputs toward evidence, never back into runtime (`AR-AF_architecture_reconciliation_synthesis.md:151`). Test-enforced: runtime and acceptance projection modules remain separate (`tests/test_replay_boundary_governance.py:96`).

**Failure modes addressed:** Runtime importing test acceptance schema, protected fields becoming runtime policy, hidden replay pass/fail thresholds.

**Implementation evidence:** `tests/helpers/golden_replay_projection.py`, protected replay helpers.

**Test evidence:** `tests/test_replay_boundary_governance.py:63`, `tests/test_replay_boundary_governance.py:96`, golden replay suites.

**Documentation evidence:** `docs/testing/protected_replay_manifest.md`, `docs/testing/replay_governance_authority.md:12`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Which advisory replay reports are canonical enough for external review?

### Concept: Projection

**Working definition:** Read-side transformation of runtime outputs into diagnostic or acceptance observations.

**Alternative terminology:** Runtime diagnostic projection, protected acceptance projection, CTIR/progression projection.

**Primary architectural responsibility:** Let downstream tools inspect runtime evidence without mutating behavior or redefining ownership.

**Lifecycle position:** After runtime finalization or as read-only prompt/CTIR adapters.

**Authority and ownership relationship:** Runtime diagnostic projection (`game.final_emission_replay_projection`) is separate from protected replay acceptance projection (`tests.helpers.golden_replay_projection`).

**Primary producers:** Projection modules.

**Primary consumers:** Replay, diagnostics, tests, reports.

**Inputs and outputs:** FEM/payload/session/log; normalized projection rows/events.

**Protected invariants:** Explicit: runtime diagnostic projection and protected replay acceptance remain separate (`AR-AF_architecture_reconciliation_synthesis.md:150`). Test-enforced "do not merge" docstrings and module identities (`tests/test_replay_boundary_governance.py:101`).

**Failure modes addressed:** Acceptance schema leaking into runtime, diagnostic projection becoming behavior owner.

**Implementation evidence:** `game/final_emission_replay_projection.py:774`, `game/final_emission_replay_projection.py:869`.

**Test evidence:** `tests/test_replay_boundary_governance.py:96`, `tests/test_golden_replay_projection.py`.

**Documentation evidence:** `AR-AB_runtime_authority_and_replay_boundary_map.md:59`, `AR-AF_architecture_reconciliation_synthesis.md:79`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Whether all projection types use consistent naming for diagnostic versus acceptance surfaces.

### Concept: Provenance

**Working definition:** Write-time or read-side metadata that records where a result, fallback, realization, or mutation came from and which owner/stage produced it.

**Alternative terminology:** Realization provenance, fallback provenance, attribution, lineage, origin.

**Primary architectural responsibility:** Make behavior traceable without owning behavior.

**Lifecycle position:** During fallback/realization selection and final-emission packaging; later read by diagnostics/replay.

**Authority and ownership relationship:** Provenance packagers are not necessarily selectors or content authors. `fallback_provenance_debug` explicitly does not select fallback prose or routing (`game/fallback_provenance_debug.py:5`).

**Primary producers:** `game.realization_provenance`, `game.fallback_provenance_debug`, final-emission meta helpers.

**Primary consumers:** FEM, runtime lineage projection, protected replay projection, audits.

**Inputs and outputs:** Family ids, owner/stage/source metadata; FEM provenance fields.

**Protected invariants:** Explicit: provenance explains behavior without owning behavior (`AR-AF_architecture_reconciliation_synthesis.md:152`). Explicit: realization fallback family stamped independently from diegetic fallback family (`game/realization_provenance.py:3`).

**Failure modes addressed:** Untraceable fallbacks, overwrites without containment, provenance fields misread as selectors.

**Implementation evidence:** `game/realization_provenance.py:35`, `game/fallback_provenance_debug.py:71`.

**Test evidence:** `tests/test_realization_provenance.py`, `tests/test_fallback_overwrite_containment.py`, `tests/test_final_emission_boundary_convergence.py:464`.

**Documentation evidence:** `AR-AA_architectural_mapping_discovery.md:969`, `AR-AI_final_vision_compatibility_closeout.md:104`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Whether provenance, evidence, and diagnostics need a shared data-model glossary.

### Concept: Evidence

**Working definition:** Runtime outputs, logs, snapshots, FEM, protected observations, governance records, generated reports, and advisory artifacts used to support inspection or acceptance.

**Alternative terminology:** Evidence surfaces, artifacts, reports, audit outputs, diagnostics.

**Primary architectural responsibility:** Support confidence, review, replay, and handoff without automatically becoming runtime authority.

**Lifecycle position:** Runtime output and post-runtime governance/reporting.

**Authority and ownership relationship:** Evidence can be runtime truth, governance contract, protected acceptance, generated artifact, or advisory artifact depending on canonicality.

**Primary producers:** Runtime, replay, audit/report tools, governance docs.

**Primary consumers:** Developers, tests, external reviewers, future classification cycles.

**Inputs and outputs:** Runtime observations and analysis; reports and evidence maps.

**Protected invariants:** Explicit: evidence does not automatically own behavior (`AR-AD_target_architecture_doctrine.md:65`). Explicit: generated/advisory artifacts require promotion before authority (`AR-AF_architecture_reconciliation_synthesis.md:153`).

**Failure modes addressed:** Advisory reports becoming hidden policy, generated artifacts mistaken for protected acceptance.

**Implementation evidence:** Tools and reports; runtime output surfaces.

**Test evidence:** `tests/test_golden_replay_artifact_manifest.py`, `tests/test_cf6_generated_projection_artifact_governance.py`.

**Documentation evidence:** `AR-AF_architecture_reconciliation_synthesis.md:100`, `AR-AD_target_architecture_doctrine.md:458`.

**Current conceptual status:** Likely permanent candidate, with artifact fanout transitional/unclear.

**Open questions:** Which evidence surfaces should be required, strongly recommended, or optional for future external review?

### Concept: Fallback

**Working definition:** Bounded substitute behavior used when upstream/model/candidate/legality conditions fail, with separate content, selection, application, provenance, recording, and observation axes.

**Alternative terminology:** Retry terminal fallback, upstream fast fallback, deterministic fallback, sealed fallback, opening fallback, strict-social fallback.

**Primary architectural responsibility:** Preserve safe player-facing continuity under failure while making the failure path observable.

**Lifecycle position:** GPT/retry path, upstream error handling, final-emission gate, sanitizer emergency path, opening bootstrap.

**Authority and ownership relationship:** Multi-axis: content author, selector/applicator, provenance packager, final recorder, runtime projection, protected replay owner may differ (`AR-AB_runtime_authority_and_replay_boundary_map.md:174`).

**Primary producers:** API fallback selection, `gm_retry`, deterministic fallback modules, strict-social modules, sanitizer, final-emission sealed paths.

**Primary consumers:** Final emission, provenance, replay projection, protected replay.

**Inputs and outputs:** Failure conditions and context; fallback candidate/final text plus metadata.

**Protected invariants:** Explicit: retry/fallback ownership is multi-axis by design (`AR-AF_architecture_reconciliation_synthesis.md:147`). Explicit: fallback family owner/provenance is registered in realization authority (`game/realization_authority.py:275`, `game/realization_authority.py:315`, `game/realization_authority.py:328`).

**Failure modes addressed:** No response under upstream failure, unsafe invented certainty, hidden fallback authorship, fallback overwriting selected text.

**Implementation evidence:** `game/gm_retry.py`, `game/diegetic_fallback_narration.py`, `game/opening_deterministic_fallback.py`, `game/fallback_provenance_debug.py`.

**Test evidence:** `tests/test_fallback_behavior_gate.py`, `tests/test_fallback_continuity_guard.py`, `tests/test_fallback_overwrite_containment.py`, golden replay fallback projection suites.

**Documentation evidence:** `AR-AB_runtime_authority_and_replay_boundary_map.md:174`, `docs/architecture_ownership_ledger.md:106`.

**Current conceptual status:** Likely permanent candidate with transitional vocabulary/fanout.

**Open questions:** Which fallback-family fields are compatibility projections versus permanent runtime schema?

### Concept: Validators

**Working definition:** Pure or bounded predicates that determine whether candidate text/artifacts satisfy contracts or legality constraints.

**Alternative terminology:** Validation layer, validator predicates, conformance checking.

**Primary architectural responsibility:** Detect contract/legality failures without repairing, scoring, or owning truth.

**Lifecycle position:** Final-emission gate and related contract checks.

**Authority and ownership relationship:** Validators own pass/fail evidence for their predicate; gate owns ordering/application and metadata packaging.

**Primary producers:** `game.final_emission_validators`, specialized validator modules.

**Primary consumers:** Final emission gate, repair loops, tests, FEM traces.

**Inputs and outputs:** Candidate text, contracts, context; pass/fail verdict, reason codes, evidence.

**Protected invariants:** Explicit in acceptance quality: validation owns verdict and evidence, not repair or scoring (`game/acceptance_quality.py:319` from search evidence). Explicit: validation-layer separation is review discipline, not runtime policy engine (`docs/architecture_ownership_ledger.md:15`).

**Failure modes addressed:** Malformed emission, fabricated authority, contract violations, validator results becoming hidden scoring.

**Implementation evidence:** `game/final_emission_validators.py`, `game/acceptance_quality.py`, `game/validation_layer_contracts.py`.

**Test evidence:** `tests/test_final_emission_validators.py`, `tests/test_fallback_behavior_validator.py`, `tests/test_narrative_mode_output_validator.py`.

**Documentation evidence:** `docs/validation_layer_separation_block_b_residue.md:22`, `docs/architecture_ownership_ledger.md:15`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Which validators are advisory, gating, or diagnostic-only should be captured in one durable table.

### Concept: Repair

**Working definition:** Bounded deterministic alteration of candidate text or metadata to satisfy a contract after validation detects a failure.

**Alternative terminology:** Final-emission repairs, semantic repair, boundary repair, upstream prepared repair.

**Primary architectural responsibility:** Recover from specific known failures without silent semantic invention.

**Lifecycle position:** Mostly final-emission gate, with upstream-prepared repair moved before final emission for some response-type cases.

**Authority and ownership relationship:** `game.final_emission_repairs` remains runtime repair orchestration home, but semantic mutations at this boundary are transitional (`docs/architecture_ownership_ledger.md:127`).

**Primary producers:** `game.final_emission_repairs`, `game.upstream_response_repairs`, local repair modules.

**Primary consumers:** Gate, final-emission metadata, replay projection.

**Inputs and outputs:** Candidate text and validation result; repaired text or skip metadata.

**Protected invariants:** Explicit: gate no longer invents answer/action fallback lines when upstream prepared emission is absent (`tests/test_final_emission_boundary_convergence.py:208`). Explicit: repair fallback behavior strip-only no template synthesis (`tests/test_final_emission_boundary_convergence.py:103`).

**Failure modes addressed:** Illegal output, meta fallback voice, response-type mismatch, semantic mutation at wrong boundary.

**Implementation evidence:** `game/final_emission_repairs.py`, `game/upstream_response_repairs.py`.

**Test evidence:** `tests/test_final_emission_repairs.py`, `tests/test_final_emission_boundary_convergence.py:46`, `tests/test_final_emission_boundary_convergence.py:151`.

**Documentation evidence:** `docs/final_emission_ownership_convergence.md:21`, `docs/architecture_ownership_ledger.md:125`.

**Current conceptual status:** Possible overlap and transitional candidate.

**Open questions:** Are all repair modes legality-preserving, or do some remain upstream-movable semantic fixes?

### Concept: Sanitizers

**Working definition:** Last-mile cleanup that strips scaffolding, unsafe formatting, or internal contamination from player-facing output, with emergency fallback only under bounded conditions.

**Alternative terminology:** Output sanitizer, strip-only sanitizer, sanitizer fallback, route-illegal strip.

**Primary architectural responsibility:** Prevent malformed or internal text from shipping without becoming a semantic repair/generation layer.

**Lifecycle position:** Final-emission boundary and finalize tail.

**Authority and ownership relationship:** Sanitizer owns cleanup behavior; gate/final emission orchestrates and records; replay projection observes sanitizer mutations.

**Primary producers:** `game.output_sanitizer`, `game.output_sanitizer_lineage`, finalizer helpers.

**Primary consumers:** Final emission gate/finalize, FEM, runtime projection.

**Inputs and outputs:** Candidate text and sanitizer context; cleaned text and sanitizer debug/lineage.

**Protected invariants:** Explicit: strip-only sanitizer drops scaffold without rewrite (`tests/test_final_emission_boundary_convergence.py:130`, `tests/test_final_emission_boundary_convergence.py:394`). Inferred: sanitizer must not invent new semantic content in default mode.

**Failure modes addressed:** Internal JSON/debug leaking to player, route-illegal contamination, empty output.

**Implementation evidence:** `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py`, `game/final_emission_replay_projection.py:672`.

**Test evidence:** `tests/test_output_sanitizer.py`, `tests/test_golden_replay_fallback_sanitizer_projection.py`, `tests/test_final_emission_boundary_convergence.py:405`.

**Documentation evidence:** `docs/final_emission_ownership_convergence.md`, `docs/validation_layer_separation_block_b_residue.md:11`.

**Current conceptual status:** Likely permanent candidate with overlap risk.

**Open questions:** Document exact boundary between sanitizer emergency fallback and repair fallback.

### Concept: Diagnostics

**Working definition:** Inspectable debug, trace, lineage, telemetry, and report surfaces that explain behavior after the fact.

**Alternative terminology:** Runtime diagnostics, debug lanes, trace, observability, telemetry.

**Primary architectural responsibility:** Make failures and decisions inspectable without driving runtime behavior.

**Lifecycle position:** Runtime metadata capture, projection, post-runtime reports.

**Authority and ownership relationship:** Diagnostics may read behavior and evidence; they should not select behavior, mutate state, or become acceptance unless promoted.

**Primary producers:** Runtime debug lanes, FEM, `runtime_lineage_telemetry`, projection/report tools.

**Primary consumers:** Operators, tests, replay, audits.

**Inputs and outputs:** Runtime metadata; diagnostic events/reports.

**Protected invariants:** Explicit: governance docs/tests must not execute gameplay (`AR-AF_architecture_reconciliation_synthesis.md:153`); replay governance excludes diagnostics/dashboards as authority (`docs/testing/replay_governance_authority.md:5`).

**Failure modes addressed:** Silent failure, uninspectable fallback, dashboards changing behavior.

**Implementation evidence:** `game/final_emission_replay_projection.py:774`, `game/runtime_lineage_telemetry.py`, report tools.

**Test evidence:** `tests/test_final_emission_gate_diagnostics.py`, `tests/test_replay_boundary_governance.py`.

**Documentation evidence:** `AR-AB_runtime_authority_and_replay_boundary_map.md:61`, `docs/testing/replay_governance_authority.md:35`.

**Current conceptual status:** Likely permanent candidate.

**Open questions:** Distinguish diagnostics from evidence in a canonicality index.

### Concept: Telemetry / Lineage

**Working definition:** Compact structured records of stage transitions, mutation classes, owners, and sources.

**Alternative terminology:** Stage diff telemetry, runtime lineage events, FEM mutation lineage.

**Primary architectural responsibility:** Explain how output changed and who owned each observed mutation.

**Lifecycle position:** Final emission and post-finalization projection.

**Authority and ownership relationship:** Telemetry records/projections are diagnostic; they do not own engine truth or gate orchestration.

**Primary producers:** `game.stage_diff_telemetry`, `game.runtime_lineage_telemetry`, `game.final_emission_replay_projection`.

**Primary consumers:** Replay projection, diagnostics, gate tests.

**Inputs and outputs:** FEM/debug/trace data; lineage events.

**Protected invariants:** Explicit: stage diff telemetry compatibility wrappers do not own packet/gate semantics (`docs/architecture_ownership_ledger.md:152`, `docs/architecture_ownership_ledger.md:161`).

**Failure modes addressed:** Unattributed mutation, conflating telemetry with owner authority.

**Implementation evidence:** `game/final_emission_replay_projection.py:598`, `game/final_emission_replay_projection.py:774`.

**Test evidence:** `tests/test_stage_diff_telemetry.py`, `tests/test_cf1_route_and_trace_precedence.py`.

**Documentation evidence:** `docs/architecture_ownership_ledger.md:152`.

**Current conceptual status:** Likely permanent candidate.

**Open questions:** Relationship between lineage and provenance should be clarified.

### Concept: Governance

**Working definition:** Doctrine, ledgers, manifests, guards, and tests that declare and watch architecture without executing gameplay.

**Alternative terminology:** Drift-watch, governance contract, replay governance, ownership governance.

**Primary architectural responsibility:** Prevent architectural drift and document target ownership/acceptance boundaries.

**Lifecycle position:** Development/test/documentation.

**Authority and ownership relationship:** Governance owns doctrine and checks; runtime owns behavior.

**Primary producers:** AR reports, `docs/architecture_ownership_ledger.md`, replay governance docs/tests, ownership guard tests.

**Primary consumers:** Developers, CI, external reviewers.

**Inputs and outputs:** Static checks, manifests, docs, governance records.

**Protected invariants:** Explicit: governance declares and watches architecture; it does not execute gameplay (`AR-AD_target_architecture_doctrine.md:69`, `AR-AF_architecture_reconciliation_synthesis.md:153`).

**Failure modes addressed:** Hidden runtime policy in docs/tests, governance thresholds changing acceptance.

**Implementation evidence:** `tests/replay_governance_contract.py`, `tests/replay_governance_registry.py`, ownership guard tests.

**Test evidence:** `tests/test_replay_governance_authority.py`, `tests/test_gate_boundary_governance.py`, `tests/test_ownership_registry.py`.

**Documentation evidence:** `docs/testing/replay_governance_authority.md:42`, `AR-AF_architecture_reconciliation_synthesis.md:115`.

**Current conceptual status:** Clearly permanent candidate.

**Open questions:** Canonical docs should distinguish governance contract from analytical/historical reports.

### Concept: Canonicality

**Working definition:** The classification of surfaces as runtime truth, governance contract, protected acceptance, generated artifact, or advisory artifact.

**Alternative terminology:** Canonicality index, artifact status, promoted evidence.

**Primary architectural responsibility:** Prevent all evidence from being treated as equal authority.

**Lifecycle position:** Documentation, governance, handoff, review.

**Authority and ownership relationship:** AR-AD provides canonicality examples; future docs may need a durable index.

**Primary producers:** AR doctrine, manifests, artifact reports.

**Primary consumers:** Developers and reviewers.

**Inputs and outputs:** File/surface status labels.

**Protected invariants:** Explicit: generated/advisory artifacts require explicit promotion before becoming authority (`AR-AF_architecture_reconciliation_synthesis.md:153`).

**Failure modes addressed:** Advisory artifacts becoming hidden policy; old reports superseding current doctrine accidentally.

**Implementation evidence:** Documentation and artifact manifest helpers.

**Test evidence:** `tests/test_golden_replay_artifact_manifest.py`, `tests/test_cf6_generated_projection_artifact_governance.py`.

**Documentation evidence:** `AR-AD_target_architecture_doctrine.md:458`, `AR-AI_final_vision_compatibility_closeout.md:64`.

**Current conceptual status:** Likely permanent candidate.

**Open questions:** Which reports from Foundation Stabilization should be labeled historical versus current reference?

### Concept: Compatibility Residue

**Working definition:** Supported aliases, legacy read paths, tolerated module splits, or historical behavior locks retained for compatibility while canonical ownership lives elsewhere.

**Alternative terminology:** Historical residue, support paths, sediment layer, transitional seam.

**Primary architectural responsibility:** Preserve behavior and test stability without reopening co-equal ownership.

**Lifecycle position:** Runtime compatibility paths, tests, docs.

**Authority and ownership relationship:** Residue is explicitly non-authoritative unless promoted or reclassified.

**Primary producers:** Legacy helpers, compatibility wrappers, historical regression tests.

**Primary consumers:** Older payloads/tests, downstream integration.

**Inputs and outputs:** Legacy shapes or aliases; normalized current behavior.

**Protected invariants:** Explicit: compatibility/support residue may remain without reopening ownership (`docs/architecture_ownership_ledger.md:29`). Explicit: Block B residue is checklist, not alternate registry (`docs/validation_layer_separation_block_b_residue.md:3`).

**Failure modes addressed:** Breaking old payloads; mistaking aliases for active architecture.

**Implementation evidence:** `game.gm` compatibility re-exports, `game.stage_diff_telemetry.resolve_gate_turn_packet`, CTIR-absent prompt reads.

**Test evidence:** Historical regression tests and compatibility governance tests.

**Documentation evidence:** `docs/architecture_audit_readme.md:183`, `docs/validation_layer_separation_block_b_residue.md:29`.

**Current conceptual status:** Transitional candidate / historical candidate depending on seam.

**Open questions:** Retirement conditions are often missing or scattered.

## 4. Concept Relationship Matrix

| Pair | Current Evidence Classification | Explanation and References |
| ---- | ------------------------------- | -------------------------- |
| Replay / Realization | Intentionally distinct | Realization creates/phrases authorized candidate text; replay observes finalized runtime outputs after execution. Runtime must not depend on protected replay (`AR-AD_target_architecture_doctrine.md:61`, `game/realization_authority.py:119`). |
| Replay / Provenance | Sequential and intentionally distinct | Provenance stamps behavior at write time; replay may project/observe it. Provenance explains but does not own behavior (`AR-AF_architecture_reconciliation_synthesis.md:152`, `game/realization_provenance.py:3`). |
| Realization / Authority | Hierarchical | Realization authority profiles define what realization layers may do and what they may not do (`game/realization_authority.py:27`, `game/realization_authority.py:372`). |
| Ownership / Authority | Partially overlapping but distinct | Ownership assigns responsibility; authority grants permission to decide/mutate/select. Provenance owner can differ from fallback selector (`game/fallback_provenance_debug.py:5`). |
| Authority / Routing | Intentionally distinct | Routing chooses a path; authority determines who may decide truth/mutation. Model routing owns model I/O/route metadata, not game truth (`AR-AD_target_architecture_doctrine.md:49`). |
| Routing / Fallback | Sequential | Routing and retry selection may lead to fallback; fallback family/content/provenance remain separate axes (`AR-AB_runtime_authority_and_replay_boundary_map.md:174`). |
| Fallback / Repair | Partially overlapping and historically entangled | Some repairs select fallback-like text; convergence docs move semantic construction upstream and keep gate repair legality-focused (`docs/architecture_ownership_ledger.md:108`, `tests/test_final_emission_boundary_convergence.py:151`). |
| Validators / Repair | Sequential | Validators detect failures; repairs alter text only after validation and should revalidate. Direct-owner split is visible in fallback gate tests (`tests/test_fallback_behavior_gate.py:15`). |
| Validators / Sanitizers | Intentionally distinct with overlap risk | Validators produce verdicts/evidence; sanitizers clean shipped text. Strip-only sanitizer tests guard against rewrite/synthesis (`tests/test_final_emission_boundary_convergence.py:130`). |
| Repair / Sanitizers | Partially overlapping | Both may alter output; repair is contract-driven, sanitizer is last-mile cleanup. Default strip-only sanitizer must not substitute templates (`tests/test_final_emission_boundary_convergence.py:405`). |
| Provenance / Evidence | Hierarchical/orthogonal | Provenance is one kind of evidence; evidence also includes logs, snapshots, protected rows, reports. Evidence does not automatically own behavior (`AR-AD_target_architecture_doctrine.md:65`). |
| Evidence / Diagnostics | Partially overlapping | Diagnostics are explanatory evidence, but not all evidence is diagnostic; protected acceptance and governance contracts are separate categories (`AR-AF_architecture_reconciliation_synthesis.md:100`). |
| Diagnostics / Validators | Intentionally distinct | Validators may emit diagnostic evidence; diagnostics do not decide pass/fail unless inside validator output. Block B says numeric heuristics inside validators are diagnostic, not evaluator scores (`docs/validation_layer_separation_block_b_residue.md:24`). |

## 5. Invariant-to-Concept Map

| Invariant | Concepts Protecting It | Evidence | Explicit or Inferred | Confidence |
| --------- | ---------------------- | -------- | -------------------- | ---------- |
| Runtime truth before narration | Runtime transaction, domain simulation, CTIR, prompt/adaptation, realization | `AR-AD_target_architecture_doctrine.md:33`, `AR-AF_architecture_reconciliation_synthesis.md:139` | Explicit | High |
| One runtime transaction spine | Runtime transaction, API ownership, persistence timing | `AR-AF_architecture_reconciliation_synthesis.md:29` | Explicit | High |
| No unauthorized state mutation | State authority, ownership, authority | `game/state_authority.py:1`, `tests/test_state_authority.py:87`, `tests/test_state_authority.py:96` | Explicit | High |
| GPT owns expression, not truth | Realization, authority, prompt/adaptation, domain simulation | `game/realization_authority.py:119`, `AR-AD_target_architecture_doctrine.md:49` | Explicit | High |
| CTIR is resolved-turn meaning when present | CTIR, prompt/adaptation | `docs/architecture_ownership_ledger.md:79`, `docs/architecture_ownership_ledger.md:89` | Explicit | High |
| Final emission owns last-mile legality/packaging | Final emission, validators, repairs, sanitizers, provenance | `AR-AF_architecture_reconciliation_synthesis.md:149`, `docs/architecture_ownership_ledger.md:120` | Explicit | High |
| No silent semantic repair at final boundary | Final emission, repair, validators, upstream prepared repair | `docs/architecture_ownership_ledger.md:108`, `tests/test_final_emission_boundary_convergence.py:151` | Explicit | High |
| Replay dependency is one-way | Replay, projection, governance, evidence | `AR-AD_target_architecture_doctrine.md:61`, `tests/test_replay_boundary_governance.py:96` | Explicit | High |
| Runtime diagnostic projection separate from protected acceptance projection | Projection, replay, diagnostics | `AR-AB_runtime_authority_and_replay_boundary_map.md:61`, `tests/test_replay_boundary_governance.py:101` | Explicit | High |
| Provenance explains behavior without owning behavior | Provenance, evidence, fallback | `AR-AF_architecture_reconciliation_synthesis.md:152`, `game/fallback_provenance_debug.py:5` | Explicit | High |
| Governance does not execute gameplay | Governance, ownership, replay | `AR-AD_target_architecture_doctrine.md:69`, `docs/testing/replay_governance_authority.md:5` | Explicit | High |
| Fallback ownership is multi-axis | Fallback, provenance, final emission, replay | `AR-AB_runtime_authority_and_replay_boundary_map.md:174`, `AR-AF_architecture_reconciliation_synthesis.md:147` | Explicit | High |
| Sanitizer default behavior remains strip-only | Sanitizers, final emission, repair | `tests/test_final_emission_boundary_convergence.py:130`, `tests/test_final_emission_boundary_convergence.py:394` | Explicit | Medium-high |
| Evidence does not automatically become authority | Evidence, canonicality, governance | `AR-AD_target_architecture_doctrine.md:65`, `AR-AF_architecture_reconciliation_synthesis.md:153` | Explicit | High |
| Compatibility residue does not reopen co-equal ownership | Ownership, compatibility residue, governance | `docs/architecture_ownership_ledger.md:29`, `docs/validation_layer_separation_block_b_residue.md:3` | Explicit | High |

## 6. Transitional and Historical Candidate Register

| Candidate | Original Purpose | Current Dependency | Retirement Condition | Evidence | Confidence |
| --------- | ---------------- | ------------------ | -------------------- | -------- | ---------- |
| Final-emission semantic repairs | Keep player-facing text legal/usable under many failure modes | Tests still lock boundary behavior and no-synthesis invariants | Move synthesis/meaning-order fixes upstream while preserving legality/packaging | `docs/architecture_ownership_ledger.md:108`, `docs/final_emission_ownership_convergence.md:21`, `tests/test_final_emission_boundary_convergence.py:46` | High |
| Legacy diegetic fallback family | Classify older fallback renderers | Still listed as tolerated family | Retire/replace old renderers or reclassify with explicit owner | `game/realization_authority.py:343`, `game/realization_authority.py:350` | High |
| Dual fallback-family vocabulary | Preserve runtime and replay compatibility across fallback fields | Realization provenance stamps separately from diegetic family; replay projects observed field | Consumer precedence documented and old field consumers retired | `game/realization_provenance.py:3`, `AR-AB_runtime_authority_and_replay_boundary_map.md:192` | High |
| CTIR-absent prompt compatibility reads | Tolerate older/missing CTIR flows | Prompt context may fall back when CTIR absent | CTIR presence is guaranteed for relevant flows and fallback reads are proven unused | `docs/architecture_ownership_ledger.md:87` | Medium |
| Opening fallback compatibility fields | Preserve protected replay observations across complex start flow | Protected replay observes opening fallback owner/source fields | Opening fallback write/read fields are consolidated without losing evidence | `AR-AB_runtime_authority_and_replay_boundary_map.md:174`, `AR-AD_target_architecture_doctrine.md:104` | Medium-high |
| `fallback_provenance_debug` historical module name | Historical debug naming retained while module owns stable provenance | Runtime still imports the module | Rename only if done with compatibility plan, or document durable name | `game/fallback_provenance_debug.py:3` | High |
| Generated/advisory evidence artifact fanout | Preserve stabilization/audit analysis | Many reports remain in repo and are cited for context | Canonicality/retention index labels current, generated, advisory, historical | `AR-AF_architecture_reconciliation_synthesis.md:100`, `AR-AE_architecture_conformance_assessment.md:39` | Medium |
| Gate module split across validators/repairs/meta | Separate practical files inside one gate layer | Still tolerated and tested | No retirement required unless split creates drift; file split itself is not duplication | `docs/validation_layer_separation_block_b_residue.md:11`, `docs/validation_layer_separation_block_b_residue.md:22` | High |
| Stage diff telemetry compatibility wrapper | Maintain older observability path | Wrapper remains compatibility residue | Consumers migrate to packet-owned resolution, or wrapper stays explicitly non-authoritative | `docs/architecture_ownership_ledger.md:161` | Medium |

## 7. Ambiguity and Documentation Gap Register

| Concept or Boundary | Ambiguity | Conflicting Evidence | Risk of Leaving Unclear | Recommended Next Investigation |
| ------------------- | --------- | -------------------- | ----------------------- | ------------------------------ |
| Fallback / Repair | Some repair paths select fallback-like text; some fallback is not repair | Multi-axis fallback is permanent, but boundary semantic repair is transitional | Future cleanup could remove safety paths or preserve accidental synthesis | Trace every final-emission repair mode to fallback family/provenance/test owner. |
| Repair / Sanitizer | Both can mutate text | Sanitizer strip-only doctrine coexists with emergency fallback fields | Sanitizer could become hidden rewrite layer | Compare sanitizer lineage fields against repair metadata and projection tests. |
| Validators / Diagnostics | Validators emit evidence and numeric diagnostics | Block B permits diagnostic heuristics but rejects evaluator scoring | Diagnostic fields may be mistaken for policy scores | Build validator mode table: advisory, gating, diagnostic-only. |
| Provenance / Evidence / Diagnostics | Provenance is evidence, diagnostics are evidence, but authority differs | Canonicality doctrine exists but not consolidated into durable index | External reviewers may over-trust generated reports | Create evidence canonicality and artifact-retention index. |
| Ownership / Authority | Same docs sometimes discuss owners and allowed authority together | State authority, realization authority, and ownership ledger use different vocabularies | Misreading owner as permission or permission as owner | Write glossary and examples for owner, authority, selector, applicator, packager, observer. |
| Routing / Dispatch | Model routing, interaction routing, final route, dispatch are not unified | Doctrine says routing metadata is not truth, but individual route modules vary | Path selection may be confused with semantic decision authority | Inventory route modules and route fields by lifecycle stage. |
| CTIR / Prompt compatibility | Prompt fallback reads are allowed when CTIR absent | CTIR is canonical when present; compatibility path still exists | Prompt may be read as second meaning owner | Determine actual call paths where CTIR is absent today. |
| Runtime diagnostic projection / protected replay projection | Well documented as separate but both read FEM/provenance | Protected replay may consume runtime diagnostics | Future consolidation could erase dependency direction | Keep AO5 boundary tests and inspect all new projection imports. |
| Compatibility residue / historical artifact | Some residue is intentionally stable; some may be historical only | Docs call residue tolerated but often lack retirement conditions | Cleanup proposals may be blocked or unsafe due to unclear status | Build residue register with original condition, active dependency, retirement signal. |
| Governance / conformance | Governance docs declare target architecture but code may only mostly align | Audit readme warns ownership declarations are not proof | False confidence in docs as implementation proof | Pair each governance claim with direct-owner test and implementation evidence. |

## 8. Preliminary Concept Map

```text
Core runtime concepts
  Runtime transaction
    -> Domain simulation
    -> CTIR
    -> Prompt/adaptation
    -> GPT/model realization
    -> Final emission
    -> Persistence/log/response

Governance concepts
  Ownership
    -> Direct-owner tests
    -> Downstream consumers
    -> Compatibility residue
  Authority
    -> State authority
    -> Realization authority
    -> Replay governance authority
  Canonicality
    -> Runtime truth
    -> Governance contract
    -> Protected acceptance
    -> Generated artifact
    -> Advisory artifact

Runtime lifecycle concepts
  Routing
    -> Model routing
    -> Interaction routing
    -> Final route
  Projection
    -> CTIR/prompt projections
    -> Runtime diagnostic projection
    -> Protected acceptance projection

Recovery and defensive concepts
  Fallback
    -> Upstream fast fallback
    -> Retry terminal fallback
    -> Opening fallback
    -> Strict-social fallback
    -> Sealed fallback
  Validators
    -> Repair
    -> Sanitizers

Trust and evidence concepts
  Provenance
    -> Realization fallback family
    -> Fallback provenance trace
  Evidence
    -> Runtime payload/log/snapshot/FEM
    -> Protected observation rows
    -> Governance records
    -> Reports/audits

Diagnostic or operational concepts
  Diagnostics
    -> Debug lanes
    -> Runtime lineage events
    -> Stage diff telemetry
    -> Audit/report outputs

Transitional or historical mechanisms
  Final-emission semantic repair pressure
  Legacy diegetic fallback family
  CTIR-absent prompt compatibility
  Dual fallback-family vocabulary
  Opening fallback compatibility fields
  Historical/debug-named provenance module

Unclassified or needs tighter classification
  Evidence versus diagnostics
  Lineage versus provenance
  Routing versus dispatch
```

## 9. Preliminary Findings

Concepts already supported as distinct: runtime transaction, domain simulation, state authority, CTIR, prompt/adaptation, realization, final emission, replay, runtime diagnostic projection, protected replay projection, provenance, governance, ownership, and canonicality.

Concepts that might be terminological aliases or require sharper vocabulary: routing/dispatch, diagnostics/telemetry/lineage, evidence/diagnostics, realization/generation/emission.

Concepts that may represent phases of one broader responsibility: validators, repair, and sanitizers are phases of the final-emission legality/packaging pipeline, but the repo treats them as different responsibilities with different owners and tests.

Concepts that appear transitional: final-emission semantic repair pressure, CTIR-absent prompt fallback reads, dual fallback-family vocabulary, opening fallback compatibility fields, legacy diegetic fallback family, and advisory/generated evidence fanout.

Concepts whose status cannot yet be determined safely: which individual repair modes are permanent guardrails versus upstream-movable semantic fixes; whether all diagnostics are purely diagnostic; whether older audit artifacts are still current references or historical context.

Newly discovered concepts that should enter Campaign 3: CTIR, prompt/adaptation, domain simulation, final emission, projection, governance, canonicality, compatibility residue, telemetry/lineage, persistence, and model routing.

## 10. Recommended Next Cycle

Recommended next cycle: **Validation, Repair, Sanitization, and Fallback Reconciliation**.

This is the highest-value next investigation because it is the densest ambiguity cluster and directly affects player-facing output. The repo already says final-emission repair ownership is transitional, but it also regression-locks safety behaviors. Classification should happen at the mode/path level, not the module level.

Files it would need:

- `docs/architecture_ownership_ledger.md`
- `docs/final_emission_ownership_convergence.md`
- `docs/validation_layer_separation_block_b_residue.md`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/output_sanitizer.py`
- `game/upstream_response_repairs.py`
- `game/fallback_behavior.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_replay_projection.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_repairs.py`
- `tests/test_final_emission_validators.py`
- `tests/test_output_sanitizer.py`
- `tests/test_fallback_behavior_validator.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_golden_replay_fallback_*`

Questions it should settle:

- Which repairs are legality-preserving, which are semantic mutation, and which are sealed terminal exceptions?
- Which fallback paths are runtime safety behavior versus replay compatibility projection?
- Does sanitizer ever own fallback decision-making, or only cleanup/emergency text under bounded conditions?
- Which validator outputs are gating, advisory, or diagnostic-only?
- Which tests are direct-owner coverage versus historical regression locks?

Out of scope:

- Removing fallback behavior.
- Refactoring final-emission modules.
- Collapsing replay and runtime projection.
- Reopening Campaign 2 vision compatibility.
- Feature expansion.

## 11. Files Recommended for External Review

### Required

- `AR-AF_architecture_reconciliation_synthesis.md` - Concise baseline and invariant list for the reconciled architecture.
- `AR-AD_target_architecture_doctrine.md` - Most complete doctrine for target boundaries, canonicality, and transitional responsibilities.
- `AR-AB_runtime_authority_and_replay_boundary_map.md` - Best map of runtime authority, replay separation, and fallback ownership axes.
- `docs/architecture_ownership_ledger.md` - Repo-facing ownership declaration for ambiguous seams and test-owner framing.
- `docs/final_emission_ownership_convergence.md` - Target classification for final-emission repair and semantic mutation pressure.
- `docs/testing/replay_governance_authority.md` - Canonical hierarchy separating replay governance from replay execution and diagnostics.
- `game/state_authority.py` - Concrete state-domain authority registry and guard implementation.
- `game/realization_authority.py` - Concrete realization/fallback authority profiles and provenance requirements.
- `game/final_emission_gate.py` - Central last-mile legality and packaging orchestration.
- `game/final_emission_repairs.py` - Main repair implementation and current transitional pressure point.
- `game/final_emission_validators.py` - Validator predicate owner for final-emission checks.
- `game/output_sanitizer.py` - Sanitization boundary and strip-only cleanup behavior.
- `game/final_emission_replay_projection.py` - Runtime diagnostic projection and lineage read-side surface.
- `tests/test_replay_boundary_governance.py` - Locks runtime diagnostic projection and protected acceptance projection separation.
- `tests/test_final_emission_boundary_convergence.py` - Locks no-silent-semantic-repair and sanitizer/upstream-prepared behavior.

### Strongly Recommended

- `AR-AI_final_vision_compatibility_closeout.md` - Prevents accidental reopening of broad architecture/vision questions.
- `AR-AE_architecture_conformance_assessment.md` - Current conformance and drift risk assessment.
- `docs/validation_layer_separation_block_b_residue.md` - Important for interpreting tolerated validation/gate splits as non-duplication.
- `docs/architecture_audit_readme.md` - Explains how to interpret ownership evidence, residue, and audit limitations.
- `docs/testing/protected_replay_manifest.md` - Protected replay field and scenario policy.
- `game/realization_provenance.py` - Write-time realization fallback-family stamp implementation.
- `game/fallback_provenance_debug.py` - Stable fallback provenance owner with historical name and containment logic.
- `game/upstream_response_repairs.py` - Upstream-prepared repair construction now separated from final-emission synthesis.
- `tests/test_state_authority.py` - Direct-owner tests for registry, mutation, and read guards.
- `tests/test_realization_authority.py` - Direct-owner tests for realization authority profiles.
- `tests/test_realization_provenance.py` - Provenance normalization and stamping tests.
- `tests/test_final_emission_repairs.py` - Direct-owner tests for repair semantics.
- `tests/test_final_emission_validators.py` - Direct-owner tests for validation predicates.
- `tests/test_output_sanitizer.py` - Direct-owner tests for sanitizer behavior.
- `tests/test_fallback_behavior_validator.py` - Direct-owner tests for fallback behavior predicates.
- `tests/test_fallback_behavior_gate.py` - Downstream gate ordering/application coverage for fallback behavior.

### Optional

- `AR-AA_architectural_mapping_discovery.md` - Historical broad file inventory and original tension map.
- `AR-AC_architectural_ownership_reconciliation.md` - Layer and permanent/transitional ownership rationale.
- `AR-AG_final_vision_compatibility_discovery.md` - Evidence source list and trust/provenance context.
- `AR-AH_final_vision_compatibility_assessment.md` - Compatibility classifications and local refinement framing.
- `docs/architecture_audit_readme.md` - Useful when interpreting report artifacts and audit limitations.
- `tests/test_gate_boundary_governance.py` - Useful for test magnet and direct-owner guard details.
- `tests/test_golden_replay_projection.py` and golden replay fallback projection suites - Useful for protected replay field behavior and fallback observation details.
- `tools/final_emission_ownership_audit.py` - Advisory scan for final-emission boundary drift.
- `tools/realization_provenance_audit.py` - Advisory scan for provenance consistency.
