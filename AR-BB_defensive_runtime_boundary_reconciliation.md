# AR-BB - Defensive Runtime Boundary Reconciliation

Campaign: Campaign 3 - Concept Reconciliation

Scope: Validators, Repair, Sanitizers, Fallback, Final Emission.

Method: repository documentation, runtime module headers and implementation surfaces, direct-owner tests, governance tests, and architectural inference. This report does not modify implementation, recommend refactoring, merge concepts, or classify removals.

## 1 Executive Summary

The strongest conceptual distinction is that each concept answers a different architectural question:

- Validators ask: "Does this candidate satisfy the relevant legality or contract predicate?"
- Repair asks: "Can a known failed condition be corrected under bounded deterministic rules?"
- Sanitizers ask: "Can unsafe presentation artifacts or internal contamination be removed or packaged without authoring ordinary meaning?"
- Fallback asks: "What bounded substitute behavior is selected when normal acceptable output cannot be produced?"
- Final Emission asks: "What final text, metadata, and FEM are allowed to reach the player and downstream observers?"

The strongest intentional overlap is at the final player-facing boundary. `game.final_emission_gate` owns orchestration and sealing; it calls validators, repairs, sanitizer integration, strict-social/fallback paths, and metadata packaging (`game/final_emission_gate.py:3`, `game/final_emission_gate.py:81`, `docs/architecture_ownership_ledger.md:120`). This is hierarchical orchestration, not proof that the helper concepts are duplicates.

The strongest transitional overlap is semantic repair at or near final emission. Doctrine says final emission should converge to legality enforcement and packaging only (`docs/final_emission_ownership_convergence.md:21`, `docs/final_emission_ownership_convergence.md:23`, `docs/final_emission_ownership_convergence.md:28`). The ledger still names several current final-emission repair paths as boundary semantic mutation with upstream migration targets (`docs/architecture_ownership_ledger.md:127`). Tests lock recent convergence behavior: answer/action fallback prose is consumed from `upstream_prepared_emission`, not minted by the gate, and fallback-behavior repair is strip-only rather than template synthesis (`tests/test_final_emission_boundary_convergence.py:151`, `tests/test_final_emission_boundary_convergence.py:180`, `tests/test_final_emission_boundary_convergence.py:208`, `tests/test_final_emission_boundary_convergence.py:103`).

The unresolved ambiguity is not whether the concepts are distinct. They are. The ambiguity is which remaining boundary mutations are permanent legality-preserving guardrails versus still-upstream-movable semantic repairs. This ambiguity is documented, fenced by tests, and narrow enough that Campaign 3 can begin concept classification after this reconciliation.

Recommendation: Concept Classification can begin. The next block should be `AR-BC_permanent_transitional_historical_concept_classification.md`.

## 2 Responsibility Profiles

### Validators

Purpose: Deterministic legality and contract predicates. Validators produce pass/fail verdicts, reason codes, and evidence; they do not repair, score, or own runtime truth. Documented doctrine identifies validators as gate-layer legality predicates (`docs/validation_layer_separation.md:42`, `docs/validation_layer_separation.md:44`) and AR-BA defines them as pass/fail predicates (`AR-BA_concept_inventory_and_responsibility_discovery.md:537`, `AR-BA_concept_inventory_and_responsibility_discovery.md:543`).

Inputs: Candidate text, response-policy contracts, narrative-mode/answer/action/dialogue/fallback contracts, referent artifacts, context fields, and sometimes GM output compatibility accessors (`game/final_emission_validators.py:83`, `game/final_emission_validators.py:231`, `game/final_emission_validators.py:777`, `game/final_emission_validators.py:1161`, `game/final_emission_validators.py:2101`).

Outputs: Boolean verdicts, failure reasons, diagnostic dictionaries, repair-eligible labels, and default debug fields (`game/final_emission_validators.py:465`, `game/final_emission_validators.py:499`).

Authority: Predicate authority only. Validators can say a candidate fails a contract; they do not select final output, perform retries, or package FEM. The ownership ledger states gate orchestration calls validators, while gate owns ordering and metadata (`docs/architecture_ownership_ledger.md:120`, `AR-BA_concept_inventory_and_responsibility_discovery.md:547`).

Ownership: Runtime owner is primarily `game.final_emission_validators`, with related specialized validators. Governance owner is validation-layer separation plus the ownership ledger (`docs/validation_layer_separation.md:1`, `docs/architecture_ownership_ledger.md:15`).

Lifecycle: After GPT or fallback candidate generation, during final-emission legality checks; also read by repair loops and retry diagnostics.

Protected invariants: Gate legality is deterministic, not evaluator scoring (`docs/validation_layer_separation.md:16`, `docs/validation_layer_separation.md:73`). GPT text is never authoritative for truth or legality (`docs/validation_layer_separation.md:37`, `docs/validation_layer_separation.md:72`). Validators do not author missing facts or fallback exposition (`game/final_emission_validators.py:91`).

Failure modes: Contract violations, fabricated certainty, meta fallback voice, route-illegal generic fallback, malformed answer/action/dialogue shapes, referent ambiguity, and validator results being misread as scores or repairs.

Dependencies: Response-policy contract readers, referent artifacts, route/fallback legality helpers, and context metadata.

Downstream consumers: Final-emission gate, repair functions, retry strategy detection, FEM/debug metadata, and direct-owner tests.

Current status: Permanent vocabulary candidate. Some validator-adjacent minimal repair helpers are historical/transitional residue in docs, but the validator concept itself is stable.

### Repair

Purpose: Bounded deterministic alteration after a known failure, preferably legality-preserving. AR-BA defines repair as alteration to satisfy a contract after validation detects failure (`AR-BA_concept_inventory_and_responsibility_discovery.md:569`, `AR-BA_concept_inventory_and_responsibility_discovery.md:575`).

Inputs: Candidate text, validation result, contract metadata, GM output, resolution/context, and upstream-prepared payloads.

Outputs: Repaired text or unchanged text, repair metadata, skip reasons, reason codes, and mutation/write-site attribution (`game/final_emission_repairs.py:796`, `game/final_emission_repairs.py:936`, `game/final_emission_repairs.py:937`, `game/upstream_response_repairs.py:299`).

Authority: Repair authority is narrower than final-emission authority. `game.final_emission_repairs` remains the runtime repair orchestration home, but several semantic mutations at final emission are explicitly transitional (`docs/architecture_ownership_ledger.md:125`, `docs/architecture_ownership_ledger.md:127`).

Ownership: Runtime owner for final-emission repair helpers is `game.final_emission_repairs`; upstream-prepared answer/action/opening fallback prose is owned by `game.upstream_response_repairs` and opening/social owners where applicable (`game/upstream_response_repairs.py:3`, `game/upstream_response_repairs.py:9`, `game/upstream_response_repairs.py:191`). Governance owner is the ownership ledger and final-emission convergence doc.

Lifecycle: Primarily gate layer after validation. Some migrated repair/prose construction now happens before final emission as upstream-prepared emission (`docs/final_emission_ownership_convergence.md:144`).

Protected invariants: Final emission should not invent answer/action fallback prose when upstream prepared text is absent or malformed (`tests/test_final_emission_boundary_convergence.py:208`, `tests/test_final_emission_boundary_convergence.py:301`, `tests/test_final_emission_boundary_convergence.py:325`). Fallback-behavior repair strips/removes/softens prohibited surfaces and records semantic synthesis skipped (`game/final_emission_repairs.py:986`, `game/final_emission_repairs.py:989`; `tests/test_final_emission_boundary_convergence.py:103`).

Failure modes: Silent semantic invention, sentence reordering for compliance theater, fabricated fallback certainty, meta fallback voice, repair becoming a second planner, and downstream suites re-owning repair derivation.

Dependencies: Validators, response-policy contracts, upstream-prepared payloads, social/strict-social seams, referent artifacts, and final-emission metadata.

Downstream consumers: Final-emission gate, metadata packaging, runtime projection, replay projection, and tests.

Current status: Mixed. Repair as a concept is permanent; semantic repair at final emission is transitional unless it is sealed, strict-social owned, or demonstrably legality-preserving.

### Sanitizers

Purpose: Last-mile cleanup of internal contamination, serialized payload leakage, unsafe prefixes, route-illegal stock text, and unrecoverable presentation artifacts. AR-BA defines sanitizers as cleanup that should not become semantic generation (`AR-BA_concept_inventory_and_responsibility_discovery.md:601`, `AR-BA_concept_inventory_and_responsibility_discovery.md:607`).

Inputs: Candidate text, sanitizer context, boundary mode, upstream-prepared empty fallback text, strict-social clamp fields, and optional sanitizer trace state.

Outputs: Cleaned text, dropped/recovered text, sanitizer debug events, sanitizer lineage trace, and optional empty/strict-social fallback evidence (`game/output_sanitizer.py:1371`, `game/output_sanitizer.py:1494`, `game/output_sanitizer_lineage.py:1`, `game/output_sanitizer_lineage.py:41`).

Authority: Sanitizer owns cleanup and trace construction for sanitizer actions. It does not own ordinary semantic repair or final selection. Strip-only is the default boundary mode; historical sentence rewrites require explicit `legacy_sentence_rewrite` mode (`game/output_sanitizer.py:6`, `game/output_sanitizer.py:197`, `game/output_sanitizer.py:1518`).

Ownership: Runtime owner is `game.output_sanitizer`; lineage owner is `game.output_sanitizer_lineage`; final emission orchestrates and records sanitizer outcomes. Strict-social fallback prose used by sanitizer is content-owned by social exchange emission when knowable (`tests/test_golden_replay_fallback_sanitizer_projection.py:123`, `tests/test_golden_replay_fallback_sanitizer_projection.py:156`).

Lifecycle: At or near final-emission boundary, including post-gate strict-social clamp handling and final cleanup.

Protected invariants: Strip-only mode drops scaffold without diegetic template substitution (`tests/test_output_sanitizer.py:45`, `tests/test_final_emission_boundary_convergence.py:130`). Serialized payload extraction recovers `player_facing_text` as packaging rather than rewriting meaning (`game/output_sanitizer.py:231`, `game/output_sanitizer.py:278`, `tests/test_final_emission_boundary_convergence.py:394`).

Failure modes: Internal JSON/debug/schema leakage, route-illegal text reaching player, empty output, sanitizer minting diegetic substitutes in the final boundary path, and sanitizer fallback ownership being mistaken for gate ownership.

Dependencies: Social exchange fallback catalog, sanitizer lineage helpers, final-emission context, and upstream-prepared empty fallback.

Downstream consumers: Final-emission finalize/meta, runtime lineage projection, protected replay sanitizer projection, and tests.

Current status: Permanent concept with transitional residue in legacy sentence rewrite mode. Its permanent boundary is strip/package/drop plus explicitly owned emergency fallback handling.

### Fallback

Purpose: Bounded substitute behavior when normal output cannot be produced, selected, or legalized. Fallback preserves continuity under failure while making the failure path observable (`AR-BA_concept_inventory_and_responsibility_discovery.md:505`, `AR-BA_concept_inventory_and_responsibility_discovery.md:511`).

Inputs: Upstream API errors, retry failures, malformed candidate text, opening/bootstrap missing text, strict-social terminal failure, sanitizer empty output, visibility/sealed conditions, contracts, and context.

Outputs: Fallback candidate/final text, tags, metadata, fallback family fields, selection/content owner fields, provenance traces, and replay-observable events.

Authority: Multi-axis by design. Content author, selector, applicator, provenance packager, recorder, and replay observer may differ (`AR-AB_runtime_authority_and_replay_boundary_map.md:174`, `AR-AB_runtime_authority_and_replay_boundary_map.md:176`). The architecture synthesis explicitly preserves retry/fallback ownership as multi-axis (`AR-AF_architecture_reconciliation_synthesis.md:147`).

Ownership: Content may be `game.gm_retry`, `game.diegetic_fallback_narration`, `game.opening_deterministic_fallback`, `game.upstream_response_repairs`, `game.social_exchange_emission`, `game.output_sanitizer`, or sealed final-emission modules depending on path (`AR-AB_runtime_authority_and_replay_boundary_map.md:178`, `AR-AB_runtime_authority_and_replay_boundary_map.md:183`). Selection may be API, gate, sanitizer, or strict-social path. Provenance packaging is separate, especially `game.fallback_provenance_debug` and `game.realization_provenance` (`game/fallback_provenance_debug.py:1`, `game/fallback_provenance_debug.py:5`, `game/realization_provenance.py:1`).

Lifecycle: GPT/retry path, upstream API error path, opening bootstrap, strict-social terminal path, sanitizer empty-output path, sealed final-emission path, and replay observation.

Protected invariants: Fallback content must be identifiable separately from selector/applicator; provenance must explain behavior without owning it (`AR-AB_runtime_authority_and_replay_boundary_map.md:185`, `AR-AB_runtime_authority_and_replay_boundary_map.md:187`, `AR-AF_architecture_reconciliation_synthesis.md:152`). Fallback families require provenance where governed (`game/realization_authority.py:275`, `game/realization_authority.py:315`, `game/realization_authority.py:329`).

Failure modes: No player response after upstream failure, hidden fallback authorship, fallback fields collapsing selection/content/provenance, fallback overwriting selected text, unsafe invented certainty, and replay treating fallback projection as runtime authority.

Dependencies: API retry loop, `gm_retry`, fallback content modules, final emission, sanitizer, provenance helpers, metadata packaging, and replay projection.

Downstream consumers: Final emission, FEM metadata, runtime diagnostic projection, protected replay projection, fallback incidence/reporting tools.

Current status: Permanent concept with transitional vocabulary/fanout. Dual `fallback_family_used` and `realization_fallback_family` fields are transitional read/compatibility pressure, not conceptual duplication (`AR-AB_runtime_authority_and_replay_boundary_map.md:202`, `game/diegetic_fallback_narration.py:7`, `game/realization_provenance.py:3`).

### Final Emission

Purpose: Last-mile legality, final selection, packaging, metadata/FEM, traceability, and sealed terminal exceptions for player-facing text (`AR-BA_concept_inventory_and_responsibility_discovery.md:345`, `AR-BA_concept_inventory_and_responsibility_discovery.md:347`).

Inputs: GPT/retry/fallback candidate text, upstream-prepared emission payloads, contracts, context, sanitizer outputs, repair metadata, provenance fields, and finalization context.

Outputs: Final player-facing text, finalized GM/FEM metadata, final-emission debug, lineage events, source/fallback/repair fields, and response/log/persistence surfaces.

Authority: Final emission owns final selection, legality, packaging, FEM, and sealed terminal exceptions (`AR-AF_architecture_reconciliation_synthesis.md:148`). It does not own engine truth, planner structure, GPT expression choices, evaluator scoring, or all fallback content authorship (`docs/validation_layer_separation.md:73`, `docs/final_emission_ownership_convergence.md:28`).

Ownership: Gate orchestration owner is `game.final_emission_gate`; metadata owner is `game.final_emission_meta`; repair helper owner is `game.final_emission_repairs`; sanitizer owner remains sanitizer; runtime projection owner is `game.final_emission_replay_projection` for read-side diagnostics (`docs/architecture_ownership_ledger.md:106`, `docs/architecture_ownership_ledger.md:138`, `AR-AB_runtime_authority_and_replay_boundary_map.md:61`).

Lifecycle: After GPT/retry/fallback candidate and before persistence, logging, response construction, and replay observation (`AR-AB_runtime_authority_and_replay_boundary_map.md:51`, `AR-AB_runtime_authority_and_replay_boundary_map.md:53`).

Protected invariants: Shipped text is legal, packaged, traceable, and consistent with upstream authorized meaning (`AR-BA_concept_inventory_and_responsibility_discovery.md:351`). Boundary should not silently invent meaning (`docs/final_emission_ownership_convergence.md:28`, `docs/final_emission_ownership_convergence.md:175`). Runtime diagnostic projection and protected replay remain read-side consumers, not runtime owners (`AR-AB_runtime_authority_and_replay_boundary_map.md:59`, `AR-AB_runtime_authority_and_replay_boundary_map.md:151`).

Failure modes: Illegal player text, schema/debug leakage, silent semantic repair, untraceable fallback selection, replay or diagnostics becoming behavior owners, persistence/log observing partial output.

Dependencies: API tail, gate modules, validators, repairs, sanitizer, provenance, metadata, finalizer, and projection.

Downstream consumers: Persistence, logs, response payload, runtime diagnostic projection, protected replay projection, tests, audits.

Current status: Permanent concept with transitional semantic-repair pressure.

## 3 Responsibility Transfer Map

Representative runtime path:

1. Runtime truth and CTIR are established before narration. API owns transaction order; engine/domain modules own authoritative simulation (`AR-AF_architecture_reconciliation_synthesis.md:139`, `AR-AF_architecture_reconciliation_synthesis.md:141`, `AR-AB_runtime_authority_and_replay_boundary_map.md:48`, `AR-AB_runtime_authority_and_replay_boundary_map.md:49`).
2. Planner/prompt construction adapts CTIR and contracts; GPT authors candidate expression only (`docs/validation_layer_separation.md:29`, `docs/validation_layer_separation.md:37`).
3. Retry/fallback handling begins when upstream/model/candidate conditions fail. API orchestrates retry/fallback and may select forced terminal fallback or upstream fast fallback before final emission (`AR-AB_runtime_authority_and_replay_boundary_map.md:52`, `game/api.py:2596`, `game/api.py:2807`, `game/api.py:2971`).
4. Provenance recording for upstream fast fallback occurs after selection, not during selection. `attach_upstream_fast_fallback_provenance` is called after terminal retry fallback selection and does not select prose (`game/fallback_provenance_debug.py:71`, `game/fallback_provenance_debug.py:74`, `game/api.py:2647`).
5. Final Emission assumes ownership when API tail delegates final player-facing handling through final-emission runtime/gate. The gate sequences validators, repairs, sanitizer integration, strict-social paths, logging, and metadata merges (`AR-AB_runtime_authority_and_replay_boundary_map.md:53`, `game/final_emission_gate.py:3`, `game/final_emission_gate.py:81`).
6. Validation begins wherever gate or related seams call predicate functions on candidate text and contracts. Validators return verdicts/evidence, not final text (`game/final_emission_validators.py:777`, `game/final_emission_validators.py:1161`, `game/final_emission_validators.py:1778`).
7. Repair begins only after a known failure or repair-eligible condition. Current final-emission repairs strip/remove/substitute and record skip/disabled metadata; migrated answer/action repair prose comes from `upstream_prepared_emission` (`game/final_emission_repairs.py:937`, `game/final_emission_repairs.py:986`, `game/upstream_response_repairs.py:299`).
8. Sanitization begins as final-boundary cleanup. Default `strip_only` mode extracts serialized payload text, strips/drop unsafe chunks, records lineage, and uses only bounded empty/strict-social fallback paths when output is otherwise empty (`game/output_sanitizer.py:1371`, `game/output_sanitizer.py:1457`, `game/output_sanitizer.py:1494`).
9. Final Emission seals final text and metadata. Persistence/log/response construction consume finalized surfaces, and replay/evidence observes them later (`AR-AB_runtime_authority_and_replay_boundary_map.md:54`, `AR-AB_runtime_authority_and_replay_boundary_map.md:56`, `AR-AB_runtime_authority_and_replay_boundary_map.md:57`).
10. Replay/projection happens after runtime. Runtime diagnostic projection reads finalized FEM; protected replay projection consumes runtime outputs but must not feed back into runtime (`AR-AB_runtime_authority_and_replay_boundary_map.md:61`, `AR-AB_runtime_authority_and_replay_boundary_map.md:151`, `tests/test_replay_boundary_governance.py:98`).

Authority changes hands from engine truth to planner structure to GPT expression to gate legality/orchestration to persistence/log/response to read-only replay/evidence. Fallback can appear before or inside final emission, but its ownership axes must remain split.

## 4 Pairwise Relationship Analysis

### Validators to Repair

Relationship type: Sequential and delegated. Validators produce failure evidence; repairs may consume it. Evidence: fallback behavior layer validates, attempts repair, then revalidates (`game/final_emission_repairs.py:1012`, `game/final_emission_repairs.py:1022`, `game/final_emission_repairs.py:1038`, `game/final_emission_repairs.py:1050`). Confidence: High.

### Validators to Sanitizers

Relationship type: Orthogonal with sequential adjacency. Validators assess legality/contract predicates; sanitizer strips/packages unsafe presentation artifacts. Evidence: validation layer names validators under gate legality, while sanitizer docstring makes strip-only cleanup default and legacy rewrites opt-in (`docs/validation_layer_separation.md:44`, `game/output_sanitizer.py:6`). Confidence: High.

### Validators to Final Emission

Relationship type: Hierarchical. Final emission orchestrates and packages validator results; validators do not own final selection. Evidence: ledger says gate owns final-emission layer ordering and calls into validators (`docs/architecture_ownership_ledger.md:120`); AR-BA says validators own pass/fail evidence while gate owns ordering/application (`AR-BA_concept_inventory_and_responsibility_discovery.md:547`). Confidence: High.

### Repair to Sanitizers

Relationship type: Orthogonal with transitional overlap. Repair corrects known failed conditions; sanitizer removes contamination. Overlap exists where legacy sanitizer rewrites and old repair templates both create substitute diegetic text. Evidence: convergence doc classifies sanitizer diegetic rewrites as semantic mutation and says they should move upstream, while default sanitizer is strip-only (`docs/final_emission_ownership_convergence.md:97`, `docs/final_emission_ownership_convergence.md:150`, `game/output_sanitizer.py:1518`). Confidence: High.

### Repair to Fallback

Relationship type: Intentional overlap plus transitional overlap. Repair may respond to fallback-behavior validation failures, but fallback content selection/authorship is a separate axis. `repair_fallback_behavior` now records semantic synthesis skipped and strips surfaces; older synthesis is explicitly move-upstream (`game/final_emission_repairs.py:936`, `game/final_emission_repairs.py:986`, `docs/architecture_ownership_ledger.md:127`). Confidence: High.

### Repair to Final Emission

Relationship type: Hierarchical and transitional. Final emission calls repair helpers under gate orchestration, but semantic repair at the boundary is transitional. Evidence: ledger names `game.final_emission_repairs` as runtime repair home and gate as orchestration owner, while convergence disallows boundary invention/reordering (`docs/architecture_ownership_ledger.md:111`, `docs/architecture_ownership_ledger.md:127`, `docs/final_emission_ownership_convergence.md:175`). Confidence: High.

### Fallback to Final Emission

Relationship type: Intentional overlap. Fallback may produce or select a candidate before final emission; final emission validates/selects/packages/records it. Sealed final-emission fallback is a permitted terminal exception. Evidence: fallback ownership map lists separate author/selector/applicator/recorder columns and identifies sealed final-emission fallback as the clearest intentional overlap (`AR-AB_runtime_authority_and_replay_boundary_map.md:176`, `AR-AB_runtime_authority_and_replay_boundary_map.md:183`). Confidence: High.

### Fallback to Provenance

Relationship type: Orthogonal and required. Fallback selection/content is behavior; provenance explains behavior. Evidence: `fallback_provenance_debug` explicitly does not select fallback prose or assign buckets (`game/fallback_provenance_debug.py:3`, `game/fallback_provenance_debug.py:5`), and realization provenance stamps governed family independently from diegetic family (`game/realization_provenance.py:3`). Confidence: High.

### Fallback to Replay

Relationship type: Read-side observation. Replay observes fallback fields and projected events; it does not select or own fallback behavior. Evidence: AR-AB forbids runtime dependency on protected replay projection and states protected replay does not own fallback content, selection, or provenance packaging (`AR-AB_runtime_authority_and_replay_boundary_map.md:96`, `AR-AB_runtime_authority_and_replay_boundary_map.md:151`, `AR-AB_runtime_authority_and_replay_boundary_map.md:172`). Confidence: High.

### Sanitizers to Final Emission

Relationship type: Hierarchical plus orthogonal. Sanitizer owns cleanup/lineage; final emission orchestrates and records final result. Sanitizer fallback projection keeps sanitizer stage/owner even when surfaced through final-emission telemetry (`game/final_emission_replay_projection.py:448`, `game/final_emission_replay_projection.py:677`, `game/final_emission_replay_projection.py:683`). Confidence: High.

## 5 Invariant Mapping

| Invariant | Protecting concepts | Evidence type and evidence |
|---|---|---|
| Runtime truth precedes narration | Final Emission indirectly, Validators/Repair/Sanitizers do not own truth | Doctrine: `AR-AF_architecture_reconciliation_synthesis.md:139`; runtime flow: `AR-AB_runtime_authority_and_replay_boundary_map.md:48` |
| GPT authors expression only | Validators, Final Emission | Doctrine: `docs/validation_layer_separation.md:37`, `docs/validation_layer_separation.md:72` |
| Gate legality is deterministic, not scoring | Validators, Final Emission | Doctrine: `docs/validation_layer_separation.md:16`, `docs/validation_layer_separation.md:73` |
| Final text must be legal, packaged, traceable | Final Emission, Validators, Sanitizers, Provenance | Doctrine/inference: `AR-BA_concept_inventory_and_responsibility_discovery.md:351`, `AR-AF_architecture_reconciliation_synthesis.md:148` |
| Boundary must not silently invent missing meaning | Repair, Final Emission, Sanitizers | Doctrine/tests: `docs/final_emission_ownership_convergence.md:28`, `tests/test_final_emission_boundary_convergence.py:208` |
| Strip-only sanitizer must not template-rewrite ordinary meaning | Sanitizers | Implementation/tests: `game/output_sanitizer.py:1371`, `tests/test_output_sanitizer.py:45` |
| Fallback ownership is multi-axis | Fallback, Final Emission, Provenance, Replay | Doctrine: `AR-AB_runtime_authority_and_replay_boundary_map.md:174`, `AR-AF_architecture_reconciliation_synthesis.md:147` |
| Provenance explains behavior without owning behavior | Fallback, Provenance, Replay | Doctrine/implementation: `AR-AF_architecture_reconciliation_synthesis.md:152`, `game/fallback_provenance_debug.py:5` |
| Runtime projection and protected replay remain separate | Final Emission, Replay, Fallback | Doctrine/tests: `AR-AB_runtime_authority_and_replay_boundary_map.md:151`, `tests/test_replay_boundary_governance.py:98` |
| Replay never drives runtime behavior | Replay, Final Emission | Doctrine/tests: `AR-AB_runtime_authority_and_replay_boundary_map.md:163`, `tests/test_replay_boundary_governance.py:41` |

## 6 Transitional Responsibility Register

| Transitional responsibility | Current owner | Future owner / target | Migration evidence | Confidence |
|---|---|---|---|---|
| Answer/action contract-shaped fallback prose at boundary | Previously final-emission gate/validators; now upstream prepared | `game.upstream_response_repairs`, planner/CTIR/API packaging | Convergence doc Block B and tests consuming `upstream_prepared_emission` (`docs/final_emission_ownership_convergence.md:144`, `tests/test_final_emission_boundary_convergence.py:151`) | High |
| Fallback-behavior template synthesis at final emission | `game.final_emission_repairs` residue | Prompt/retry/upstream fallback behavior shaping; final emission strip-only | Ledger and code mark move-upstream/semantic synthesis skipped (`docs/architecture_ownership_ledger.md:127`, `game/final_emission_repairs.py:936`, `game/final_emission_repairs.py:986`) | High |
| Sanitizer diegetic sentence rewrites | `game.output_sanitizer` legacy mode | Upstream guard/GM/planner or strict-social owner; final sanitizer strip-only | Convergence doc and explicit legacy mode (`docs/final_emission_ownership_convergence.md:150`, `game/output_sanitizer.py:197`) | High |
| Boundary semantic sentence reordering/compression | `game.final_emission_repairs` | Planner/retry/pre-final bounded repair | Convergence anti-goals disallow semantic reordering/compression at final boundary (`docs/final_emission_ownership_convergence.md:146`, `docs/final_emission_ownership_convergence.md:179`) | High |
| Narrative authority/anti-railroad/context replacement prose at gate | Gate policy layers | Planner constraints or bounded pre-final repair; final gate strip/fail | Convergence table targets prompt/planner/evaluator offline (`docs/final_emission_ownership_convergence.md:151`) | Medium |
| Scene-opening fallback composition ambiguity | Opening deterministic fallback plus upstream prepared plus gate selection | `game.opening_deterministic_fallback` composes; `game.upstream_response_repairs` packages; gate selects only | Implementation headers and AR-AB opening fallback row (`game/opening_deterministic_fallback.py:1`, `game/upstream_response_repairs.py:191`, `AR-AB_runtime_authority_and_replay_boundary_map.md:180`) | High |
| Dual fallback-family vocabulary | Diegetic fallback metadata plus realization provenance | Keep distinct until classification; document read precedence | AR-AB classifies as transitional; provenance docs keep fields independent (`AR-AB_runtime_authority_and_replay_boundary_map.md:202`, `game/realization_provenance.py:3`) | Medium |
| Legacy diegetic fallback renderers | `game.diegetic_fallback_narration` | Registered fallback families or retired/replaced seams | Realization authority labels legacy diegetic fallback temporary (`game/realization_authority.py:343`, `game/realization_authority.py:350`) | Medium |

## 7 Permanent Boundary Recommendations

Validators permanently own deterministic pass/fail predicates, reason codes, and evidence for declared contracts. They intentionally do not own repair, final selection, fallback content, provenance packaging, or evaluator scoring. They should never become a hidden quality-scoring or runtime-truth authority.

Repair permanently owns bounded deterministic correction for known failures where correction is legality-preserving, reason-coded, and test-backed. It intentionally does not own ordinary content generation, planner intent, fallback-family authorship, or final gate ordering. It should never become a silent semantic completion layer at the final boundary.

Sanitizers permanently own strip/package/drop cleanup of internal, schema, debug, route-illegal, and presentation contamination, plus sanitizer lineage. They intentionally do not own general narrative repair or ordinary diegetic rewriting. They should never become the default source of replacement scene prose outside explicit emergency fallback seams.

Fallback permanently owns the architectural pattern of bounded substitute behavior under failure, but not as a single module owner. It intentionally spans content author, selector, applicator, provenance packager, recorder, and observer axes. It should never collapse those axes into one ambiguous "fallback owner" field.

Final Emission permanently owns final selection, legality orchestration, packaging, FEM/meta, final traceability, and sealed terminal exceptions. It intentionally does not own engine truth, planner structure, GPT expression choices, evaluator scoring, or all fallback content authorship. It should never become a general upstream semantic repair engine.

## 8 Remaining Ambiguities

- Which specific remaining final-emission policy layers are permanent legality-preserving guardrails versus upstream-movable semantic repair? Repository doctrine identifies the category, but a symbol-by-symbol post-Block-D2 retirement table is not complete in this report.
- Which fallback-family fields are permanent runtime schema versus compatibility projection fields? AR-AB identifies dual vocabulary as transitional, but classification is deferred.
- Which validator outputs are gating, advisory, or diagnostic-only across all validator modules? AR-BA notes the need for one durable table (`AR-BA_concept_inventory_and_responsibility_discovery.md:567`).
- Whether sanitizer empty fallback should remain sanitizer-owned when the fallback text source is upstream prepared. Current evidence says sanitizer owns selection/lineage and upstream owns prepared text source, but vocabulary could be made clearer in classification.

These are unresolved questions for classification or focused inventory, not blockers to understanding the conceptual boundaries.

## 9 Campaign Impact

This reconciliation changes Campaign 3 by turning the high-density cluster from "possibly overlapping concepts" into a set of bounded responsibilities with known overlap types:

- Intentional hierarchical overlap: Final Emission orchestrates validators, repairs, sanitizer integration, fallback selection/recording, and meta packaging.
- Intentional orthogonal overlap: Fallback and provenance; fallback and replay; sanitizer and final-emission recording.
- Transitional overlap: final-boundary semantic repair, sanitizer legacy rewriting, dual fallback-family vocabulary, and legacy diegetic fallback classification.

Concept Classification can begin. Another broad reconciliation cycle is not required before classification. Additional repository evidence is useful only for symbol-level classification of remaining final-emission semantic repair paths and fallback-field permanence.

Recommended next block: `AR-BC_permanent_transitional_historical_concept_classification.md`.

## Files Recommended for External Review

### Required

- `AR-BA_concept_inventory_and_responsibility_discovery.md` - Prior concept inventory and explicit cluster handoff.
- `AR-AF_architecture_reconciliation_synthesis.md` - Architectural invariants, especially retry/fallback multi-axis ownership, final-emission authority, replay separation, and provenance non-ownership.
- `AR-AB_runtime_authority_and_replay_boundary_map.md` - Runtime flow, replay boundary, and fallback ownership map.
- `docs/architecture_ownership_ledger.md` - Canonical seam ownership declarations for gate orchestration, repairs, metadata, and validation-layer separation.
- `docs/final_emission_ownership_convergence.md` - Normative target for final-emission legality/packaging versus semantic mutation.
- `docs/validation_layer_separation.md` - Phase contract for engine, planner, GPT, gate, evaluator.
- `game/final_emission_gate.py` - Runtime orchestration entrypoint.
- `game/final_emission_validators.py` - Primary validator implementation.
- `game/final_emission_repairs.py` - Primary repair implementation and transitional flags.
- `game/output_sanitizer.py` and `game/output_sanitizer_lineage.py` - Sanitizer behavior and lineage owner.
- `game/realization_authority.py`, `game/realization_provenance.py`, `game/fallback_provenance_debug.py` - Fallback-family/provenance authority boundaries.

### Strongly Recommended

- `game/upstream_response_repairs.py` - Evidence for migrated upstream prepared emission responsibilities.
- `game/gm_retry.py` - Retry/terminal fallback selection and producer metadata.
- `game/opening_deterministic_fallback.py` - Opening fallback content ownership.
- `game/diegetic_fallback_narration.py` - Diegetic fallback-family vocabulary.
- `game/final_emission_replay_projection.py` - Runtime diagnostic projection and fallback split-owner projection.
- `tests/test_final_emission_boundary_convergence.py` - Regression locks for no boundary synthesis, upstream prepared repair, strip-only sanitizer, and social-owned fallback.
- `tests/test_output_sanitizer.py` - Sanitizer strip-only behavior and lineage assertions.
- `tests/test_golden_replay_fallback_sanitizer_projection.py` - Sanitizer fallback split-owner projection.
- `tests/test_replay_boundary_governance.py` - Runtime versus protected replay boundary locks.
- `tests/test_fallback_behavior_validator.py`, `tests/test_fallback_behavior_repairs.py`, `tests/test_fallback_behavior_gate.py` - Validator/repair/gate separation around fallback behavior.

### Optional

- `docs/testing/protected_replay_manifest.md` and `docs/testing/replay_governance_authority.md` - Governance context for protected replay observations.
- `tools/final_emission_ownership_audit.py` and `tools/validation_layer_audit.py` - Advisory drift scans, useful for future classification but not doctrine by themselves.
- Fallback incidence/replay reports under `docs/audits/` and `artifacts/` - Useful supporting evidence for runtime frequency and maintenance pressure, but not primary ownership evidence.

## Evidence Standards Applied

- Documented doctrine is cited from AR reports, ownership ledger, convergence docs, and validation-layer doctrine.
- Implementation evidence is cited from runtime module docstrings, functions, and metadata/provenance code.
- Test evidence is cited from direct-owner and governance tests.
- Architectural inference is limited to responsibility synthesis where code and doctrine show different axes, especially fallback split ownership and final-emission orchestration.

No inference in this report is presented as implementation cleanliness. Where docs say code still carries transitional behavior, this report preserves that distinction.
