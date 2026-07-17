# AR-BD Concept Map Synthesis and Campaign Closeout

Campaign: Campaign 3 - Concept Reconciliation

Scope: final synthesis and closeout of Campaign 3 using AR-BA, AR-BB, AR-BC, and the doctrine/implementation/test evidence those reports established.

Non-goals: implementation refactoring, terminology simplification for aesthetics, concept merging, Campaign 1 or Campaign 2 reopening, Controlled Feature Expansion.

## 1 Executive Summary

Campaign 3 has established a stable conceptual architecture for the project.

The architecture is best understood as a forward runtime truth pipeline surrounded by defensive runtime constraints, evidence projection, and governance:

```text
Player intent
  -> runtime transaction
  -> domain simulation
  -> CTIR resolved-turn meaning
  -> prompt/adaptation
  -> realization
  -> final emission
  -> persistence/log/response
  -> projection/replay/evidence
  -> governance
```

The permanent conceptual model is now clear:

- Runtime truth is established before narration.
- One runtime transaction coordinates a turn.
- Domain simulation owns authoritative outcomes.
- State authority governs mutation/read boundaries.
- CTIR owns resolved-turn meaning for narration.
- Prompt/adaptation packages approved truth into expression context.
- Realization produces candidate expression and governed fallback/provenance vocabulary.
- Final emission owns final legality, selection, packaging, metadata, and sealed terminal exceptions.
- Validators, bounded repair, sanitizers, and fallback are distinct defensive runtime concepts.
- Replay, projection, provenance, evidence, diagnostics, and telemetry explain finalized behavior after runtime.
- Ownership, authority, canonicality, and governance keep these concepts from collapsing into each other.
- Compatibility residue is a real category, but individual residue instances are historical or transitional unless explicitly promoted.

AR-BB resolved the highest-pressure conceptual cluster: validators, repair, sanitizers, fallback, and final emission. AR-BC then classified the major vocabulary. AR-BD consolidates those conclusions into the contributor-facing concept map.

Campaign 3 is complete. Future implementation can rely on this vocabulary without reopening the inventory, reconciliation, or classification work.

## 2 Permanent Concept Map

The concept map below shows dependency direction, not file import order or detailed runtime flow.

```text
Foundational governance vocabulary
  Canonicality
    -> Ownership
    -> Authority
      -> State Authority
      -> Runtime Transaction

Core runtime truth
  Runtime Transaction
    -> Domain Simulation
      -> CTIR
        -> Prompt / Adaptation
          -> Realization
            -> Final Emission
              -> Persistence / Log / Response

Defensive runtime boundary
  Final Emission
    -> Validators
    -> Bounded Repair
    -> Sanitizers
    -> Fallback
    -> Provenance packaging

Evidence and observation
  Finalized runtime surfaces
    -> Runtime Diagnostic Projection
    -> Protected Replay Projection
    -> Replay
    -> Evidence
    -> Diagnostics
    -> Telemetry / Lineage

Governance and continuity
  Evidence
    -> Canonicality labels
    -> Governance
    -> Test Governance
    -> Compatibility Residue registers
    -> Historical Vocabulary
```

### Core Runtime

Core runtime concepts answer "how does a player intent become authoritative game output?"

- Runtime Transaction coordinates the turn.
- Domain Simulation decides game truth.
- State Authority constrains mutation/read permissions.
- CTIR captures resolved-turn meaning for narration.
- Prompt / Adaptation packages truth into model context.
- Realization produces candidate expression.
- Final Emission seals the final player-facing result.

### Defensive Runtime

Defensive runtime concepts answer "what prevents invalid or unsafe output from shipping?"

- Validators answer whether a candidate satisfies deterministic predicates.
- Repair answers whether a known failure can be corrected under bounded rules.
- Sanitizers remove, package, or drop unsafe presentation artifacts.
- Fallback provides bounded substitute behavior when normal output cannot safely ship.
- Final Emission orchestrates these concepts at the last-mile boundary.

### Evidence

Evidence concepts answer "how do we know what happened, and what may future tools compare?"

- Provenance records why output exists and who authored, selected, applied, or packaged it.
- Projection reads finalized surfaces into diagnostic or protected observation forms.
- Replay observes finalized runtime behavior and protected fields.
- Evidence collects runtime truth, projections, generated reports, and advisory artifacts.
- Diagnostics and Telemetry / Lineage explain runtime paths and ownership splits.

### Governance

Governance concepts answer "which claims are authoritative and who owns them?"

- Ownership assigns responsibility.
- Authority states the kind of decision a concept may make.
- Canonicality classifies surfaces as runtime truth, runtime projection, protected acceptance, governance contract, generated artifact, advisory artifact, or historical reference.
- Governance declares doctrine and drift-watch rules without executing gameplay.

### Historical / Transitional

Historical and transitional concepts answer "why does this older or compatibility-shaped surface still exist?"

- Compatibility Residue is the umbrella category for tolerated non-owning old paths, aliases, fields, and report surfaces.
- Transitional repair names current final-boundary semantic repair pressure.
- Transitional fallback vocabulary names dual fallback-family fields and legacy fallback classifications.
- Historical compatibility mechanisms preserve evidence continuity but do not own current behavior.

## 3 Runtime Concept Lifecycle

This lifecycle describes where each major concept enters and leaves responsibility during a complete runtime turn.

### 1. Player Intent Enters Runtime

Primary concepts: Runtime Transaction, Ownership, Authority, Governance.

Player input enters through the API-visible transaction. Runtime Transaction owns turn ordering. Ownership and Authority determine which modules may coordinate, mutate, select, package, or observe. Governance does not participate in gameplay; it supplies the doctrine that defines these boundaries.

Responsibility entry: Runtime Transaction starts.

Responsibility exit: Runtime Transaction continues through the entire live turn and exits only after response/log/persistence are complete.

### 2. Authoritative Simulation Establishes Truth

Primary concepts: Domain Simulation, State Authority, Runtime Truth.

Domain Simulation resolves what happens in the game world. State Authority constrains which owners may mutate or read domains. GPT, prompt text, replay, diagnostics, and governance do not own this truth.

Responsibility entry: after request eligibility and state loading.

Responsibility exit: after authoritative mutation and hygiene produce the resolved runtime state that narration may express.

### 3. CTIR Captures Resolved-Turn Meaning

Primary concepts: CTIR, Runtime Transaction, Prompt / Adaptation.

CTIR turns post-mutation runtime truth into a bounded resolved-turn meaning object for narration. It is not the whole state and not prompt prose. It is the meaning boundary prompt/adaptation must consume when present.

Responsibility entry: after authoritative mutation.

Responsibility exit: CTIR remains available to prompt/adaptation and downstream evidence, but it does not own expression or final legality.

### 4. Prompt / Adaptation Packages Truth For Expression

Primary concepts: Prompt / Adaptation, Response Policy Contracts, Routing.

Prompt/adaptation reads approved state, CTIR, visibility, response contracts, plans, and route context. It shapes what the model is asked to do without becoming domain truth or gate legality.

Responsibility entry: after CTIR and contract context are available.

Responsibility exit: once model-ready context and constraints are handed to realization/model I/O.

### 5. Realization Produces Candidate Expression

Primary concepts: Realization, Routing, Fallback, Provenance.

Realization covers GPT/model expression, route metadata, candidate prose, governed fallback-family vocabulary, and realization provenance. GPT or fallback content may author words, but neither becomes authoritative domain truth.

Responsibility entry: after prompt/adaptation.

Responsibility exit: when candidate, prepared, fallback, or upstream-error output is handed to final emission.

### 6. Defensive Runtime Seals Player-Facing Output

Primary concepts: Final Emission, Validators, Repair, Sanitizers, Fallback, Provenance.

Final Emission owns last-mile selection, legality, packaging, metadata, FEM, and sealed terminal exceptions. Validators provide deterministic pass/fail evidence. Bounded Repair may correct known failures. Sanitizers strip/package/drop contamination. Fallback may supply bounded substitute behavior. Provenance records the resulting ownership and path explanation.

Responsibility entry: after candidate or fallback output exists.

Responsibility exit: after final player-facing text, metadata, and traceable FEM are sealed.

### 7. Persistence, Log, And Response Preserve The Final Result

Primary concepts: Persistence, Runtime Transaction, Final Emission.

Persistence stores runtime documents and logs. Runtime Transaction owns transaction timing; storage owns mechanics. Logs and response payloads observe finalized surfaces, not unsealed candidate text.

Responsibility entry: after final emission seals output.

Responsibility exit: after durable state/log/response surfaces are complete.

### 8. Evidence Observes Finalized Runtime Surfaces

Primary concepts: Projection, Runtime Diagnostic Projection, Protected Replay Projection, Replay, Evidence, Diagnostics, Telemetry / Lineage, Provenance.

Projection reads finalized surfaces into diagnostic or protected observation models. Runtime Diagnostic Projection explains finalized FEM/provenance. Protected Replay Projection defines protected observations. Replay and evidence consume these surfaces after runtime.

Responsibility entry: after runtime surfaces exist.

Responsibility exit: evidence remains available for review, tests, trend windows, and reports. It does not feed back into live runtime.

### 9. Governance Classifies And Watches

Primary concepts: Governance, Canonicality, Ownership, Authority, Test Governance, Compatibility Residue.

Governance uses evidence to maintain doctrine, direct-owner tests, dependency-direction checks, protected replay policy, and canonicality labels. Governance is read-side and doctrinal, not live gameplay.

Responsibility entry: after evidence exists or when maintainers update doctrine/tests.

Responsibility exit: governance never exits as a support layer, but it must not enter the live runtime decision path.

## 4 Architectural Layer Model

### Runtime Truth

Concepts:

- Domain Simulation
- State Authority
- CTIR
- Persistence

Purpose: establish, constrain, and preserve authoritative game truth and resolved-turn meaning.

Non-ownership: does not author final prose, perform offline scoring, or define protected replay acceptance.

### Runtime Coordination

Concepts:

- Runtime Transaction
- Routing
- Ownership and Authority as applied runtime vocabulary

Purpose: keep one coherent turn sequence and identify which owner may coordinate each decision point.

Non-ownership: does not replace domain owners or make governance a runtime policy engine.

### Expression

Concepts:

- Prompt / Adaptation
- Response Policy Contracts
- Realization
- Opening Realization

Purpose: adapt authoritative truth into model context and candidate player-facing expression.

Non-ownership: does not mutate authoritative truth or own final legality.

### Defensive Runtime

Concepts:

- Final Emission
- Validators
- Bounded Repair
- Sanitizers
- Fallback
- Strict-Social Emission where social terminal semantics are specialized

Purpose: decide what final text can ship and keep invalid, unsafe, or untraceable output from reaching the player.

Non-ownership: does not become a general semantic authoring layer or domain truth owner.

### Evidence

Concepts:

- Replay
- Projection
- Runtime Diagnostic Projection
- Protected Replay Projection
- Provenance
- Evidence
- Diagnostics
- Telemetry / Lineage

Purpose: observe, explain, compare, and preserve finalized runtime behavior.

Non-ownership: does not select runtime behavior or mutate output.

### Governance

Concepts:

- Ownership
- Authority
- Canonicality
- Governance
- Test Governance

Purpose: declare doctrine, classify evidence, assign direct owners, guard dependency direction, and watch drift.

Non-ownership: does not execute gameplay or silently promote advisory artifacts into authority.

### Historical Compatibility

Concepts:

- Compatibility Residue
- Transitional repair vocabulary
- Transitional fallback vocabulary
- Historical compatibility mechanisms
- Advisory / Generated Artifacts when retained as history

Purpose: preserve compatibility, evidence continuity, and old-path interpretation without reopening ownership.

Non-ownership: does not become current architecture unless explicitly promoted.

## 5 Permanent Vocabulary

### Runtime Transaction

Definition: the single live turn sequence from request entry through simulation, CTIR, realization, final emission, persistence, logs, and response.

Purpose: preserve ordering and prevent split runtime authority.

Not: a file-size goal, a universal domain owner, or a replay/evidence concept.

Related concepts: Domain Simulation, CTIR, Final Emission, Persistence, Routing.

Primary invariants: one turn has one transaction spine; runtime truth comes before narration; replay observes finalized outputs.

### Domain Simulation

Definition: authoritative game outcome resolution and state transition semantics.

Purpose: decide what actually happened before expression.

Not: GPT prose, prompt context, final-emission metadata, or replay observation.

Related concepts: State Authority, Runtime Transaction, CTIR, Persistence.

Primary invariants: GPT does not own truth; domain owners own simulation outcomes; final-emission text does not mutate engine truth.

### State Authority

Definition: registry and guard vocabulary for state domains, read permissions, mutation permissions, and cross-domain write exceptions.

Purpose: prevent hidden or unauthorized state mutation.

Not: persistence mechanics, universal state storage, prompt policy, or final-emission repair.

Related concepts: Authority, Ownership, Domain Simulation, Governance.

Primary invariants: only authorized owners mutate domains; read/write exceptions are explicit; prompt/model text is non-authoritative.

### Ownership

Definition: assignment of responsibility for runtime owners, direct-owner tests, downstream consumers, support residue, and governance surfaces.

Purpose: localize responsibility and prevent semantic ownership drift.

Not: proof that implementation is already clean, or the same thing as authority.

Related concepts: Authority, Governance, Test Governance, Compatibility Residue.

Primary invariants: direct-owner suites own semantic assertions; downstream suites consume; compatibility support does not reopen co-equal ownership.

### Authority

Definition: permission to decide, mutate, select, apply, package, observe, or govern within a particular boundary.

Purpose: distinguish behavior ownership from metadata packaging or read-side observation.

Not: mere import presence, broad ownership, or diagnostic visibility.

Related concepts: Ownership, State Authority, Fallback, Provenance, Governance.

Primary invariants: GPT owns expression not truth; provenance records but does not select; replay observes but does not drive runtime.

### Canonicality

Definition: classification of a surface's authority status.

Purpose: separate runtime truth, runtime projection, protected acceptance, governance contract, generated artifact, advisory artifact, and historical reference.

Not: an aesthetic ranking of documents.

Related concepts: Evidence, Governance, Replay, Projection, Compatibility Residue.

Primary invariants: advisory/generated evidence does not become authority without explicit promotion; historical references are not current doctrine by default.

### CTIR

Definition: the resolved-turn meaning object for narration, built after authoritative mutation.

Purpose: give prompt/adaptation a stable post-mutation meaning boundary.

Not: full persisted state, prompt text, GPT output, or final-emission metadata.

Related concepts: Runtime Transaction, Domain Simulation, Prompt / Adaptation.

Primary invariants: CTIR is built after mutation; prompt consumes CTIR when present; prompt does not re-decide CTIR-owned meaning.

### Prompt / Adaptation

Definition: packaging of CTIR, approved read models, visibility, response contracts, and narrative plans into model-ready context.

Purpose: adapt runtime truth into expression constraints.

Not: domain truth, legality verdicts, bounded repair, or replay acceptance.

Related concepts: CTIR, Response Policy Contracts, Realization, Routing.

Primary invariants: prompt adapts truth; it does not create truth; planner structure does not become gate legality.

### Response Policy Contracts

Definition: shipped response shape and policy structures consumed by prompt/adaptation and final-emission validation.

Purpose: define what kind of response the model is expected to produce and the gate is expected to verify.

Not: validator verdicts, repair strategies, or gate orchestration.

Related concepts: Prompt / Adaptation, Validators, Final Emission.

Primary invariants: contracts are structure, not final pass/fail decisions.

### Realization

Definition: production of candidate expression through GPT/model I/O or governed fallback routes, including realization metadata.

Purpose: produce player-facing candidate prose without owning game truth.

Not: domain simulation, final legality, or protected replay acceptance.

Related concepts: Prompt / Adaptation, Routing, Fallback, Provenance.

Primary invariants: model output is candidate expression only; realization provenance records source/family without owning behavior.

### Opening Realization

Definition: opening-turn realization of visible basis, narrative obligations, GPT candidate text, and deterministic fallback participation.

Purpose: handle campaign start as bootstrap plus first emitted turn while preserving split ownership.

Not: a parallel structural opener authority or a collapse of opening fallback ownership axes.

Related concepts: Runtime Transaction, Prompt / Adaptation, Realization, Final Emission, Replay.

Primary invariants: opening crosses multiple owners; opening fallback fields are observations, not a single semantic owner.

### Final Emission

Definition: last-mile boundary for final player-facing text selection, legality, packaging, metadata, FEM, and sealed terminal exceptions.

Purpose: decide what can ship and make it traceable.

Not: domain truth, planner structure, ordinary semantic authoring, or protected replay schema.

Related concepts: Validators, Repair, Sanitizers, Fallback, Provenance, Projection.

Primary invariants: final text is legal, packaged, traceable; final emission should not silently invent missing meaning except sealed terminal exceptions.

### Validators

Definition: deterministic predicates that say whether candidate output satisfies declared contracts or legality constraints.

Purpose: provide pass/fail reasons and evidence.

Not: repair, scoring, final selection, fallback authorship, or domain truth.

Related concepts: Response Policy Contracts, Final Emission, Repair, Diagnostics.

Primary invariants: validators produce verdicts/evidence, not replacement output.

### Repair

Definition: bounded deterministic correction after a known failure.

Purpose: correct eligible failures without turning final emission into a general semantic author.

Not: ordinary narrative generation, planner intent, fallback-family authorship, or final gate ordering.

Related concepts: Validators, Final Emission, Sanitizers, Fallback.

Primary invariants: repair is reason-coded and bounded; final-boundary semantic repair is transitional unless sealed or legality-preserving.

### Sanitizers

Definition: cleanup/packaging boundary for internal contamination, serialized payload leakage, route-illegal stock text, and unsafe presentation artifacts.

Purpose: strip, package, drop, or recover intended player text without authoring ordinary meaning.

Not: general narrative repair or default diegetic rewrite.

Related concepts: Final Emission, Repair, Fallback, Telemetry / Lineage.

Primary invariants: strip/package/drop is permanent; legacy rewrite behavior is transitional.

### Fallback

Definition: bounded substitute behavior when normal output cannot be produced, selected, legalized, or safely shipped.

Purpose: preserve response continuity under failure while keeping authorship and selection observable.

Not: one module, one owner field, or untraceable narrative invention.

Related concepts: Realization, Final Emission, Provenance, Replay, Sanitizers.

Primary invariants: content author, selector, applicator, provenance packager, recorder, runtime diagnostic owner, and protected replay owner may differ.

### Strict-Social Emission

Definition: specialized social dialogue emission and emergency fallback seam for strict-social terminal behavior.

Purpose: keep social dialogue semantics with the social owner while final emission packages/applies legality.

Not: generic final-emission repair ownership.

Related concepts: Fallback, Final Emission, Sanitizers, Repair.

Primary invariants: strict-social semantic shaping stays with social exchange emission; gate orchestration does not become social semantic ownership.

### Provenance

Definition: metadata and trace vocabulary explaining source, owner, family, selection, application, or fallback path.

Purpose: explain finalized behavior without owning the behavior.

Not: selection logic, fallback prose authorship, or replay acceptance.

Related concepts: Authority, Fallback, Realization, Final Emission, Evidence.

Primary invariants: provenance records behavior; it does not decide behavior.

### Projection

Definition: read-side conversion of finalized runtime surfaces into diagnostic or protected observation forms.

Purpose: make runtime outputs comparable, explainable, and reviewable.

Not: runtime mutation or final-emission selection.

Related concepts: Runtime Diagnostic Projection, Protected Replay Projection, Replay, Evidence.

Primary invariants: projection reads finalized surfaces; runtime diagnostic and protected replay projection remain separate.

### Runtime Diagnostic Projection

Definition: runtime-owned read-side projection of finalized FEM/provenance into diagnostic lineage events and fields.

Purpose: explain finalized runtime metadata.

Not: protected acceptance schema or runtime behavior owner.

Related concepts: Projection, Provenance, Diagnostics, Telemetry / Lineage.

Primary invariants: diagnostic projection may feed evidence, but not live runtime selection.

### Protected Replay Projection

Definition: test/governance-owned projection defining protected observations and acceptance fields.

Purpose: lock and compare selected behavior surfaces after runtime.

Not: runtime diagnostic vocabulary owner or runtime dependency.

Related concepts: Replay, Projection, Evidence, Governance.

Primary invariants: runtime must not import protected replay acceptance structures; protected replay observes after runtime.

### Replay

Definition: observation and comparison of finalized runtime outputs, protected fields, traces, logs, and snapshots.

Purpose: preserve behavior evidence and detect drift.

Not: runtime policy, final-emission owner, or fallback selector.

Related concepts: Projection, Evidence, Governance, Diagnostics.

Primary invariants: replay dependency is one-way from runtime outputs toward evidence.

### Evidence

Definition: runtime outputs, projections, reports, diagnostics, trend artifacts, and governance records used to support architecture claims.

Purpose: let maintainers understand and justify behavior.

Not: automatically authoritative policy.

Related concepts: Canonicality, Replay, Diagnostics, Governance.

Primary invariants: evidence needs canonicality labels; advisory reports require explicit promotion before becoming authority.

### Diagnostics

Definition: explanatory information about paths, failures, drift, and runtime decisions.

Purpose: make behavior understandable and reviewable.

Not: live scoring or hidden policy unless explicitly part of a validator verdict.

Related concepts: Evidence, Projection, Telemetry / Lineage, Governance.

Primary invariants: diagnostics explain; they do not secretly decide.

### Telemetry / Lineage

Definition: runtime trace and stage-transition evidence that explains how output changed or which owner/path contributed.

Purpose: provide observability for finalized behavior.

Not: domain truth or protected acceptance by default.

Related concepts: Diagnostics, Provenance, Runtime Diagnostic Projection.

Primary invariants: lineage is explanatory and read-side unless explicitly part of runtime packaging.

### Governance

Definition: doctrine, protected replay policy, ownership ledgers, direct-owner test rules, and drift-watch constraints.

Purpose: keep architecture understandable and enforceable by review and tests.

Not: gameplay execution or runtime policy engine.

Related concepts: Ownership, Authority, Canonicality, Test Governance.

Primary invariants: governance declares and watches; it does not execute gameplay.

### Test Governance

Definition: mapping of responsibilities to direct-owner suites and typed neighbor suites.

Purpose: prevent tests from becoming rival semantic owners.

Not: runtime behavior or broad procedural command reference.

Related concepts: Ownership, Governance, Evidence.

Primary invariants: direct-owner suites own semantic assertions; neighbors are smoke, downstream, transcript, evaluator, gauntlet, or compatibility consumers.

### Compatibility Residue

Definition: tolerated historical/support surfaces such as aliases, old fields, legacy names, compatibility wrappers, or historical report references.

Purpose: preserve compatibility and evidence continuity without reopening ownership.

Not: current semantic authority by default.

Related concepts: Canonicality, Governance, Historical Vocabulary, Transitional Vocabulary.

Primary invariants: residue is explicitly non-owning unless promoted by current doctrine or protected acceptance.

### Persistence

Definition: storage and retrieval of runtime documents, logs, snapshots, envelopes, and reset/factory shapes.

Purpose: preserve finalized runtime truth and surfaces replay/evidence may later observe.

Not: transaction timing, domain simulation, or final-emission policy.

Related concepts: Runtime Transaction, Domain Simulation, Final Emission, Replay.

Primary invariants: storage owns mechanics; runtime transaction owns timing.

## 6 Transitional Vocabulary

### Final-Emission Semantic Repair Pressure

Why it exists: final emission historically kept player-facing text legal and usable under malformed, incomplete, or unsafe candidate output.

Why it should not yet disappear: current safety behavior and regression tests still protect cases where boundary correction is needed.

Retirement event: upstream layers reliably provide compliant prepared content, leaving final emission to legality, packaging, strip-only cleanup, and sealed terminal exceptions.

### Transitional Boundary Repair

Why it exists: some repair paths still reorder, synthesize, or bridge player-visible meaning to satisfy contracts.

Why it should not yet disappear: removing vocabulary before each path is classified would blur the distinction between permanent bounded repair and semantic boundary repair.

Retirement event: remaining repair modes are classified as legality-preserving, sealed exception, upstream-owned semantic synthesis, or historical compatibility.

### Transitional Fallback Vocabulary

Why it exists: fallback has multiple legitimate axes, while old runtime/replay fields compress or overlap those axes.

Why it should not yet disappear: consumers still need compatibility projection and distinct read/write meanings.

Retirement event: a consumer map and replay proof establish field precedence without losing author/selector/applicator/provenance meaning.

### Dual Fallback-Family Vocabulary

Why it exists: `fallback_family_used` and governed realization-family vocabulary answer related but not identical questions.

Why it should not yet disappear: protected replay and runtime provenance still observe both kinds of meaning.

Retirement event: field semantics are documented and consumers can rely on one durable interpretation or explicitly separate names.

### CTIR-Absent Prompt Compatibility Reads

Why it exists: prompt construction tolerates old or exceptional paths where CTIR is absent.

Why it should not yet disappear: absence behavior remains a useful guard against exceptional callers.

Retirement event: normal resolved-turn paths guarantee CTIR before prompt construction, and absence behavior is explicitly scoped.

### Opening Fallback Compatibility Fields

Why it exists: opening spans bootstrap, planning, realization, fallback, final emission, persistence, and replay.

Why it should not yet disappear: protected replay observes opening fallback owner/source/authorship compatibility fields.

Retirement event: opening handoff doctrine and protected evidence support simpler read-side projection.

### Legacy Sanitizer Rewrite Mode

Why it exists: sanitizer historically rewrote some unsafe or scaffold-like text.

Why it should not yet disappear: non-default compatibility paths and tests may still describe it.

Retirement event: live final-emission sanitizer behavior is fully represented by strip/package/drop plus explicitly owned emergency fallback seams.

### Generated / Advisory Evidence Artifact Fanout

Why it exists: stabilization and audit campaigns created many useful reports.

Why it should not yet disappear: those reports still support history, review, and trend context.

Retirement event: canonicality labels and retention conventions make each artifact's status clear.

## 7 Historical Vocabulary

Historical vocabulary is retained for compatibility, audit continuity, or old-path interpretation. It is not current architecture unless current doctrine, ownership rows, or protected acceptance explicitly promote it.

Historical vocabulary includes:

- Legacy diegetic fallback classifications.
- Historical/debug provenance module naming.
- Dated audit cycle labels and old stabilization report names.
- Dead-governance archive references.
- Strict-social and prompt/contract compatibility aliases.
- Telemetry or packet compatibility wrappers.
- Historical protected replay snapshots.
- Older generated reports not promoted to current governance.
- CTIR-absent prompt language when describing old-path tolerance.

Compatibility Residue is permanent as a classification category, but each residue instance should be read as historical/supporting unless proven current.

## 8 Concept Dependency Map

### Foundational Dependencies

```text
Canonicality
  -> Ownership
  -> Authority
  -> State Authority
  -> Runtime Transaction
```

Canonicality enables contributors to know which surfaces count as authority. Ownership and Authority apply that classification to people, modules, tests, and decision types. State Authority applies ownership/authority to mutation and read domains. Runtime Transaction coordinates the live turn using those boundaries.

### Runtime Dependencies

```text
Runtime Transaction
  -> Domain Simulation
  -> CTIR
  -> Prompt / Adaptation
  -> Realization
  -> Final Emission
  -> Persistence
```

Domain Simulation requires runtime order and state authority. CTIR requires post-mutation truth. Prompt / Adaptation requires CTIR and approved read models. Realization requires prompt context and route/model ownership. Final Emission requires candidate/prepared/fallback output. Persistence requires finalized runtime surfaces.

### Defensive Dependencies

```text
Final Emission
  -> Validators
  -> Repair
  -> Sanitizers
  -> Fallback
  -> Provenance
```

Final Emission orchestrates the boundary. Validators provide deterministic evidence. Repair consumes known failures. Sanitizers clean/package/drop artifacts. Fallback supplies bounded substitute behavior. Provenance records the explanation. These concepts intentionally overlap at the last-mile boundary because they answer different questions.

### Evidence Dependencies

```text
Finalized runtime surfaces
  -> Provenance
  -> Runtime Diagnostic Projection
  -> Protected Replay Projection
  -> Replay
  -> Evidence
  -> Diagnostics / Telemetry
  -> Governance
```

Evidence depends on finalized runtime surfaces. Projection is read-side. Replay observes after runtime. Governance consumes evidence but does not drive live behavior.

### Compatibility Dependencies

```text
Compatibility Residue
  -> Canonicality
  -> Ownership
  -> Governance
  -> Historical Vocabulary
```

Compatibility Residue depends on Canonicality and Ownership because without those concepts old paths would look like rival owners. Governance records residue status and prevents historical mechanisms from becoming accidental current architecture.

## 9 Campaign 3 Closeout Assessment

### 1. Which architectural concepts are truly foundational?

The foundational concepts are:

- Runtime Transaction
- Domain Simulation
- State Authority
- CTIR
- Final Emission
- Ownership
- Authority
- Canonicality

These define the architectural model itself. Removing or replacing them would change how the project understands runtime truth, expression, final output, evidence, and governance.

### 2. Which concepts remain essential implementation concepts?

Essential implementation concepts are:

- Prompt / Adaptation
- Response Policy Contracts
- Realization
- Opening Realization
- Routing
- Validators
- Repair as bounded deterministic correction
- Sanitizers
- Fallback
- Provenance
- Replay
- Projection
- Runtime Diagnostic Projection
- Protected Replay Projection
- Persistence
- Strict-Social Emission

These may evolve in implementation, but the architecture requires them.

### 3. Which concepts are transitional?

Transitional concepts are:

- Final-emission semantic repair pressure.
- Transitional boundary repair.
- Transitional fallback vocabulary.
- Dual fallback-family vocabulary.
- CTIR-absent prompt compatibility reads.
- Opening fallback compatibility fields.
- Legacy sanitizer rewrite mode.
- Generated/advisory evidence artifact fanout where status is not yet labeled for onboarding.

These should be treated as evolution registers, not implementation mandates.

### 4. Which concepts intentionally overlap?

Intentional overlap exists where concepts answer different questions at the same boundary:

- Final Emission overlaps Validators, Repair, Sanitizers, and Fallback because it orchestrates last-mile legality and packaging.
- Fallback overlaps Realization, Final Emission, Provenance, Replay, and Sanitizers because content author, selector, applicator, packager, recorder, and observer may differ.
- Provenance overlaps Evidence and Replay because it explains behavior that those systems observe.
- Runtime Diagnostic Projection overlaps Protected Replay Projection as read-side projections, but they have different authority.
- Prompt / Adaptation overlaps CTIR because prompt consumes CTIR, but prompt is not CTIR.
- Governance overlaps Ownership and Canonicality because governance declares them, but it does not execute runtime.

These overlaps are architectural, not proof of duplicate ownership.

### 5. Which concepts are historical?

Historical concepts include:

- Legacy diegetic fallback classifications.
- Historical/debug provenance naming.
- Older audit cycle labels and dated reports.
- Dead-governance archives.
- Compatibility aliases and wrappers.
- Historical generated/advisory artifacts.
- Old CTIR-absent prompt language when used only as compatibility tolerance.

They are retained for compatibility and interpretability, not as current semantic owners.

### 6. What permanent vocabulary should future contributors use?

Future contributors should use:

- Runtime Transaction
- Domain Simulation
- State Authority
- Ownership
- Authority
- Canonicality
- CTIR
- Prompt / Adaptation
- Response Policy Contracts
- Realization
- Opening Realization
- Routing
- Final Emission
- Validators
- Bounded Repair
- Sanitizers
- Fallback with multi-axis ownership
- Strict-Social Emission
- Provenance
- Projection
- Runtime Diagnostic Projection
- Protected Replay Projection
- Replay
- Evidence
- Diagnostics
- Telemetry / Lineage
- Governance
- Test Governance
- Persistence
- Compatibility Residue

When discussing fallback, contributors should use specific axes: content author, selector, applicator, provenance packager, recorder, runtime diagnostic owner, and protected replay owner.

When discussing evidence, contributors should include canonicality: runtime truth, runtime projection, protected acceptance, governance contract, generated artifact, advisory artifact, or historical reference.

### 7. Should implementation priorities change because of Campaign 3?

No implementation priorities should change directly because of Campaign 3.

Campaign 3 was conceptual. It establishes vocabulary and doctrine for future work. It does not authorize refactoring, simplification, concept merging, feature expansion, fallback-field collapse, replay/projection merger, or final-emission cleanup by itself.

Future implementation campaigns can use the vocabulary to scope work more precisely, but Campaign 3's closeout is documentation and conceptual stabilization only.

### Campaign Success

Conceptual ambiguity has been reduced to bounded transition registers. The major concepts are stable, their overlaps are intentional and named, and future implementation can rely on this vocabulary.

Campaign 3 answered the original questions:

- Foundational concepts have been identified.
- Essential implementation concepts have been separated from foundational concepts.
- Transitional and historical vocabulary have been separated.
- Intentional overlap has been explained.
- Permanent vocabulary has been established.
- Future contributors have a concept map and glossary to avoid rediscovery.

## 10 Campaign Recommendation

Recommendation: **Campaign 3 Complete**.

Reason:

- AR-BA completed the concept inventory and ambiguity register.
- AR-BB reconciled the defensive runtime cluster.
- AR-BC classified every major concept by long-term role.
- AR-BD consolidates the permanent concept map, lifecycle, layer model, vocabulary, transition register, historical register, and closeout answers.

No final refinement is required before closing Campaign 3.

Recommended transition: begin Campaign 4 as a documentation placement and refinement-readiness campaign, not Controlled Feature Expansion.

Recommended first Architecture Reconciliation block for Campaign 4:

**AR-CA - Permanent Doctrine Placement and Contributor Onboarding Map**

Suggested AR-CA purpose:

- Place the permanent vocabulary into durable contributor-facing documentation.
- Cross-reference AR-AD, AR-AF, AR-BA through AR-BD without creating competing doctrine.
- Identify which existing docs should be first-stop onboarding references.
- Preserve transitional and historical registers as context, not implementation tasks.

## Files Recommended for External Review

### Required

- `AR-BD_concept_map_synthesis_and_campaign_closeout.md` - final Campaign 3 synthesis and closeout.
- `AR-BC_permanent_transitional_historical_concept_classification.md` - controlling classification table and individual concept reviews.
- `AR-BB_defensive_runtime_boundary_reconciliation.md` - defensive runtime boundary reconciliation.
- `AR-BA_concept_inventory_and_responsibility_discovery.md` - original Campaign 3 concept inventory.
- `AR-AF_architecture_reconciliation_synthesis.md` - concise architecture baseline and invariants.
- `AR-AD_target_architecture_doctrine.md` - target doctrine, layer model, canonicality, and multi-axis ownership.

### Strongly Recommended

- `AR-AB_runtime_authority_and_replay_boundary_map.md` - runtime, replay, and fallback ownership maps.
- `docs/architecture_ownership_ledger.md` - repo-facing ownership declarations.
- `docs/final_emission_ownership_convergence.md` - final-emission repair and semantic mutation doctrine.
- `docs/validation_layer_separation.md` - truth/structure/expression/legality/evaluator layer contract.
- `docs/testing/protected_replay_manifest.md` - protected replay policy.
- `docs/testing/replay_governance_authority.md` - replay governance authority boundary.
- `docs/ctir_prompt_adapter_architecture.md` - CTIR/prompt adapter doctrine.
- `docs/state_authority_model.md` - state authority model and guard adoption.

### Optional

- `AR-AA_architectural_mapping_discovery.md` - original broad discovery reference.
- `AR-AC_architectural_ownership_reconciliation.md` - ownership reconciliation rationale.
- `AR-AE_architecture_conformance_assessment.md` - conformance context.
- `AR-AI_final_vision_compatibility_closeout.md` - Campaign 2 closeout guardrail.
- `docs/architecture_audit_readme.md` - interpretation guidance for audit evidence and residue.
- Current generated/advisory reports under `artifacts/golden_replay/` and `docs/audits/` when read through canonicality labels.

Minimum onboarding set:

1. `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
2. `AR-BC_permanent_transitional_historical_concept_classification.md`
3. `AR-AF_architecture_reconciliation_synthesis.md`
4. `AR-AD_target_architecture_doctrine.md`
5. `docs/architecture_ownership_ledger.md`

## Evidence Standards Applied

Prior Campaign 3 reports: AR-BA supplied the inventory; AR-BB reconciled the defensive runtime cluster; AR-BC supplied long-term classification.

Doctrine evidence: AR-AD, AR-AF, ownership ledger, validation-layer separation, final-emission convergence, state authority model, CTIR/prompt adapter doctrine, protected replay governance.

Implementation evidence: the synthesis relies on implementation evidence already cited by AR-BA through AR-BC, including state authority, realization authority/provenance, fallback provenance, final-emission gate/validators/repairs, sanitizer, final-emission replay projection, and upstream response repairs.

Test evidence: the synthesis relies on direct-owner and governance tests already cited by AR-BA through AR-BC, especially state authority, final-emission boundary convergence, replay boundary governance, validator/repair/sanitizer direct-owner suites, and ownership/test governance suites.

No new architectural theories are introduced here. This document consolidates prior doctrine, implementation evidence, tests, and Campaign 3 findings into the permanent conceptual model.
