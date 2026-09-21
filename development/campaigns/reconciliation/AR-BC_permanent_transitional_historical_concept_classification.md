# AR-BC Permanent, Transitional, and Historical Concept Classification

Campaign: Campaign 3 - Concept Reconciliation

Scope: architectural concept classification using AR-BA concept inventory, AR-BB defensive runtime reconciliation, target architecture doctrine, ownership ledger, final-emission convergence doctrine, validation-layer doctrine, representative implementation surfaces, and direct-owner/governance tests.

Non-goals: implementation cleanup, terminology simplification for aesthetics, concept merging, runtime refactor planning, Campaign 2 reopening, feature planning.

## 1 Executive Summary

The architecture has reached a mature conceptual state. Its core vocabulary is no longer exploratory: runtime transaction, domain simulation, state authority, CTIR, prompt/adaptation, realization, final emission, replay, projection, provenance, ownership, authority, canonicality, and governance all have durable architectural jobs and should be treated as permanent vocabulary for future contributors.

The strongest long-term pattern is a single forward runtime chain surrounded by explicit evidence and governance:

```text
Runtime request
  -> authoritative domain simulation
  -> CTIR resolved-turn meaning
  -> prompt/adaptation
  -> GPT/model realization
  -> final emission
  -> persistence/log/response
  -> runtime diagnostics
  -> protected replay/evidence
  -> governance/advisory review
```

AR-BB changed the classification of the defensive runtime cluster. Validators, sanitizers, fallback, and final emission are not historical cleanup residue. They are permanent concepts. Repair is also permanent as bounded deterministic correction, but final-boundary semantic repair is transitional. The remaining ambiguity is therefore not broad conceptual overlap; it is mode-level classification inside repair/fallback/sanitizer paths.

The project's transitional vocabulary is concentrated in compatibility-shaped fields and boundary semantic mutation: dual fallback-family vocabulary, CTIR-absent prompt compatibility reads, opening fallback compatibility fields, legacy diegetic fallback classifications, historical/debug module names, generated/advisory evidence fanout, and final-emission semantic repair pressure.

The project's historical vocabulary is narrow. Historical residue mostly exists to preserve compatibility, past audit trails, and older names. It should not be treated as current architecture unless explicitly promoted by doctrine or protected acceptance.

Campaign 3 is approaching completion. One concept-map synthesis cycle should follow this classification, because the permanent/transitional taxonomy is now stable enough to consolidate into a contributor-facing map. Recommended next block: **AR-BD - Concept Map Synthesis and Doctrine Placement**.

## 2 Concept Classification Table

| Concept | Classification | Secondary Role | Confidence | Expected Lifetime |
|---|---|---|---|---|
| Runtime Transaction | Foundational | Essential runtime orchestration | High | Permanent |
| Domain Simulation | Foundational | State-authority consumer | High | Permanent |
| State Authority | Foundational | Governance contract | High | Permanent |
| Ownership | Foundational | Governance vocabulary | High | Permanent |
| Authority | Foundational | Layer/permission vocabulary | High | Permanent |
| Routing | Essential | Supporting diagnostics | Medium-high | Permanent, with field vocabulary evolution |
| CTIR | Foundational | Prompt-adapter dependency | High | Permanent |
| Prompt / Adaptation | Essential | Planner layer | High | Permanent |
| Realization | Essential | Expression and fallback authority | High | Permanent |
| Opening Realization | Essential | Transitional compatibility pressure | Medium-high | Permanent boundary, evolving implementation |
| Final Emission | Foundational | Defensive runtime orchestration | High | Permanent |
| Replay | Essential | Evidence and protected acceptance | High | Permanent |
| Projection | Essential | Diagnostic/protected read model | High | Permanent |
| Provenance | Essential | Evidence substrate | High | Permanent |
| Evidence | Supporting | Governance input | High | Permanent, with canonicality labels |
| Validators | Essential | Defensive gate layer | High | Permanent |
| Repair | Essential | Transitional boundary semantics | High | Permanent concept; some paths transitional |
| Sanitizers | Essential | Defensive packaging/cleanup | High | Permanent concept; legacy rewrite mode transitional |
| Fallback | Essential | Multi-axis runtime safety | High | Permanent concept; some vocabulary transitional |
| Diagnostics | Supporting | Evidence substrate | High | Permanent |
| Telemetry / Lineage | Supporting | Provenance-adjacent diagnostics | High | Permanent |
| Governance | Supporting | Doctrine and drift-watch | High | Permanent |
| Canonicality | Foundational | Evidence classification | High | Permanent |
| Compatibility Residue | Historical | Transitional guardrail | High | Long-lived as a category; individual residues retire |
| Persistence | Essential | Runtime truth storage | High | Permanent |
| Response Policy Contracts | Essential | Planner/gate contract structure | High | Permanent |
| Strict-Social Emission | Essential | Fallback/repair special owner | Medium-high | Permanent seam |
| Runtime Diagnostic Projection | Essential | Supporting diagnostics | High | Permanent |
| Protected Replay Projection | Essential | Governance/protected acceptance | High | Permanent |
| Test Governance | Supporting | Ownership enforcement | High | Permanent |
| Advisory / Generated Artifacts | Supporting | Historical evidence fanout | Medium-high | Permanent category; individual artifacts age out |

## 3 Individual Concept Reviews

### Runtime Transaction

Primary classification: **Foundational**.

Secondary role: essential runtime orchestration.

Why it exists: it preserves one coherent turn from request entry through authoritative mutation, CTIR placement, GPT/retry/fallback, final emission, persistence, logging, and response construction.

Architectural questions answered: who owns the live turn sequence; when does mutation happen; when is CTIR attached; when is final text sealed; when may replay observe output.

Protected invariants: one turn has one transaction spine; runtime truth precedes narration; persistence and replay observe finalized outputs, not partial candidate state.

Dependencies: domain simulation, state authority, CTIR, prompt/adaptation, realization, fallback, final emission, persistence, diagnostics.

Dependents: CTIR timing, prompt construction, final emission, replay inputs, provenance/evidence, API response invariants.

Expected lifetime: permanent.

Implementation impact: implementation helpers may evolve, but the concept itself is stable unless the architecture stops being a single-turn transaction model.

Evidence: AR-AD defines a turn as one transaction spine owned by `game.api`; AR-AF lists the turn transaction as the baseline model; AR-AB maps start campaign and shared resolved-turn flow through `game.api`; tests around turn pipeline, replay boundary, and state authority assume this ordering.

### Domain Simulation

Primary classification: **Foundational**.

Secondary role: state-authority consumer.

Why it exists: it is where game truth is resolved before narration.

Architectural questions answered: what actually happened; which domain owns which outcome; which modules may mutate authoritative state.

Protected invariants: GPT text is not truth; prompt and final emission do not mutate engine domains; domain owners decide simulation outcomes before expression.

Dependencies: runtime transaction, state authority, storage/runtime state.

Dependents: CTIR, prompt/adaptation, realization, final emission consistency, replay evidence.

Expected lifetime: permanent.

Implementation impact: domain modules may change as features evolve, but the concept of authoritative simulation remains fixed.

Evidence: AR-AD and validation-layer doctrine define the engine layer as authoritative truth; AR-AF names domain modules as simulation owners; `docs/state_authority_model.md` and `game/state_authority.py` back the mutation vocabulary; `tests/test_state_authority.py` guards pseudo-owner and cross-domain writes.

### State Authority

Primary classification: **Foundational**.

Secondary role: governance contract.

Why it exists: it declares state domains, read relationships, mutation guards, and cross-domain write exceptions.

Architectural questions answered: who may mutate a domain; who may read across domains; which cross-domain writes are intentionally allowed.

Protected invariants: no unauthorized state mutation; state-authority registry is not a persistence engine; prompts/GPT/final emission are not hidden domain owners.

Dependencies: ownership, authority, domain simulation.

Dependents: domain modules, governance tests, mutation traces, architecture audits.

Expected lifetime: permanent.

Implementation impact: domain rows can change, but the state-authority concept should not disappear.

Evidence: `game/state_authority.py`, `tests/test_state_authority.py`, `docs/architecture_ownership_ledger.md`, and AR-AF all classify state authority as registry and guard vocabulary, not universal state.

### Ownership

Primary classification: **Foundational**.

Secondary role: governance vocabulary.

Why it exists: it prevents responsibility smearing across runtime modules, direct-owner tests, downstream suites, compatibility residue, and governance artifacts.

Architectural questions answered: who owns a concern; who consumes it; which tests are direct-owner coverage; which paths are compatibility support only.

Protected invariants: direct-owner tests are not replaced by downstream suites; compatibility residue does not reopen co-equal ownership; governance declarations are targets, not proof code is already clean.

Dependencies: authority, governance, canonicality.

Dependents: test governance, ownership ledger, audit tools, future documentation.

Expected lifetime: permanent.

Implementation impact: owner rows may change, but ownership as a concept remains foundational.

Evidence: `docs/architecture_ownership_ledger.md` states the ownership model and standard seam presentation; AR-AD defines multi-axis ownership; tests such as ownership registry and gate/replay boundary governance enforce placement and dependency discipline.

### Authority

Primary classification: **Foundational**.

Secondary role: layer/permission vocabulary.

Why it exists: it distinguishes the permission to decide, mutate, select, package, observe, or govern from merely touching a value.

Architectural questions answered: who decides behavior; who writes metadata; who only observes; who is allowed to mutate truth.

Protected invariants: GPT owns expression, not truth; provenance explains behavior without selecting it; governance is not gameplay; replay is read-side.

Dependencies: ownership, state authority, validation-layer separation, canonicality.

Dependents: runtime transaction, domain simulation, final emission, fallback, provenance, replay.

Expected lifetime: permanent.

Implementation impact: authority profiles and registries can evolve, but authority is a core architectural language.

Evidence: AR-AD's multi-axis ownership doctrine, AR-AB's runtime authority ledger, `game/realization_authority.py`, `game/state_authority.py`, and `docs/testing/replay_governance_authority.md`.

### Routing

Primary classification: **Essential**.

Secondary role: supporting diagnostics.

Why it exists: it selects runtime/model/interaction/final paths without necessarily owning truth or final behavior.

Architectural questions answered: which path was chosen; which model or response route applied; what route metadata downstream layers should preserve.

Protected invariants: route selection is not domain truth; routing metadata must not become a hidden replay or governance policy source; final route observations remain evidence unless promoted.

Dependencies: runtime transaction, prompt/adaptation, realization, fallback, final emission.

Dependents: prompt construction, GPT/model calls, retry/fallback, final emission metadata, replay projection.

Expected lifetime: permanent, with vocabulary evolution.

Implementation impact: route fields and modules may consolidate or split, but path-selection vocabulary remains necessary.

Evidence: AR-BA identifies routing/dispatch ambiguity; AR-AD classifies model routing as GPT/model I/O and route metadata; AR-AB maps API route, GPT retry, and final emission paths.

### CTIR

Primary classification: **Foundational**.

Secondary role: prompt-adapter dependency.

Why it exists: it is the resolved-turn meaning boundary for narration after authoritative mutation.

Architectural questions answered: what meaning should narration express; where does prompt construction get turn meaning; how is retry-stable meaning preserved.

Protected invariants: CTIR is built after mutation and hygiene; prompt context consumes CTIR when present; prompt construction does not re-decide CTIR-owned semantics.

Dependencies: runtime transaction, domain simulation, state authority.

Dependents: prompt/adaptation, realization, final-emission consistency, replay evidence.

Expected lifetime: permanent.

Implementation impact: CTIR shape may evolve, but a resolved-turn meaning boundary remains foundational.

Evidence: `docs/ctir_prompt_adapter_architecture.md`, ownership ledger CTIR section, AR-AD doctrine, AR-AF baseline, and CTIR direct-owner tests named in the ownership ledger.

### Prompt / Adaptation

Primary classification: **Essential**.

Secondary role: planner layer.

Why it exists: it packages approved runtime truth, CTIR, visibility, response contracts, and narrative plans into model context.

Architectural questions answered: what does GPT get to see; what structure must candidate expression satisfy; how do prompt bundles adapt truth without owning truth.

Protected invariants: prompt context is not domain truth; prompt context is not a second CTIR owner; prompt contracts shape model output but do not own final legality verdicts.

Dependencies: runtime transaction, CTIR, response policy contracts, domain read models, routing.

Dependents: realization, validators, final emission, replay evidence.

Expected lifetime: permanent.

Implementation impact: prompt builders and plans may change, but adaptation remains essential.

Evidence: validation-layer doctrine names planner responsibilities; ownership ledger names `game.prompt_context.py` and contract owners; AR-AD states prompt construction adapts truth but does not create it.

### Realization

Primary classification: **Essential**.

Secondary role: expression and fallback authority.

Why it exists: it turns prompt/model/fallback routes into candidate player-facing expression and records governed realization/fallback vocabulary.

Architectural questions answered: who authored candidate prose; which fallback family applies; what realization profile governs metadata.

Protected invariants: GPT owns expression, not truth; realization provenance records source/family without mutating behavior; fallback families require governed provenance where applicable.

Dependencies: prompt/adaptation, routing, fallback, provenance.

Dependents: final emission, replay projection, evidence, diagnostics.

Expected lifetime: permanent.

Implementation impact: model call mechanics and fallback families may evolve; realization as expression boundary remains.

Evidence: AR-AD and AR-AF classify GPT/model routing as expression; `game/realization_authority.py` and `game/realization_provenance.py` define authority/provenance vocabulary; AR-BB preserves fallback/provenance separation.

### Opening Realization

Primary classification: **Essential**.

Secondary role: transitional compatibility pressure.

Why it exists: campaign start is both bootstrap and first emitted turn; opening realization curates public diegetic basis and participates in deterministic fallback without owning the whole opening structure.

Architectural questions answered: where opening visible facts enter narration; how bootstrap crosses planning, realization, fallback, final emission, persistence, and replay.

Protected invariants: opening realization is not a parallel structural opener authority; opening fallback content/source/owner fields remain observable without collapsing ownership axes.

Dependencies: runtime transaction, domain simulation, prompt/adaptation, final emission, fallback, replay.

Dependents: start-campaign response, opening fallback compatibility fields, protected replay observations.

Expected lifetime: permanent boundary, evolving implementation.

Implementation impact: compatibility field shapes may change, but opening as a multi-owner handoff remains architecturally necessary.

Evidence: AR-AB start campaign flow and opening scene realization row; AR-AD intentional overlap table; AR-BA transitional register for opening fallback compatibility fields.

### Final Emission

Primary classification: **Foundational**.

Secondary role: defensive runtime orchestration.

Why it exists: it is the last-mile boundary that decides what final text, metadata, and FEM may reach the player and downstream observers.

Architectural questions answered: what can ship; which text is final; how legality, selection, packaging, sanitizer output, repair metadata, and provenance are recorded.

Protected invariants: final text is legal, packaged, traceable, and consistent with upstream authorized meaning; final emission should not silently invent missing meaning except explicitly sealed terminal exceptions.

Dependencies: realization, validators, repair, sanitizers, fallback, provenance, response contracts.

Dependents: persistence, logs, response payload, runtime diagnostic projection, protected replay, evidence.

Expected lifetime: permanent.

Implementation impact: helper functions and repair modes may change; final emission remains a foundational architectural boundary.

Evidence: AR-AD, AR-AF, AR-BB, ownership ledger final-emission sections, `docs/final_emission_ownership_convergence.md`, and boundary convergence tests all make this concept durable.

### Replay

Primary classification: **Essential**.

Secondary role: evidence and protected acceptance.

Why it exists: it observes finalized runtime outputs to detect drift, protect known behavior, and support architecture evidence.

Architectural questions answered: what did a turn produce; which fields are protected; what drift is acceptable; what evidence supports future changes.

Protected invariants: replay dependency is one-way; runtime must not import protected replay acceptance structures; protected replay observes behavior but does not own runtime behavior.

Dependencies: final emission, projection, evidence, governance, canonicality.

Dependents: protected acceptance, drift reports, governance tests, advisory artifacts.

Expected lifetime: permanent.

Implementation impact: runner/projection details may evolve, but replay as protected observation remains essential.

Evidence: AR-AB replay boundary map, AR-AD doctrine, `docs/testing/protected_replay_manifest.md`, `docs/testing/replay_governance_authority.md`, and `tests/test_replay_boundary_governance.py`.

### Projection

Primary classification: **Essential**.

Secondary role: diagnostic/protected read model.

Why it exists: it converts finalized runtime surfaces into diagnostic lineage and protected observation rows.

Architectural questions answered: how are finalized metadata/FEM/log/snapshot surfaces read; which projection owns runtime diagnostics; which projection owns protected acceptance.

Protected invariants: runtime diagnostic projection and protected replay projection remain separate; projection reads and explains, it does not mutate runtime output.

Dependencies: final emission, provenance, replay, evidence.

Dependents: diagnostics, protected replay, governance/advisory reports.

Expected lifetime: permanent.

Implementation impact: read helpers may change, but projection remains essential because evidence requires stable read models.

Evidence: AR-AB and AR-AD explicitly split `game.final_emission_replay_projection` from golden replay projection helpers; replay boundary governance tests lock the direction.

### Provenance

Primary classification: **Essential**.

Secondary role: evidence substrate.

Why it exists: it records why an output, fallback, selection, family, or repair path exists without owning the behavior it explains.

Architectural questions answered: who authored the content; who selected it; who packaged the evidence; why was fallback used.

Protected invariants: provenance does not select fallback prose; provenance does not own runtime behavior; provenance fields should preserve multi-axis ownership.

Dependencies: authority, fallback, realization, final emission, canonicality.

Dependents: replay projection, diagnostics, evidence reports, governance.

Expected lifetime: permanent.

Implementation impact: field names and packagers may evolve; provenance as behavior explanation is durable.

Evidence: AR-AF invariant "provenance explains behavior without owning behavior"; AR-BB fallback/provenance analysis; `game/realization_provenance.py`; `game/fallback_provenance_debug.py`.

### Evidence

Primary classification: **Supporting**.

Secondary role: governance input.

Why it exists: it provides observations, reports, diagnostics, snapshots, recurrence records, and audit outputs used to understand behavior.

Architectural questions answered: what supports a claim; which artifacts are runtime truth, protected acceptance, generated, advisory, or historical.

Protected invariants: evidence does not automatically become authority; generated/advisory artifacts require explicit promotion before becoming protected or governance authority.

Dependencies: replay, projection, provenance, diagnostics, canonicality.

Dependents: governance, audit reports, campaign decisions, external review.

Expected lifetime: permanent category, with individual artifacts aging.

Implementation impact: report sets may change; evidence classification remains necessary.

Evidence: AR-AD canonicality index; AR-AF evidence model; AR-BA evidence/diagnostics ambiguity register.

### Validators

Primary classification: **Essential**.

Secondary role: defensive gate layer.

Why it exists: validators answer whether a candidate satisfies deterministic legality or contract predicates.

Architectural questions answered: does this candidate pass; why did it fail; what evidence can repair/gate logic consume.

Protected invariants: validators do not repair, score, author missing facts, select final output, or own runtime truth.

Dependencies: response contracts, final emission, candidate text, prompt artifacts.

Dependents: repair, final emission, diagnostics, tests.

Expected lifetime: permanent.

Implementation impact: predicate functions may change, but validation as deterministic legality remains.

Evidence: AR-BB responsibility profile; `docs/validation_layer_separation.md`; `game/final_emission_validators.py`; direct-owner tests for final-emission validators.

### Repair

Primary classification: **Essential**.

Secondary role: transitional boundary semantics.

Why it exists: repair provides bounded deterministic alteration after a known failure, preferably legality-preserving.

Architectural questions answered: can a failed condition be corrected safely; where should semantic synthesis live; what metadata records repair.

Protected invariants: repair must be reason-coded and bounded; final-boundary repair must not become silent semantic completion; upstream-prepared emission should carry contract-shaped fallback prose when meaning is needed.

Dependencies: validators, final emission, response contracts, upstream-prepared payloads, sanitizer/fallback seams.

Dependents: final emission, diagnostics, replay projection, boundary tests.

Expected lifetime: permanent concept; specific semantic boundary paths are transitional.

Implementation impact: repair implementations are expected to change more than the concept. Legality-preserving repair remains; final-emission semantic repair pressure should shrink as upstream ownership matures.

Evidence: AR-BB classifies repair as distinct and mixed; ownership ledger names final-emission repair ownership as transitional; final-emission convergence doctrine separates legality/packaging from semantic mutation; boundary convergence tests lock no silent boundary synthesis.

### Sanitizers

Primary classification: **Essential**.

Secondary role: defensive packaging/cleanup.

Why it exists: sanitizers remove internal contamination, serialized payload leakage, unsafe prefixes, route-illegal stock text, and unrecoverable presentation artifacts.

Architectural questions answered: can unsafe or non-player-facing presentation artifacts be stripped or packaged; what lineage records sanitizer action.

Protected invariants: strip/package/drop is permanent; ordinary diegetic rewriting at the final boundary is transitional unless explicitly owned by a specialized seam.

Dependencies: final emission, candidate text, sanitizer context, strict-social fallback where applicable.

Dependents: final emission, runtime lineage, replay projection, diagnostics.

Expected lifetime: permanent concept; legacy rewrite modes transitional.

Implementation impact: sanitizer internals can narrow, but the cleanup boundary remains necessary.

Evidence: AR-BB sanitizer profile; `game/output_sanitizer.py` default strip-only behavior; final-emission convergence doctrine; sanitizer direct-owner tests and boundary convergence tests.

### Fallback

Primary classification: **Essential**.

Secondary role: multi-axis runtime safety.

Why it exists: fallback supplies bounded substitute behavior when normal output cannot be produced, selected, legalized, or safely shipped.

Architectural questions answered: what happens under upstream/model/gate/sanitizer/opening/strict-social failure; who authored fallback content; who selected/applied/recorded it.

Protected invariants: fallback content author, selector, applicator, provenance packager, recorder, runtime diagnostic owner, and protected replay owner may differ; fallback projection must not become runtime authority.

Dependencies: runtime transaction, realization, final emission, sanitizers, provenance, replay.

Dependents: response continuity, final emission, provenance, diagnostics, replay evidence.

Expected lifetime: permanent concept; dual vocabulary and legacy families transitional.

Implementation impact: fallback paths and fields may evolve, but bounded substitute behavior remains essential.

Evidence: AR-AB fallback ownership map; AR-AF multi-axis fallback invariant; AR-BB fallback responsibility profile; `game/realization_authority.py`, `game/fallback_provenance_debug.py`, and fallback behavior tests.

### Diagnostics

Primary classification: **Supporting**.

Secondary role: evidence substrate.

Why it exists: diagnostics explain runtime behavior, failure modes, drift, lineage, and governance findings.

Architectural questions answered: why did this happen; which path was used; what changed; where should maintainers look.

Protected invariants: diagnostics may explain but must not silently decide behavior; diagnostic heuristics are not live evaluator scores unless explicitly within a validator's pass/fail contract.

Dependencies: projection, telemetry/lineage, evidence, governance.

Dependents: audit reports, replay analysis, maintainer review.

Expected lifetime: permanent.

Implementation impact: diagnostic shapes may change; diagnostic/explanatory support remains necessary.

Evidence: AR-BA ambiguity register; AR-BB validator/diagnostic distinctions; validation-layer doctrine's evaluator read-only boundary.

### Telemetry / Lineage

Primary classification: **Supporting**.

Secondary role: provenance-adjacent diagnostics.

Why it exists: telemetry and lineage provide compact runtime traces, stage transitions, and read-side lineage events.

Architectural questions answered: what stages changed output; which owner/path contributed; what trace explains a final surface.

Protected invariants: lineage/telemetry explain stage movement but do not own domain truth or protected acceptance by default.

Dependencies: runtime transaction, final emission, provenance, projection.

Dependents: diagnostics, replay, evidence reports.

Expected lifetime: permanent.

Implementation impact: event names and wrappers can change, but observability remains.

Evidence: ownership ledger stage diff telemetry section; AR-AB runtime lineage projection row; AR-AD canonicality index.

### Governance

Primary classification: **Supporting**.

Secondary role: doctrine and drift-watch.

Why it exists: governance declares target ownership, protected replay policy, dependency direction, direct-owner suites, and audit discipline.

Architectural questions answered: what is the doctrine; what is protected; what should tests enforce; what is merely advisory.

Protected invariants: governance is not gameplay; governance docs/tests must not become runtime policy engines; audit tools are maintainer aids, not semantic proof.

Dependencies: ownership, authority, canonicality, evidence.

Dependents: future architecture cycles, test placement, protected replay policy, external review.

Expected lifetime: permanent.

Implementation impact: documents and tests may move, but governance remains a durable support layer.

Evidence: AR-AD governance layer; AR-AF governance model; ownership ledger; protected replay governance docs and tests.

### Canonicality

Primary classification: **Foundational**.

Secondary role: evidence classification.

Why it exists: it says which surfaces are runtime truth, runtime projection, protected acceptance, governance contract, generated artifact, advisory artifact, or historical reference.

Architectural questions answered: which evidence can decide behavior; which docs are doctrine; which artifacts are advisory; which reports are historical.

Protected invariants: advisory/generated artifacts require explicit promotion; runtime truth, protected acceptance, and governance contracts remain distinct.

Dependencies: governance, evidence, replay, projection.

Dependents: documentation priorities, artifact retention, external review, campaign synthesis.

Expected lifetime: permanent.

Implementation impact: canonicality labels may be refined, but the category is foundational to avoiding evidence/authority confusion.

Evidence: AR-AD canonicality index; AR-AF evidence model; AR-BA ambiguity and transitional registers.

### Compatibility Residue

Primary classification: **Historical**.

Secondary role: transitional guardrail.

Why it exists: it preserves old read paths, field names, helper aliases, debug module names, protected observations, and historical evidence until consumers no longer depend on them.

Architectural questions answered: why does this old-looking surface remain; is it an active owner or tolerated support path; what would retire it.

Protected invariants: compatibility residue must not reopen co-equal ownership; residue is support unless explicitly promoted.

Dependencies: ownership, canonicality, replay, evidence.

Dependents: legacy tests, protected replay compatibility, older reports, external review.

Expected lifetime: the category is long-lived; individual residues should expire only after clear dependency retirement.

Implementation impact: individual residue can disappear, but the classification category should remain in doctrine.

Evidence: ownership ledger standard seam presentation; validation-layer residue docs; AR-BA transitional/historical register; AR-BB dual fallback-family and legacy diegetic fallback discussion.

### Persistence

Primary classification: **Essential**.

Secondary role: runtime truth storage.

Why it exists: it stores and retrieves runtime documents, logs, snapshots, envelopes, and reset/factory shapes.

Architectural questions answered: what state is durable; where logs come from; which surfaces replay may read later.

Protected invariants: storage owns mechanics, not transaction timing, domain truth, or final emission policy.

Dependencies: runtime transaction, domain simulation, final emission.

Dependents: replay, evidence, API response reconstruction, governance reports.

Expected lifetime: permanent.

Implementation impact: storage implementation may change; persistence remains essential.

Evidence: AR-AD persistence layer; AR-AF layer model; AR-AB start-campaign persistence/log flow.

### Response Policy Contracts

Primary classification: **Essential**.

Secondary role: planner/gate contract structure.

Why it exists: it defines shipped response-policy shapes that prompt/adaptation and final-emission validators consume.

Architectural questions answered: what response type/shape is expected; what contract does GPT attempt; what legality should gate verify.

Protected invariants: contracts are structure/read-side ownership, not validator verdicts, repair strategies, or gate ordering.

Dependencies: prompt/adaptation, CTIR, final emission, validators.

Dependents: validators, repair, final emission, prompt tests.

Expected lifetime: permanent.

Implementation impact: contract shapes evolve with product behavior, but the concept remains essential.

Evidence: ownership ledger response policy contracts section; validation-layer doctrine planner/gate split; downstream tests named in the ledger.

### Strict-Social Emission

Primary classification: **Essential**.

Secondary role: fallback/repair special owner.

Why it exists: strict-social dialogue has specialized legality and fallback shaping that should not be silently owned by generic final-emission repair.

Architectural questions answered: who owns terminal strict-social dialogue semantics; where social emergency fallback text comes from; when gate only packages/applies.

Protected invariants: strict-social content shaping stays with social exchange emission; final emission may orchestrate and seal but should not become the semantic owner.

Dependencies: domain/social simulation, prompt contracts, final emission, sanitizer/fallback.

Dependents: final emission, sanitizer fallback, replay projection, social tests.

Expected lifetime: permanent seam.

Implementation impact: specific social fallback lines may change; the specialized owner concept remains.

Evidence: ownership ledger strict-social seam; final-emission convergence doctrine; AR-BB sanitizer/fallback profiles; social exchange emission direct-owner tests.

### Runtime Diagnostic Projection

Primary classification: **Essential**.

Secondary role: supporting diagnostics.

Why it exists: it projects finalized FEM/provenance into runtime lineage events and diagnostic fields.

Architectural questions answered: what does runtime metadata say after finalization; how do selection/content/fallback/repair owner splits appear in diagnostics.

Protected invariants: runtime diagnostic projection reads finalized surfaces; it is not protected acceptance and not runtime behavior.

Dependencies: final emission, provenance, telemetry/lineage, projection.

Dependents: protected replay may consume diagnostics; advisory reports; external review.

Expected lifetime: permanent.

Implementation impact: projection helpers can change, but the read-side runtime diagnostic concept remains.

Evidence: AR-AB runtime diagnostic projection map; AR-AD replay/evidence layer; replay boundary governance tests.

### Protected Replay Projection

Primary classification: **Essential**.

Secondary role: governance/protected acceptance.

Why it exists: it defines protected observation rows, protected field paths, scenario status, and acceptance comparisons.

Architectural questions answered: what does protected replay lock; which observations are accepted; which drift matters.

Protected invariants: protected projection may consume runtime outputs/diagnostics but must not feed runtime; protected fields are test/governance authority only.

Dependencies: replay, projection, evidence, governance.

Dependents: protected replay tests, trend reports, drift analysis.

Expected lifetime: permanent.

Implementation impact: field lists may change under governance, but protected acceptance projection remains.

Evidence: AR-AB protected replay projection section; `docs/testing/protected_replay_manifest.md`; replay governance tests.

### Test Governance

Primary classification: **Supporting**.

Secondary role: ownership enforcement.

Why it exists: it maps live invariant responsibilities to direct-owner suites and typed neighbors so tests do not become rival semantic owners.

Architectural questions answered: where should assertions live; which suites are smoke/downstream/compatibility; what is the direct owner.

Protected invariants: test inventory governance is not runtime behavior; downstream/compatibility tests must not become direct-owner suites by accumulation.

Dependencies: ownership, governance, evidence.

Dependents: future tests, architecture audits, CI governance checks.

Expected lifetime: permanent.

Implementation impact: test files may move, but direct-owner governance remains important.

Evidence: ownership ledger test inventory section; validation-layer doctrine test ownership notes; ownership registry and gate/replay governance tests.

### Advisory / Generated Artifacts

Primary classification: **Supporting**.

Secondary role: historical evidence fanout.

Why it exists: reports and generated artifacts capture trend, drift, recurrence, fallback incidence, provenance, and audit evidence.

Architectural questions answered: what evidence exists; is it current doctrine, generated evidence, advisory evidence, or historical trail.

Protected invariants: advisory/generated artifacts do not become policy unless explicitly promoted; stale reports should be interpreted through canonicality.

Dependencies: replay, evidence, diagnostics, governance.

Dependents: campaign reports, external review, future audits.

Expected lifetime: permanent category; individual artifacts age into historical context.

Implementation impact: artifacts can be regenerated, archived, or superseded; the category remains necessary.

Evidence: AR-AD canonicality index; AR-AF evidence model; AR-BA evidence artifact fanout transitional candidate.

## 4 Dependency Hierarchy

### Core Foundational Stack

```text
Canonicality
  -> Ownership
  -> Authority
  -> State Authority
  -> Runtime Transaction
```

Canonicality tells contributors which surfaces are authoritative. Ownership and authority make that classification operational. State authority applies it to mutation/read domains. Runtime transaction uses these rules to coordinate a turn.

### Runtime Production Stack

```text
Runtime Transaction
  -> Domain Simulation
  -> CTIR
  -> Prompt / Adaptation
  -> Realization
  -> Final Emission
  -> Persistence
```

Domain simulation depends on runtime ordering and state authority. CTIR depends on authoritative post-mutation state. Prompt/adaptation depends on CTIR and approved read models. Realization depends on prompt/adaptation and model/fallback routing. Final emission depends on candidate/prepared/fallback output. Persistence stores the finalized result.

### Defensive Boundary Stack

```text
Final Emission
  -> Validators
  -> Repair
  -> Sanitizers
  -> Fallback
  -> Provenance
```

Final emission orchestrates the boundary. Validators produce pass/fail evidence. Repair consumes known failures when bounded correction is allowed. Sanitizers clean/package unsafe presentation artifacts. Fallback may provide substitute behavior before or inside final emission. Provenance records behavior explanation after selection/application.

Important dependency answer: **Final Emission does not depend on Repair as a concept to exist**, but current implementation uses repair helpers. The final-emission concept would survive if some repair modes migrated upstream.

### Replay and Evidence Stack

```text
Finalized runtime surfaces
  -> Runtime Diagnostic Projection
  -> Protected Replay Projection
  -> Evidence
  -> Governance
```

Replay depends on finalized runtime surfaces and projection. Protected replay may depend on runtime diagnostics, but runtime must not depend on protected replay.

Important dependency answer: **Replay depends on Final Emission only indirectly through finalized output surfaces**. Replay observes final emission; it does not own or drive it.

### Provenance and Authority Stack

```text
Authority
  -> Realization Authority
  -> Fallback ownership axes
  -> Provenance
  -> Evidence / Replay
```

Provenance depends on authority because it records which owner/selector/applicator/family a behavior came from. It does not replace authority.

Important dependency answer: **Provenance depends on Authority**, because provenance has no meaning unless the architecture distinguishes who may decide, select, package, or observe.

### Validation Stack

```text
Prompt / Adaptation
  -> Response Policy Contracts
  -> Validators
  -> Final Emission
  -> Evidence
```

Validators depend on contracts and candidate text. They emit evidence but do not own repair or final output.

Important dependency answer: **Validators depend on Final Emission for orchestration but not for predicate meaning**. Final emission packages validator outcomes; validators own the deterministic predicates.

### Repair and Final Emission Stack

```text
Validators
  -> Repair
  -> Final Emission
  -> Provenance / Diagnostics
```

Repair is usually triggered by validation failure or known repair-eligible conditions. Final emission may call repair, but target doctrine says semantic synthesis belongs upstream unless sealed or legality-preserving.

Important dependency answer: **Final Emission should not conceptually depend on semantic Repair**, only on legality/packaging capability. Current semantic repair paths are transitional.

## 5 Permanent Architectural Vocabulary

Future contributors should be expected to understand these terms regardless of implementation evolution:

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
- Final Emission
- Validators
- Repair, with the distinction between permanent bounded repair and transitional boundary semantic repair
- Sanitizers
- Fallback, especially multi-axis fallback ownership
- Provenance
- Replay
- Projection
- Runtime Diagnostic Projection
- Protected Replay Projection
- Evidence
- Diagnostics
- Telemetry / Lineage
- Governance
- Persistence
- Compatibility Residue, as a category of non-owning support/historical surfaces

## 6 Transitional Vocabulary

### Final-Emission Semantic Repair Pressure

Why it exists today: the final boundary historically had to keep shipped text legal and usable under many failure modes, including incomplete model output and malformed fallback behavior.

Condition still requiring it: some current boundary paths still repair or reorder player-visible meaning, and tests intentionally preserve safety behavior.

Future event that would eliminate it: upstream owners consistently provide prepared compliant content, leaving final emission with legality, packaging, strip-only cleanup, and sealed terminal exceptions.

### Dual Fallback-Family Vocabulary

Why it exists today: runtime diegetic family fields and governed realization fallback-family fields answer related but different questions, while replay projects compatibility observations.

Condition still requiring it: consumers still need distinct write-time truth, provenance family, and read-side observation semantics.

Future event that would eliminate it: a documented consumer map and replay proof establish field precedence without losing multi-axis meaning.

### Legacy Diegetic Fallback Classification

Why it exists today: older fallback renderers and family names remain tolerated so old paths and observations are understandable.

Condition still requiring it: legacy renderers or protected observations still reference the vocabulary.

Future event that would eliminate it: old paths are retired or reclassified under explicit realization/fallback authority without evidence loss.

### CTIR-Absent Prompt Compatibility Reads

Why it exists today: prompt construction remains tolerant of older or exceptional flows where CTIR is absent.

Condition still requiring it: not every caller path is proven to attach CTIR before prompt construction.

Future event that would eliminate it: normal resolved-turn paths always attach CTIR and absence behavior is either unreachable or explicitly scoped to error handling.

### Opening Fallback Compatibility Fields

Why it exists today: opening crosses bootstrap, realization, fallback, final emission, persistence, and replay; protected replay observes source/owner fields.

Condition still requiring it: external/protected observations still depend on opening fallback owner/source/authorship fields.

Future event that would eliminate it: opening handoff doctrine and protected replay evidence support simpler read-side projection.

### Historical / Debug-Named Provenance Modules

Why it exists today: names such as `fallback_provenance_debug` persist even though the module owns stable provenance packaging.

Condition still requiring it: runtime imports and tests depend on the module name.

Future event that would eliminate it: a compatibility-safe rename/documentation placement is explicitly scoped. This report does not recommend doing that work.

### Generated / Advisory Evidence Artifact Fanout

Why it exists today: repeated audit and stabilization work produced many useful reports.

Condition still requiring it: those artifacts remain useful for history, trend context, and external review.

Future event that would eliminate it: canonicality labels and retention rules make older advisory reports clearly historical rather than active doctrine.

### Legacy Sanitizer Rewrite Mode

Why it exists today: old sanitizer behavior could rewrite or replace unsafe text rather than only strip/package/drop.

Condition still requiring it: compatibility tests and non-default paths may still exercise legacy rewrite semantics.

Future event that would eliminate it: strip-only/default boundary behavior fully covers live final-emission use, and legacy behavior is scoped or retired.

## 7 Historical Vocabulary

Historical vocabulary is retained for compatibility, evidence continuity, or audit trail value. It should not be interpreted as current architecture unless a current doctrine file, owner ledger row, or protected acceptance policy promotes it.

Historical or primarily compatibility-shaped terms:

- Legacy diegetic fallback family
- Historical/debug fallback provenance naming
- Older audit cycle labels and dated report names
- Dead-governance archive references
- Compatibility aliases in strict-social and prompt/contract seams
- Compatibility wrappers around telemetry or packet resolution
- Historical protected replay snapshots and generated reports not currently promoted
- CTIR-absent prompt fallback language when used as old-path tolerance rather than normal architecture

Compatibility Residue is itself a permanent classification category, but each residue instance is historical/supporting unless current doctrine says otherwise.

## 8 Documentation Priority Matrix

| Concept | Dedicated Doctrine | Glossary Entry | Ownership Documentation | Runtime Documentation | No Additional Documentation |
|---|---:|---:|---:|---:|---:|
| Runtime Transaction | Yes | Yes | Yes | Yes | No |
| Domain Simulation | Yes | Yes | Yes | Yes | No |
| State Authority | Existing, maintain | Yes | Existing, maintain | Existing, maintain | No |
| Ownership | Existing, maintain | Yes | Existing, maintain | No | No |
| Authority | Yes | Yes | Yes | No | No |
| Routing | No | Yes | Yes | Yes | No |
| CTIR | Existing, maintain | Yes | Existing, maintain | Yes | No |
| Prompt / Adaptation | Existing, maintain | Yes | Existing, maintain | Yes | No |
| Realization | Yes | Yes | Yes | Yes | No |
| Opening Realization | No | Yes | Yes | Yes | No |
| Final Emission | Existing, maintain | Yes | Existing, maintain | Yes | No |
| Replay | Existing, maintain | Yes | Existing, maintain | Yes | No |
| Projection | Yes | Yes | Yes | Yes | No |
| Provenance | Yes | Yes | Yes | Yes | No |
| Evidence | Yes | Yes | No | No | No |
| Validators | No | Yes | Existing, maintain | Yes | No |
| Repair | Yes | Yes | Existing, maintain | Yes | No |
| Sanitizers | No | Yes | Yes | Yes | No |
| Fallback | Yes | Yes | Existing, maintain | Yes | No |
| Diagnostics | No | Yes | No | Yes | No |
| Telemetry / Lineage | No | Yes | Existing, maintain | Yes | No |
| Governance | Existing, maintain | Yes | Existing, maintain | No | No |
| Canonicality | Yes | Yes | No | No | No |
| Compatibility Residue | Yes | Yes | Yes | No | No |
| Persistence | No | Yes | Existing, maintain | Yes | No |
| Response Policy Contracts | Existing, maintain | Yes | Existing, maintain | Yes | No |
| Strict-Social Emission | No | Yes | Existing, maintain | Yes | No |
| Advisory / Generated Artifacts | Yes | Yes | No | No | No |

Priority interpretation:

- Dedicated doctrine: concept deserves a stable contributor-facing document or a stable section in a doctrine document.
- Glossary entry: concept should be named consistently in a permanent architecture glossary.
- Ownership documentation: owner, direct-owner tests, downstream consumers, and compatibility residue should remain declared.
- Runtime documentation: implementation-facing documentation should explain how the concept appears in live execution.
- No additional documentation: none of the major concepts in this classification are low enough priority to leave undocumented.

## 9 Architectural Observations

### More Fundamental Than Expected

Canonicality proved more fundamental than AR-BA initially implied. It is not merely documentation hygiene; it is the concept that prevents evidence, diagnostics, protected acceptance, generated artifacts, and governance reports from becoming accidental authority.

Authority also proved more fundamental than ownership alone. Ownership says who owns a concern, while authority says what kind of decision they are allowed to make. The fallback/provenance/replay cluster cannot be understood without that distinction.

Projection proved more architectural than implementation-oriented. Runtime diagnostic projection and protected replay projection are separate because they answer different questions and protect one-way dependency.

Compatibility Residue proved to be a permanent category even though each instance is historical or transitional. The architecture needs a durable way to name non-owning support paths.

### Primarily Implementation-Oriented Concepts

Some terms are implementation-oriented even when their parent concept is architectural:

- Specific fallback-family field names are less permanent than fallback's multi-axis ownership model.
- Individual repair helper names are less permanent than bounded repair as a concept.
- Legacy sanitizer rewrite modes are less permanent than sanitizer strip/package/drop responsibility.
- Specific generated report files are less permanent than evidence/canonicality.
- Current routing field names are less permanent than routing as path-selection metadata.

### Classifications Changed Because Of AR-BB

AR-BB upgraded the defensive runtime cluster from "possibly overlapping cleanup area" to distinct concepts with stable responsibilities:

- Validators: Essential, not transitional.
- Sanitizers: Essential, with transitional legacy rewrite paths.
- Fallback: Essential, with transitional vocabulary/fanout.
- Final Emission: Foundational, not merely a gate implementation.
- Repair: Essential as bounded correction, with semantic boundary repair classified as transitional.

AR-BB also clarified that final emission's use of validators, repair, sanitizer integration, and fallback is hierarchical orchestration, not duplicate concept ownership.

### Rename Candidates For Future Documentation

These are vocabulary observations, not implementation cleanup recommendations:

- "Compatibility Residue" should remain the preferred umbrella term for tolerated non-owning support/historical paths.
- "Runtime Diagnostic Projection" and "Protected Replay Projection" should be named distinctly whenever replay is discussed.
- "Repair" should usually be qualified as "bounded repair" or "semantic boundary repair" when the distinction matters.
- "Fallback owner" should be avoided as a single field phrase in doctrine; use content author, selector, applicator, provenance packager, recorder, runtime diagnostic owner, and protected replay owner.
- "Evidence" should be labeled by canonicality class: runtime truth, runtime projection, protected acceptance, governance contract, generated artifact, advisory artifact, or historical reference.

## 10 Campaign Assessment

Campaign 3 is close to completion. AR-BA inventoried the concept set and identified ambiguous boundaries. AR-BB reconciled the highest-pressure defensive runtime cluster. AR-BC now classifies every major concept into long-term architectural status.

Another broad classification refinement cycle is not needed unless future reviewers challenge a specific concept's evidence. The classification is stable enough to support synthesis.

Recommended next block:

**AR-BD - Concept Map Synthesis and Doctrine Placement**

Recommended AR-BD purpose:

- Convert this classification into a compact concept map.
- Place permanent vocabulary into a contributor-facing architecture glossary/doctrine page.
- Cross-reference existing doctrine instead of creating another competing source of truth.
- Preserve transitional and historical registers as registers, not implementation mandates.

Campaign closeout can likely follow AR-BD if no new conceptual ambiguity appears during synthesis.

## Files Recommended for External Review

### Required

- `AR-BA_concept_inventory_and_responsibility_discovery.md` - concept inventory and initial ambiguity register.
- `AR-BB_defensive_runtime_boundary_reconciliation.md` - reconciliation of validators, repair, sanitizers, fallback, and final emission.
- `AR-AF_architecture_reconciliation_synthesis.md` - baseline architecture and invariants.
- `AR-AD_target_architecture_doctrine.md` - target doctrine, layer model, multi-axis ownership, canonicality index.
- `AR-AB_runtime_authority_and_replay_boundary_map.md` - runtime/replay boundary maps and fallback ownership axes.
- `docs/architecture_ownership_ledger.md` - repo-facing ownership declarations.
- `docs/final_emission_ownership_convergence.md` - final-emission legality/packaging versus semantic mutation classification.
- `docs/validation_layer_separation.md` - phase contract for truth, structure, expression, legality, and offline scoring.
- `docs/testing/protected_replay_manifest.md` - protected replay policy.
- `docs/testing/replay_governance_authority.md` - replay governance boundary.

### Strongly Recommended

- `game/state_authority.py` and `tests/test_state_authority.py` - concrete state authority implementation and direct-owner tests.
- `game/realization_authority.py`, `game/realization_provenance.py`, `game/fallback_provenance_debug.py` - realization/fallback/provenance authority evidence.
- `game/final_emission_gate.py`, `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/output_sanitizer.py` - defensive runtime cluster evidence.
- `game/final_emission_replay_projection.py` - runtime diagnostic projection owner.
- `game/upstream_response_repairs.py` - upstream-prepared emission evidence.
- `tests/test_final_emission_boundary_convergence.py` - final-boundary anti-regression evidence.
- `tests/test_replay_boundary_governance.py` - replay/projection dependency-direction evidence.
- `tests/test_output_sanitizer.py`, `tests/test_final_emission_validators.py`, `tests/test_final_emission_repairs.py` - direct-owner evidence for defensive helpers.

### Optional

- `AR-AA_architectural_mapping_discovery.md` - original broad discovery map.
- `AR-AC_architectural_ownership_reconciliation.md` - ownership/layer reconciliation rationale.
- `AR-AE_architecture_conformance_assessment.md` - conformance and refinement readiness context.
- `AR-AI_final_vision_compatibility_closeout.md` - Campaign 2 closeout guardrail.
- `docs/architecture_audit_readme.md` - guidance for interpreting audit evidence and residue.
- Generated reports under `artifacts/golden_replay/` and `docs/audits/` - useful historical/advisory evidence when interpreted through canonicality.

## Evidence Standards Applied

Doctrine evidence: AR-AD, AR-AF, ownership ledger, validation-layer separation, final-emission convergence, protected replay governance.

Implementation evidence: state authority, realization authority/provenance, fallback provenance, final-emission gate/validators/repairs, output sanitizer, final-emission replay projection, upstream response repairs.

Test evidence: state authority, final-emission boundary convergence, replay boundary governance, validator/repair/sanitizer direct-owner tests, ownership/test governance suites referenced by the ownership ledger.

Architectural inference: used only where doctrine and implementation show different ownership axes, especially fallback split ownership, provenance non-ownership, final-emission orchestration, and evidence/canonicality distinctions. Inference is not presented as proof of implementation cleanliness.
