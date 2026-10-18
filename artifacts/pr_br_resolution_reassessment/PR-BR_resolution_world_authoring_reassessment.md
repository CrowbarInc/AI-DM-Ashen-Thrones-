# PR-BR Resolution and World-Authoring Architecture Reassessment

Discovery-only cycle. No production code changes, prompt changes, gameplay/model calls, gate reruns, commits, or pushes were performed. Evidence comes from the already-produced second full 4x10 gate under `artifacts/pr_br_second_full_gate/20261003T142725Z`, existing code, existing tests, and current review artifacts.

## 1. Executive Conclusion

The second full 4x10 gate collapsed because Ashen Thrones now has a substantially better owner for player-intent interpretation, but not a coherent owner for the separate GM decision: given established state, mechanics, uncertainty, NPC knowledge, permissible improvisation, and persistence rules, what actually happens now and what new facts may exist?

Manual verification is 8/40 PASS and 32/40 FAIL. Contract quality is FULLY CORRECT 6, PARTIAL BUT SUFFICIENT 11, INCORRECT 23. Incorrect contracts are associated with 20 visible failures, but some incorrect contracts still passed and some fully correct contracts still failed. The dominant product failure is unsupported consequential invention: 19 primary failures, plus derivative addressee/discourse/location failures fed by invented premises.

The Resolution Contract should continue to answer what the player wants resolved. Current downstream architecture implicitly asks it, resolvers, or free-form generation to also decide what is true, what can be invented, what is observation versus inference/testimony, what persists, and whether an NPC knows something. That responsibility is not correctly owned.

Recommended decision: A. CURRENT ARCHITECTURE IS SALVAGEABLE WITH A BOUNDED RESOLUTION-PLANNING LAYER.

## 2. Full 40-Turn Population Table

Canonical table: `artifacts/pr_br_resolution_reassessment/turn_population.md`.

Machine-readable table: `artifacts/pr_br_resolution_reassessment/turn_population.json`.

All 40 turns are represented with player input, manual grade, contract quality, operation/topic/resolution subject, addressee/referent fields, resolver, generation path, authority classifications, retry/fallback behavior, mutation/persistence summaries, visible response, causal family, severity, and evidence note. Unknown fields are marked UNKNOWN in the JSON where normalized telemetry did not expose the read set.

## 3. Manual PASS/FAIL Verification

- Manual PASS: 8/40 = 20%.
- Manual FAIL: 32/40 = 80%.
- Persona pass counts: persona_a 2, persona_b 2, persona_c 1, persona_d 3.
- Evaluator PASS was 25/40 with 20 false positives and 3 false negatives, so evaluator signal is not trustworthy for product gate decisions.
- Accepted/emitted equality held. Post-seal mutation was not the collapse mechanism.

## 4. Failure-Family Distribution

- CONSEQUENTIAL_AUTHORITY: 19.
- RESOLUTION_EXECUTION: 5.
- ADDRESSEE_BINDING: 3.
- DISCOURSE_CONTINUITY: 2.
- CONTRACT_CONSTRUCTION: 1.
- MOVEMENT / LOCATION: 1.
- REFERENT_BINDING: 1.
- PASS: 8.

The primary cluster is unsupported consequential authority. Fallback/nonresolution, addressee loss, and location continuity are important, but they are not the largest root cause.

## 5. Severity Distribution

- HIGH: 23.
- MEDIUM: 9.
- PASS: 8.

High severity concentrates around consequential world invention and recursive premise use.

## 6. Root-Cause vs Contributing-Cause Analysis

Root-causal mechanisms:

- Unsupported consequential invention: generated prose created patrol dates, route changes, official orders, command relationships, physical evidence, historical notices, report procedures, deadlines, and Captain Thoran without authored support.
- Outcome/prose conflation: generation decided both what happened and how to narrate it.
- Provenance weakness: NPC claims, incidental details, observations, inferences, and world truth are tracked in fragments, but later reasoning can still treat generated premises as grounded context.
- Contract overburdening: downstream code implicitly expects the contract to carry outcome authority, uncertainty, NPC knowledge, and persistence decisions, although its stated role is intent.

Contributing mechanisms:

- Incorrect contracts changed resolver/addressee/subject selection in 20 visible failures.
- Generic fallback avoided hallucination in some cases but failed the human-GM standard by refusing ordinary resolution.
- Addressee/referent failures worsened when invented entities or claims polluted discourse.

## 7. Contract-Quality Analysis and Correlation

Verified contract population: FULLY CORRECT 6, PARTIAL BUT SUFFICIENT 11, INCORRECT 23. This verifies the reported approximately 23/40 incorrect contracts. Incorrect contracts associated with visible failure: 20.

Contract accuracy is not sufficient as the main product standard:

- Incorrect but playable: A05, D03, D09.
- Fully correct but failed: A10, B06, C03, D05.
- Partial but sufficient but failed: A02, A03, A08, A09, B09, C04, D02, D08.

Conclusion: interpretation remains unstable, but contract failures are often symptoms or contributors. The collapse is not reducible to contract construction.

## 8. Contract Failure Taxonomy

Observed contract defects:

- Compound inspection target loss: A01, C02, D10.
- Addressee loss or wrong addressee: B02, B04, B10, D04, D07.
- Action/social operation confusion: A07, C05, C07, D06.
- Topic over structure: B07/B08 consumed player-authored or previously invented context as route authority.
- Unresolved/generation fallback despite resolvable request: A05.

Shared mechanism: structural subject, addressee, and topic fields are still brittle under compound follow-ups and polluted discourse. However, many failures happened after a correct or sufficient contract, so the architecture should not make the contract own fictional outcome.

## 9. Consequential-Authority Failure Analysis

The gate's unsupported facts changed investigation topology:

- A02/A04/D05 invented notice chronology, official seal/handwriting, rosters, orders, annotations, and older notices.
- A03/D02 invented route changes tied to the Ash Compact census choke.
- B06-B10 invented Captain Thoran, search command authority, hiring authority, official assignments, reporting, and payment procedure.
- C05-C10 invented patrol bootprints, broken twigs, a route into woods, a fork, a stone marker, a watchtower, split-patrol evidence, and a repeated fork after movement should have advanced.
- D06 invented a driver's route report, old milestone conditions, and negative eyewitness evidence.

PR-BN/C19 catches some explicit operational rules and identities, but many failures arrived as ordinary narrative observation, NPC testimony, or local color. Post-generation classification is too late for those.

## 10. Unsupported-Fact Inventory

Material unsupported propositions by turn:

- A02: posting date, official seal, handwriting match, notice chronology.
- A03: departure timing, route alteration after census choke, no signals, captain update path.
- A04: roster board, departure time, assigned route, later annotations/orders.
- A08: access restrictions and a patrol member bringing news.
- A09: trouble report and returns through other gates.
- B01: patrol last seen near muddy footprints northwest of crates.
- B06: Captain Thoran commands the gate watch/search.
- B07: Captain Thoran as actionable captain with special patrol requirements.
- B08: official assignment, scouting order, reporting channel, deferred payment.
- B09: return timeline and reserved captain details.
- B10: serjeant treats Thoran as valid target while misanswering captain-directed question.
- C03: unsupported patrol orders attached to watcher response.
- C04: physical patrol orders, report point, dusk-yesterday deadline.
- C05: patrol bootprints, hurried movement, broken twigs, route into woods.
- C07: fork, split patrol, stone marker, watchtower route evidence.
- C08: print-depth evidence for hurry/split.
- C09: continued thinning/split-print evidence.
- C10: twin boot trails/fork/watchtower reintroduced after the character had moved on.
- D02: changed route, roster-favor procedure, census rationale.
- D05: historical notices, route changes, census causation.
- D06: driver route report and old-milestone negative evidence.

## 11. Consequential-Fact Provenance Chains

Patrol route/census chain:

`authored missing-patrol warning and northwest track clue -> A03/D02 generated route change after census choke -> persisted as authoritative fact -> D05 historical-notice inspection consumes that theme -> route change becomes explainable official history`.

Patrol evidence chain:

`authored northwest muddy track clue -> B01 says patrol vanished near footprints northwest of crates -> C05 converts premise into patrol bootprints, broken twigs, and route -> C07 adds fork/marker/watchtower/split evidence -> C08-C10 reason over invented physical geography`.

Captain Thoran chain:

`no named captain in authored state -> B06 invents Captain Thoran commanding the watch -> B07 treats him as present/actionable -> B08 serjeant accepts "Captain Thoran sent me" and invents assignment/orders -> B09/B10 keep treating Thoran as authority`.

Official procedure/order chain:

`missing patrol notice -> C04 patrol orders/report point/deadline -> B08 official assignment/payment/reporting -> D02 official channels for roster favors`.

Historical notice chain:

`notice board with missing-patrol/tax/curfew notices -> A02 chronology/seal/handwriting -> D05 older covered notices and historical route changes`.

## 12. Self-Reinforcing Invention Chains

The 10-turn sequences expose the pattern hidden by targeted tests:

`model invents fact -> fact enters prose/session/discourse/ledger -> later resolution reads it -> fact appears grounded -> model extends it -> extension persists -> fiction drifts`.

Current provenance metadata is not strong enough to stop an invented premise from recursively legitimizing itself. In particular, NPC claims can stay tagged as claims in one structure while still functioning as practical route/evidence truth in later context.

## 13. Current Authority-Responsibility Map

- May invent a fact: split between model generation, live-resolution proposal synthesis, bounded-improvisation validation, and proposition authority checks.
- Incidental vs consequential: `bounded_improvisation.py` and `proposition_authority.py`, mostly after text exists.
- Incidental persistence: bounded-improvisation ledger.
- Consequential persistence: nominally blocked, but consequential facts survive as prose, discourse, NPC claims, or pseudo-grounded context.
- Observation vs inference: no single authoritative owner.
- NPC testimony vs world truth: partially represented in bounded improvisation, not consistently honored downstream.
- Action success/check/roll: deterministic in mechanics, weak in ordinary exploration/social/world-action.
- Scene object/NPC/clue/route/procedure/order/history creation: no clear pre-narration owner.
- Generated fact commit: spread across discourse focus, bounded ledger, session traces, and visible response.

Responsibilities owned too late: authority classification, truth promotion, route/procedure/history creation, NPC knowledge, and many ordinary outcomes.

## 14. Resolver-Responsibility Map

Relevant resolvers:

- Exploration: accepts contract/scene context; under-resolves concrete inspections (A01, C02, D10) and over-authors physical evidence/history (A02, A04, C08, D05).
- Social: accepts addressee/topic/contract; frequently decides NPC knowledge, command authority, official procedure, and truth status inside prose.
- Travel/world_action: can leave movement as prose without authoritative location mutation (C05-C10).
- Generation/unresolved: high-risk fallback; A08 and D06 invent consequential facts, while A05 passes only accidentally.
- Contract-adjudication bridge: good contract-first deterministic lane, but not the owner for most gate failures.

## 15. Generation-Responsibility Map

Generation currently performs interpretation, fictional resolution, world authoring, epistemic resolution, and narration in overlapping ways. The gate supports the hypothesis that generation decides both fictional outcome and prose realization in ordinary paths. Existing validation cannot reliably reconstruct authority after free-form outcome generation.

## 16. PR-BN/C19 Responsibility Map

PR-BN/C19-style validation helps block explicit consequential rules/identities, preserve accepted/emitted integrity, and store bounded incidental/NPC-claim metadata. It does not reliably decide before narration whether an observation exists, whether an NPC knows an answer, whether a physical clue is allowed, whether an official procedure exists, or whether a generated premise may affect future turns.

## 17. Persistence/Commit/Provenance Map

Persistence channels observed:

- `authoritative_facts_created` telemetry, e.g. census route change and Captain Thoran.
- NPC claims with epistemic framing, sometimes too weakly honored.
- Discourse focus commits from contract/emitted text.
- Bounded improvisation ledger with `truth_status`.
- Location/session state, which remained `frontier_gate` while C persona narration moved outside it.

Provenance gap: later reasoning needs mandatory distinctions among authored world, bounded incidental, NPC claim, rumor, observation, inference, speculation, player assertion, and generated proposal.

## 18. C26/Post-Contract Semantic-Regression Analysis

Confirmed raw-semantic influence turns: A05, D03, D09.

- A05: contract unresolved, but generation resolved the physical search from raw text; product passed, invariant failed.
- D03: contract bound Tavern Runner, visible response answered watcher; product passed, invariant failed.
- D09: contract targeted Notice Board, visible response followed raw townhouse knock; product passed, invariant failed.

Conclusion: C26 did not establish a global invariant. It closed selected resolver-selection paths but left generation/unresolved and product-success fallback paths where raw semantics can still control resolution after the contract.

## 19. Addressee/Referent Analysis

Primary failures: B02, B04, B10, D04, D07. Related discourse fallout: A10, D08.

Follow-up phrasing such as "then," "his wagon," "the driver who just answered me," and "Captain Thoran" is fragile when prior discourse contains invented entities. Addressee/referent binding should become provenance-aware: a referent invented without authority should not be treated like an authored or grounded NPC.

## 20. Fallback/Overconstraint Analysis

Failure type A, over-invention: A02-A04, A08-A09, B01, B06-B10, C03-C05, C07-C10, D02, D05-D06.

Failure type B, overconstraint/nonresolution: A01, A07, A10, B02, C02, C06, D08, D10.

The architecture must permit harmless sensory/local connective detail and fallible NPC claims while blocking or qualifying consequential facts about clues, official orders, routes, command, history, evidence, and procedures unless established by state, mechanics, or an explicit authorized proposal.

## 21. State/Location Continuity Analysis

C05-C10 is the location-continuity failure. The character narratively leaves the gate, follows tracks, reaches a fork/marker/watchtower route, takes the northwest fork, slows before a bend, and then C10 resets visible geography to the already-passed fork. Telemetry location remains `frontier_gate`.

Root cause: unsupported generated geography plus prose-only movement without authoritative scene/location mutation. This is part of missing resolution ownership because "where is the PC now?" was decided by narration rather than state.

## 22. Human-GM Decision Comparison

A competent human GM would decide before speaking:

- player intent;
- established state and relevant mechanics;
- whether the response is observation, inference, testimony, action outcome, or new fact;
- whether the PC/NPC can perceive or know it;
- whether uncertainty or a check applies;
- whether bounded incidental detail is allowed;
- what provenance and state changes persist;
- then narration.

Current sequence often does contract intent -> resolver/generation prose -> validators/classifiers -> discourse/persistence. The missing middle is the GM decision.

## 23. GM Resolution Plan Hypothesis Evaluation

Candidate responsibilities:

- Contract reference: exists; reuse it.
- Resolution method: partially exists; not authoritative enough.
- Established facts consulted: traces exist; not required as plan input/output.
- Proposed new facts: exist as bounded proposals or extracted propositions after prose; too late.
- Authority/provenance: fragmented.
- Observation/inference/testimony: not coherently owned.
- Uncertainty/checks: deterministic in mechanics, weak in ordinary paths.
- Resolved outcome: often generated prose.
- Allowed mutations/persistence: fragmented and late.

A minimal plan is justified if it owns consulted facts, outcome type, proposed new facts with authority class, epistemic mode, permitted mutations, persistence policy, and narration constraints. It should not duplicate contract intent.

## 24. Architectural Option Comparison

Option A: Continue current architecture with stronger PR-BN/C19 authority enforcement.

Addresses explicit consequential rules/identities and some post-generation facts. Does not address generated physical evidence, official procedure, NPC knowledge, recursive premise promotion, or prose-only movement. Low initial scope, high whack-a-mole risk.

Option B: Add typed GM resolution/world-authoring plan.

Addresses the root boundary by deciding outcome and permissible authoring before narration. Preserves C18-C27 around a clearer decision object. Moderate scope. Risk: schema bloat if it duplicates the contract or tries to model the whole world.

Option C: Move more outcome determination into deterministic/simulation resolvers.

Reduces hallucinated consequential truth for mechanics, movement, perception, and authored-state queries. Risk: overconstraint unless paired with bounded invention and NPC testimony.

Option D: Hybrid/reconciled boundary.

Best supported concrete shape: contract remains intent owner; deterministic resolver/plan owner decides outcome/provenance; model may propose typed candidate facts only under validation; narration expresses decided outcome. This is bounded B plus selected C, not a rewrite.

## 25. C18-C27 Salvageability Matrix

- C18 immutable valid-response boundary: PRESERVE. Accepted/emitted equality held.
- C19 authority hardening: MODIFY. Keep it, but move authority decision earlier.
- C20 bounded incidental entity binding: MODIFY. Useful for harmless detail; must not authorize consequential evidence.
- C21 referential nominality/head resolution: MODIFY. Add provenance-aware referent validity.
- C22 primary/supporting intent/addressee integrity: MODIFY. Test polluted discourse and invented entities.
- C23 semantic ownership discovery: PRESERVE/MODIFY. Concern confirmed; broaden invariant.
- C24 unparsed/adjudication bypass closure: PRESERVE. Contract-first adjudication is sound.
- C25 Resolution Contract semantic ownership: PRESERVE. Contract remains intent owner.
- C26 contract-driven resolver selection/structured-output boundary: MODIFY. Not global.
- C27 structural subject/topic distinction: PRESERVE/MODIFY. Helps interpretation, not outcome authority.

## 26. Why Targeted Testing Misled Us

Targeted C27 tests were too shallow, too contract-centric, and too short. They did not stress 10-turn state accumulation, recursive invention, provenance durability, NPC knowledge/world-truth separation, or product-level authority assertions. Synthetic padding tests did not simulate a player pursuing generated details for ten turns.

Cheaper inner loop: no-model artifact replay auditors for consequential proposition creation, provenance chains, NPC claim promotion, location mutation vs narration, and plan-consistency.

## 27. Recommended Architecture

Adopt a bounded resolution-planning layer:

`PLAYER INPUT -> RESOLUTION CONTRACT -> GM RESOLUTION DECISION/PLAN -> specialized mechanics/resolvers or validated model proposals -> narration -> validation/commit`

Minimal fields:

- `contract_id`;
- `resolution_method`;
- `established_facts_consulted`;
- typed `outcome`;
- `proposed_new_facts` with authority/consequence/provenance;
- `allowed_mutations`;
- persistence policy;
- narration constraints.

## 28. Smallest Coherent Next Implementation Slice

Repair a typed pre-narration authority/outcome decision for ordinary exploration/social/world-action turns that currently rely on generated prose.

Targets: consequential-authority failures, recursive invention, prose-only movement/location drift, and NPC claim/world-truth confusion.

Explicitly not first slice: full addressee rewrite, full schema migration, human playtest, broad simulation redesign, PR-BS.

Minimum changes: add a small plan object and deterministic validator for new consequential propositions; thread it through generation prompt/output metadata; require narration to realize only the plan; block persistence of unplanned consequential facts.

Deterministic tests: B06 Captain Thoran, C05-C10 patrol track chain, A02/A04 notice/roster facts, D05 historical notices, D06 driver old-milestone report.

Stopping criteria: unsupported consequential facts are blocked or downgraded before narration; harmless inspections still produce playable bounded observation or explicit uncertainty; no full-gate rerun until static auditors pass.

## 29. Testing-Strategy Implications

Add cheap inner-loop tests:

- 40-turn artifact replay auditor.
- Proposition provenance chain detector.
- Consequential proposition plan-consistency checker.
- NPC claim truth-promotion regression tests.
- Multi-turn invented-premise pursuit fixtures.
- Location mutation vs narration consistency checks.
- Contract-quality/product-quality correlation dashboard.

## 30. Risks and Evidence Gaps

Evidence gaps:

- Normalized telemetry does not fully enumerate every state read.
- Some unsupported proposition origins are inferred from emitted text/telemetry rather than complete prompt internals.
- No tests or model calls were rerun by instruction.

Risks:

- Plan layer could become another schema requiring synchronization if it duplicates contract interpretation.
- Too strict an authority gate could revive generic nonresolution.
- Too much deterministic simulation too soon could balloon scope.
- If provenance is not represented in prompts and persistence, recursive invention will continue.

## 31. API/Model-Token Cost Implications

The recommended direction should reduce release-gate spend by moving checks into static deterministic auditors. Runtime model cost need not increase if deterministic resolvers create most plans. If model-proposed plans are later introduced, use them selectively for ambiguous/social epistemic cases with small structured outputs. Full 4x10 gates should remain release-candidate tests, not inner-loop debugging.

## 32. PR-BR Viability

PR-BR remains viable/converging if it stops treating C18-C27 as a linear bug chain and repairs the missing responsibility boundary. Existing work is valuable. The next authorized slice must move fictional outcome/world-authoring decisions upstream of narration.

## Required Decision

A. CURRENT ARCHITECTURE IS SALVAGEABLE WITH A BOUNDED RESOLUTION-PLANNING LAYER
