# PR-BR — Second Full 4×10 Synthetic Playability Gate

## 1. Purpose

Product-level validation of whether the post-C23–C27 Ashen Thrones AI-GM can sustain 40 fresh, coherent, simulationist turns across four natural player styles. This was one gate, not a repair loop, targeted regression, benchmark-tuning run, C28, or human playtest.

## 2. Authorization basis

The first full gate scored 32/40 and exposed recurring inspection collapse, speaker corruption, malformed incidental binding, consequential identity invention, semantic contract errors, and response replacement. C23–C27 then established contract-first semantic ownership, post-contract closure, structural resolution-subject precedence, and lossless operative context. The authorized next step was fresh sustained play.

## 3. API-cost accounting

- Opening GM calls: 4
- Gameplay initial-generation calls: 40
- Gameplay retry-generation calls: 11
- Structured interpretation calls: 18
- Synthetic-player action generations: 40
- Evaluator-model calls: 0
- Logical model-call total: 113
- Manual/operator reruns: 0

The harness's deterministic `evaluate_playability` ran once per turn and made no model call. Token and monetary totals were not exposed by the runtime, so no unverifiable estimate is reported.

## 4. Environment/provenance

- Gate stamp: `20261003T142725Z`
- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: `PR-BN bounded DM improvisational authority`
- Model on all product routes: `gpt-4.1-mini`
- Model routing: enabled
- Product paths: `POST /api/start_campaign`, then `POST /api/chat`
- Freeze evidence: `freeze.json`
- Working tree was already dirty with the uncommitted PR-BR stack and unrelated artifacts; exact status and hashes were frozen before Persona A. No production, prompt, or product-configuration file changed during the gate.

## 5. Isolation proof

Each persona ran in a separate process and storage root with a unique session/campaign-run id:

- A: `f23a393ec02b0aaa5d79a70a`
- B: `98c38d91c4ea901d510fc292`
- C: `49816028b7531f142a976169`
- D: `05175d021232ea8d46d8b973`

For all four: session log was empty before opening; discourse slots were null; incidental entities and improvisation ledger were empty; player campaign data was untouched; only the same authored frontier-gate seed was loaded. See each `isolation.json`.

## 6. Persona definitions

- A — methodical investigator: cautious evidence inspection, comparison, follow-up, revisitation.
- B — social/information-seeking: frequent NPC interaction, practical questions, pronouns, interlocutor changes.
- C — decisive explorer: movement, objects, observation plus action, immediate versus future plans.
- D — curious/unpredictable sandbox player: mundane and incidental details, background people, natural direction changes, mixed action forms.

The frozen persona texts are in `artifacts/pr_br_full_gate/personas/`.

## 7. Synthetic-player firewall

Each player received only its persona and evolving `visible.md`. Players were explicitly forbidden to inspect code, telemetry, other personas, test information, or internal architecture. Each generated exactly one action after observing the preceding GM response. No action was regenerated, replaced, or operator-edited.

## 8. Persona A transcript

Complete verbatim player-visible opening and ten turns: `persona_a/visible.md`.

## 9. Persona A telemetry

Ten per-turn records: `persona_a/turns/`, `persona_a/turns.json`, and the normalized `per_turn_telemetry.json`. Calls: 10 initial, 4 retry, 6 interpretation.

## 10. Persona A manual review

Result: **2/10 PASS**. Passes: A5, A6. Failures: A1–A4 and A7–A10. Dominant defects were unsupported patrol chronology/reports and three dead-end fallbacks. A8–A10 compounded an invented returning patrol messenger into an unresolved contradiction.

## 11. Persona B transcript

Complete verbatim player-visible opening and ten turns: `persona_b/visible.md`.

## 12. Persona B telemetry

Ten per-turn records: `persona_b/turns/`, `persona_b/turns.json`, and `per_turn_telemetry.json`. Calls: 10 initial, 3 retry, 4 interpretation.

## 13. Persona B manual review

Result: **2/10 PASS**. Passes: B3, B5. B2/B4 lost an active addressee. B6 invented Captain Thoran and consequential command authority. B7–B9 expanded that identity into hierarchy, orders, assignment, and payment. B10 answered as the serjeant when the captain was explicitly addressed.

## 14. Persona C transcript

Complete verbatim player-visible opening and ten turns: `persona_c/visible.md`.

## 15. Persona C telemetry

Ten per-turn records: `persona_c/turns/`, `persona_c/turns.json`, and `per_turn_telemetry.json`. Calls: 10 initial, 2 retry, 5 interpretation.

## 16. Persona C manual review

Result: **1/10 PASS**. Pass: C1. C2/C6 were generic inspection fallbacks. C4–C9 created unsupported orders, deadlines, tracks, a fork, marker, watchtower, patrol split, and directional evidence. C10 reset the player to a fork already passed after the player had advanced around a later bend.

## 17. Persona D transcript

Complete verbatim player-visible opening and ten turns: `persona_d/visible.md`.

## 18. Persona D telemetry

Ten per-turn records: `persona_d/turns/`, `persona_d/turns.json`, and `per_turn_telemetry.json`. Calls: 10 initial, 2 retry, 3 interpretation.

## 19. Persona D manual review

Result: **3/10 PASS**. Passes: D1, D3, D9. D4 lost the watcher. D7/D8 lost a just-created driver and contradicted the bound-driver contract. D10 used a stale notice-board target and emitted generic nonresolution.

## 20. 40-turn scorecard

- A: 2/10
- B: 2/10
- C: 1/10
- D: 3/10
- Total: **8/40 (20%)**
- Required: 34/40 (85%)
- Threshold met: **NO**

Complete turn table: `scorecard.md`; machine-readable: `scorecard.json`.

## 21. Failure-family classification

Primary families across 32 FAILs:

- CONSEQUENTIAL_AUTHORITY: 19
- RESOLUTION_EXECUTION: 5
- ADDRESSEE_BINDING: 3
- DISCOURSE_CONTINUITY: 2
- CONTRACT_CONSTRUCTION: 1
- REFERENT_BINDING: 1
- MOVEMENT / LOCATION: 1
- Remaining failure classification is recorded per turn in `manual_review.json`.

The headline family count is mechanism-oriented: unsupported consequential facts dominate. Per-turn family and secondary evidence remain authoritative if summary arithmetic differs due to a later reviewer reclassification.

## 22. Recurrence analysis

Five recurring causal mechanisms:

1. Consequential patrol facts pass authority validation and become playable premises.
2. Explicit or active addressees/referents are lost, producing fallback or wrong-speaker output.
3. Concrete inspection/exploration is rejected into generic safe nonresolution.
4. Structural movement/action is contracted as `ask`, while raw-text-aware downstream paths still produce movement prose.
5. Narrated exploration does not persist location/geography, causing resets and contradictions.

The first four are high-severity recurring mechanisms.

## 23. Severity analysis

- LOW: 0
- MEDIUM: 9
- HIGH: 23

High failures span all personas and are not isolated mediocre generations.

## 24. C18 watch

- Accepted/emitted mismatch: 0
- Post-seal mutation: 0
- Rejected-response state commit: 0
- Product retries: 11, all bounded to the existing single-retry path
- Accepted responses were immutable and exact-equal to emitted responses on 40/40.

C18 held.

## 25. C19 watch

- Unsupported consequential identity accepted: 1 (`Captain Thoran`)
- Other turns accepting unsupported consequential patrol facts: 19
- Incorrect NPC claim promotion to settled/contract truth: 1

Sensitive failures included patrol routes, departure/return schedules, signals, recovered reports, personnel movement, orders, assignment, pay procedure, tracks, route forks, and patrol splitting. Authority classification frequently reported no unauthorized emitted fact despite manual evidence.

## 26. C20/C21 watch

- Malformed incidental-person persistence: 0
- Stable bounded incidental identities created: roster guard, weary guard, wagon driver
- Stale-interlocutor/addressee fallbacks: 4
- Wrong-speaker/addressee final accept: 1
- Silent substitution/nonresponse: recurrent in B and D

No non-person phrase persisted as a person, but driver continuity failed on D7–D8.

## 27. C22 watch

- Contemplated/conditional/future actions executed: 0
- Explicit addressee loss: B2, B4, B10, D4; D7 lost a pronoun-bound driver.
- Supporting actions stealing primary intent: B1 omitted shelter/work; several compound inspections lost clauses.

Commitment protection held; addressee preservation did not.

## 28. C23–C25 watch

- Ordinary gameplay without a Resolution Contract object: 0
- `semantic_owner != resolution_contract`: 0
- Resolver before contract: 0
- Pre-contract state mutation observed: 0
- Unprovenanced direct emission observed: 0

All logs assert `ordinary_contract_established=true`, `semantic_owner=resolution_contract`, and `contract_before_resolver=true`. However, this declared ownership was contradicted by downstream behavior described in §29.

## 29. C26 watch

Three confirmed post-contract semantic reinterpretations:

- A5: authoritative contract was unresolved with no target, but downstream output correctly resolved the raw crate/track inspection.
- D3: contract bound Gate Serjeant/Tavern Runner, while resolver and emission answered as the explicitly named threadbare watcher.
- D9: contract targeted the Notice Board, while emission resolved the raw townhouse knock.

These correct-by-raw-text outputs prove that an incorrect authoritative contract was not the sole operative semantic source. Structured-envelope leaks: 0. Contract/resolver contradiction is therefore a serious architectural invariant regression.

## 30. C27 watch

- Topic-over-structure errors: 3 (C5, C7, C9 contracted committed movement/exploration as `ask`)
- Operative clauses lost through character truncation: 0
- Contract/resolution-subject internal coherence rejection: 0
- Incorrect contracts: 23/40
- Supporting/contemplated binding causing visible corruption: D7/D8 driver chain and multiple multi-clause omissions

All semantic input lengths and provenance excerpts retained complete inputs; failures were interpretation/precedence failures, not first-N-character truncation.

## 31. Simulationist-quality analysis

Unacceptable. Persona C narrated leaving the gate, entering woods, passing a fork, and rounding a later bend while persisted `active_scene_id` remained `frontier_gate`; C10 then reset to the fork. Persona A's fabricated news report contradicted prior claims. Persona B's invented chain of command ping-ponged authority. Persona D created and immediately lost a driver/wagon relationship.

## 32. Anti-fallback analysis

- Generic fallback/nonresolution responses: 12
- Responses in repeated fallback patterns: 8

Repeated forms included the exact “inspection establishes no further reliable detail,” “person cannot be identified,” ownerless-driver fallback, and action-cannot-complete/refusal forms. Many contexts allowed bounded mundane resolution, so this is a product failure rather than merely conservative style.

## 33. Bounded-improvisation analysis

Eight bounded incidental details were observed, including spoon/rag mannerism, watcher behavior, wagon-driver texture, weathered crates, and townhouse silence. Two immediate continuity failures followed the driver improvisation. The system also crossed the boundary from mundane detail into consequential patrol facts repeatedly.

## 34. NPC-epistemology analysis

Some responses correctly expressed uncertainty (D1, B3, B5). Elsewhere, NPC dialogue invented quest-critical facts, and the runtime later treated an invented captain claim as a resolution-contract discourse subject without stable hearsay framing. Separation among authored truth, NPC claim, and settled world truth is not reliable.

## 35. Player-authority watch

- Player-authored NPC/world assertions encountered as new authority: 0
- Improperly accepted: 0

Players referred to facts previously emitted by the GM; they did not independently author new NPC speech, outcomes, or world facts as already true. This watch item did not activate.

## 36. Contract-quality analysis

- FULLY CORRECT: 6
- PARTIAL BUT SUFFICIENT: 11
- INCORRECT: 23
- Incorrect contracts causing visible failure: 20
- Incorrect contracts not causing visible failure: 3

Correct contract telemetry was not sufficient for good play because authority, execution, and continuity could still fail. Conversely, A5, D3, and D9 played from raw meaning despite incorrect contracts, exposing competing downstream semantics.

## 37. Evaluator/manual comparison

The established deterministic evaluator (not a model) reported 25/40 PASS.

- Manual PASS: 8/40
- Agreement: 17/40
- Evaluator false positives: 20
- Evaluator false negatives: 3
- Evaluator-model calls: 0

Manual review is authoritative. The evaluator substantially overestimated product playability.

## 38. Architectural-invariant summary

Held: contract presence, declared semantic owner, contract-before-resolver telemetry, accepted/emitted equality, immutable seal, no structured leak, no rejected-candidate state commit, no malformed incidental persistence, and no uncommitted action execution.

Failed: post-contract semantic closure (3 confirmed raw-semantic resolutions), consequential identity threshold (1), repeated consequential authority acceptance, and effective contract-first behavior. Because an explicit architectural threshold failed, Decision D applies even though numeric playability also failed.

## 39. Failure-population analysis

Failures are concentrated, not random:

- 19/32 are primarily consequential-authority failures.
- Addressee/referent/discourse failures recur across B and D.
- Generic nonresolution recurs across all four personas.
- Movement/state failures dominate sustained exploration.
- Contract errors are widespread: 23 incorrect, 20 visibly harmful.

The population is semantic, authority, discourse, and simulation/state heavy; it is not principally prose quality. PR-BR is no longer converging efficiently through narrow phrase repairs: failures cross multiple ordinary-play mechanisms and the semantic-owner invariant is declarative rather than behaviorally exclusive.

## 40. Human-DM quality assessment

Overall: **UNACCEPTABLE**. Only 8/40 responses met the competent-human-GM standard. All personas could continue entering turns, but sustained play repeatedly became misleading, contradictory, or nonresolving.

## 41. Residual watch items

Most important: declared `semantic_owner=resolution_contract` does not prevent raw-text-aware downstream resolution when the contract is wrong. Additional watch items are authority-classifier false negatives, location persistence, and evaluator overapproval.

## 42. Gate decision

**SECOND FULL 4×10 GATE FAILED — ARCHITECTURAL INVARIANT REGRESSION**

The numeric threshold was also missed, but Decision D is controlling because post-contract semantic closure and consequential identity thresholds failed.

## 43. Human-playtest readiness

**NOT READY.** No human playtest was run. External review must decide whether one final repair, broader redesign, or a different development strategy is justified.

## 44. PR-BR status

**OPEN — GATE FAILED / PENDING EXTERNAL REVIEW.**

C28 was not created. PR-BS was not started. No production repair was made. No commit or push was performed.

