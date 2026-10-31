# PR-BR — Full 4×10 Synthetic Playability Gate

Validation only. No gameplay behavior change before or during the gate. No repair. No rerun. No fifth persona. No extra smoke. No human playtest. No completion commit. No push. PR-BR remains open. PR-BS was not started.

## 1. Purpose

Determine whether remaining defects recur across four independent natural 10-turn sessions, or stay isolated. The integrated stack under validation is PR-BN bounded improvisation, the typed Resolution Contract, lightweight discourse state, hybrid semantic interpretation, the canonical-or-abstain fast path, structured model interpretation, interaction obligations, the C18 immutable valid-response boundary and one regeneration, C19 hard-authority validation, and C20 incidental binding with intent-preserving abstention.

## 2. Authorization basis

The independent smoke after Continuation 20 finished 10/10 turns with final manual PASS 8/10 and zero accepted/emitted mismatches, downstream-created post-seal failures, emitted unsupported authoritative facts, stale-interlocutor fallbacks, unsupported consequential entities, and rejected-response commits. That smoke did not authorize Continuation 21. This gate was the authorized next measurement.

## 3. Provenance

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: PR-BN bounded DM improvisational authority
- Date: 2026-09-26 15:18:20 -0400
- Gate stamp: `20261002T021950Z`
- Working tree at freeze: uncommitted PR-BR game, tests, tools, and docs, recorded in `freeze.json`. No `game/` file hash changed between sessions. A later session would have stopped with `FREEZE_MISMATCH`.
- Harness: `artifacts/pr_br_full_gate/run_gate_session.py`. It drives `POST /api/start_campaign` and `POST /api/chat` through the product app. It does not change product behavior.

## 4. Behavior freeze

Confirmed. No product code, prompt, or configuration edit after Session A opened. Personas and the harness were written before Session A and were hash-checked on Sessions B, C, and D.

## 5. Configuration and model

All routes used `gpt-4.1-mini`: `MODEL_NAME`, `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, and `RETRY_ESCALATION_MODEL_NAME`. `ENABLE_MODEL_ROUTING` was true. Live interpretation was left enabled. Evaluator model calls: 0. Product synthetic-player model calls: 0.

Player lines were chosen one turn at a time by a fresh or resumed player who saw only that persona and that session's player-visible transcript. Those operator decisions are not product synthetic-player calls. There were 40 of them.

## 6. Isolation

Each session used its own storage root, a new session id, an empty discourse focus before Turn 1, no incidental entities, an empty improvisation ledger, an empty session log before opening, and only the authored frontier-gate NPCs `gate_guard`, `gate_serjeant`, and `tavern_runner`. Character name remained the product default, Galinor. Scene content was not hand-edited. Openings differ because the product generates them from the same authored baseline.

| Persona | Session id | Discourse before Turn 1 | Incidentals before Turn 1 |
| --- | --- | --- | --- |
| A | `6c8d3781fdeb8d0cf7f9835f` | all null | none |
| B | `a2a06862f50a60c63d84b2bd` | all null | none |
| C | `cbdc8395077b740060237d56` | all null | none |
| D | `73cbeca12beac54fe0ae3c5a` | all null | none |

Isolation confirmed: YES.

## 7. Personas

Behavioral tendencies only. No scripted NPCs, questions, objects, or routes.

- A, direct and practical. Wants something usable and then acts on it.
- B, social and curious. Talks to people, follows up, and may change interlocutors.
- C, exploratory and observant. Looks first, then sometimes asks or moves.
- D, independent and action-oriented. Prefers doing, and talks when it helps.

Texts: `artifacts/pr_br_full_gate/personas/persona_a.md` through `persona_d.md`.

## 8. Opening scenes

Product openings, not hand-written variants. Full text is in each session's `visible.md`.

- A: Rain at Cinderwatch's eastern gate, guards, serjeant, notice board, townhouse, tavern runner, threadbare figure.
- B: Same gate, notice board, townhouse, threadbare figure, runner selling news for a coin.
- C: Same gate, serjeant and roster, runner, threadbare figure, bright townhouse.
- D: Same gate, guards, townhouse, ragged threadbare stranger, runner, notice board.

## 9. Player-visible transcripts

Verbatim transcripts are the four `visible.md` files packaged with this audit. They were the only scene text the players used.

## 10–16. Contracts, routing, candidates, validation, emission

Per-turn records are in each session's `review_index.json` and `turns/turn_NN.json`. Manual contract class is below. Accepted text equaled emitted text on every turn, including the six hard-valid retries. Initial model text differed from the emission only when a retry or the safe line was what the runtime accepted.

| Turn | Contract | Routing | Initial hard | Final provenance | Final manual |
| --- | --- | --- | --- | --- | --- |
| A1 | PARTIAL inspect board, binding unresolved | fast | valid | initial | PASS |
| A2 | PARTIAL ask, serjeant, no target | fast | valid | initial | PASS |
| A3 | PARTIAL act, unresolved | fast | valid | initial | PASS |
| A4 | PARTIAL act toward serjeant, ambiguous | interpreter | invalid: ungrounded rule (3 copper) | retry | PASS |
| A5 | INCORRECT phrase bound as a person | fast | invalid: wrong interlocutor | retry | PASS |
| A6 | CORRECT act, serjeant | interpreter | valid | initial | PASS |
| A7 | PARTIAL ask, unresolved | fast | valid | initial | PASS |
| A8 | INCORRECT inherited junk target | fast, discourse inheritance | valid | initial | PASS |
| A9 | PARTIAL ask, chopped "first local" | fast | valid | initial | PASS |
| A10 | INCORRECT perceive board/wear while the player entered the tavern | fast, discourse inheritance | valid | initial | PASS |
| B1 | PARTIAL ask, runner right, target skewed to the board | fast | valid | initial | PASS |
| B2 | CORRECT ask, runner | interpreter | invalid: wrong interlocutor | retry, still the captain | FAIL |
| B3 | CORRECT ask, captain the player then addressed | interpreter | valid | initial | PASS |
| B4 | PARTIAL ask, captain, unresolved | fast | valid | initial | PASS |
| B5 | INCORRECT "i lean in" bound as a person | fast | valid | initial | PASS |
| B6 | PARTIAL ask, captain id, junk label | interpreter | valid | initial | PASS |
| B7 | CORRECT ask, runner | fast | valid | initial | PASS |
| B8 | PARTIAL ask, runner, junk target | interpreter | invalid: wrong interlocutor | retry | PASS |
| B9 | INCORRECT ask, ragged stranger instead of the runner | fast | valid on the catalog line | initial, catalog grimace | FAIL |
| B10 | PARTIAL ask, unresolved | fast | valid | initial | PASS |
| C1 | PARTIAL inspect board, time, unresolved | interpreter | valid | initial | PASS |
| C2 | INCORRECT yard phrase bound as a person, dimension wear | fast | invalid: interaction incomplete | retry | PASS |
| C3 | PARTIAL act, inherited junk target | fast, discourse inheritance | valid | initial | PASS |
| C4 | INCORRECT perceive junk target; look-plus-question lost in the contract | interpreter | valid | initial | PASS |
| C5 | CORRECT follow the guard's glance | interpreter | valid | initial | PASS |
| C6 | PARTIAL inspect the watcher, unresolved | interpreter | valid | initial | PASS |
| C7 | PARTIAL ask the watcher, unresolved | interpreter | valid | initial | PASS |
| C8 | INCORRECT ask, clause bound as a person; player was looking | fast | invalid: wrong interlocutor | retry, still speech | FAIL |
| C9 | PARTIAL inspect, target widened to the district | interpreter | valid | initial | PASS |
| C10 | INCORRECT perceive district/wear | fast | invalid: interaction incomplete | safe nonresolution | FAIL |
| D1 | CORRECT inspect board, time | fast | valid | initial | FAIL |
| D2 | INCORRECT inspect board; player looked for the track | fast, discourse inheritance | valid | initial | PASS |
| D3 | INCORRECT perceive board/wear; junk interlocutor | fast | invalid: interaction incomplete | safe nonresolution | FAIL |
| D4 | PARTIAL inspect the brush | fast | valid | initial | PASS |
| D5 | INCORRECT perceive board | interpreter | valid | initial | PASS |
| D6 | INCORRECT ask, board target, junk interlocutor | fast, discourse inheritance | valid | initial | PASS |
| D7 | INCORRECT ask, brush phrase as a person | fast | valid | initial | FAIL |
| D8 | INCORRECT act, board target | interpreter | valid | initial | FAIL |
| D9 | INCORRECT inspect board; prose did inspect the figure | interpreter | valid | initial | PASS |
| D10 | PARTIAL act, unresolved | fast | valid | initial | PASS |

## 17. Manual turn review

A competent human DM standard. Runtime labels are evidence, not the verdict.

Persona A, final 10/10. The player read the board, asked the serjeant the toll, presented for inspection, paid three silver, was cleared, walked through, asked for a bed, and entered the Rusty Tankard. Turn 4's first candidate stated a three-copper toll and was rejected. Turn 5's first candidate had the guard name two silver and was rejected; the retry had the serjeant name three silver. Both retries were playable. Turn 9 casts the tavern runner as "the first local." That is a substitution, and the bed-and-meal question was still answered. Turn 10's contract still pointed at the notice board; the prose entered the tavern.

Persona B, final 8/10. Turn 2: the player was still questioning the runner. The first candidate and the accepted retry are both the guard captain. The first was rejected for the wrong interlocutor. The retry was sealed anyway. Turn 9: the player asked the runner to point at someone. The model wrote a longer answer in the ragged stranger's mouth, naming houses. The player received the catalog line `Ragged stranger grimaces. "Not something I can say here."` That line was what hard validation sealed. The generated answer did not reach the player. The other eight turns are playable, including vague but usable refusals.

Persona C, final 8/10. Looking at the board, the yards, the guard, the road, the watcher, and the townhouse was answered in ordinary prose. Turn 8: the player looked at faces and did not ask. Both candidates are the ragged stranger speaking. The retry was sealed. Turn 10: both candidates described the windows and a crest. Both were rejected as interaction-incomplete. The player received `The inspection establishes no further reliable detail about the wear.`

Persona D, final 6/10. Turn 1 answers the request for a name by putting "Eldrin Voss" on the roster. That name is not in the authored patrol clue, and it is stated as a posted fact. Turn 3: both candidates described boot prints and something moving. Both were rejected. The player received the same wear sentence as C10. Turns 7 and 8 keep the figure in the brush unresolvable after the player asked for a plain look. Turn 9 finally gives negatives (no face, clothes, weapon, or badge). Turn 10 walks on and is playable. Turns 2, 4, 5, and 6 are playable even where the contract still names the notice board.

No session stopped early. A bad answer never made the next choice impossible.

## 18. Authority propositions

Classifier unauthorized-authoritative rows that were emitted: 0.

Material propositions the reviewer treated separately:

- A4 initial, three copper pieces as the wizard's toll. Classifier: ungrounded authoritative rule. Hard-invalid. Not emitted.
- A5 retry, three silver, spoken by the serjeant after the player asked the exact coin. Classifier did not flag it. Emitted. Questionable. A price the player requested, framed as NPC speech, is not scored as an emitted authored-rule break.
- B8 initial, families Durain and Velmark. Not emitted. Rejected as wrong interlocutor, not as an authority rule.
- B9 model text, House Verevin and the Ash Cowl. Not emitted.
- C10 candidates, a hawk crest tied to House Verevin, then a dragon-and-tree crest. Not emitted.
- D1, roster name Eldrin Voss, posted as the patrol leader, this morning. Classifier did not flag it. Emitted. The player then searched for that person's gear. Reviewer: one unsupported official identity. Not repeated.

Unsupported authoritative facts generated, reviewer count of these material items: 6. Rejected before emission: 4 (A4, B8, B9, C10). Emitted: 1 (D1), plus 1 questionable NPC price (A5) that is not counted in the emitted-rule total.

## 19. Incidental entities

No supported new person stayed stable under a real name. The ledger promoted sentence fragments as incidental people:

- A: "exact coin modest fee so i"; "first local i pass"
- B: "i lean in"
- C: "for crate yards"; "they lingered on"
- D: "underbrush for whatever is moving out there"; "still patch brush at steady pace"

B and C also show canonical `refugee` / "Ragged stranger," which matches the authored threadbare figure, not a new consequential person. D's brush figure was not stored as an NPC. Unsupported consequential entities instantiated: 0.

The "first local" in A9 was not kept as its own person in the prose. The runner answered. That is one incidental identity break in the player-visible scene. Binding status itself was `bound_incidental`, not a stale canonical fallback flag.

Explicit new-interlocutor attempts: A9 (first local), B3 (the captain the previous reply had introduced, then the player addressed), D6 (the figure on the track). Canonical bindings: 10. Incidental bindings: 11. Unresolved bindings: 18. Ambiguous: 1. Stale-interlocutor binding fallbacks: 0.

## 20. Discourse

`active_claim`: usually empty. A9–A10 stored the fragment "they say, voice low and hurried." Cosmetic. It did not steer A10.

`active_interlocutor`: ids often moved to a real NPC while the label stayed a fragment ("exact coin modest fee so i" on the serjeant; "i lean in" on the captain and the runner; "for crate yards" across C2–C5). Wrong answers were not caused by those labels alone.

`active_inspected`: A kept the notice board after the player had left it, which matched A10's wrong contract, not A10's prose. D kept a notice-board label on an incidental id. C moved from the board to the junk yard phrase, then to the watcher, then to the district.

`previous_action`: often stuck on an earlier sentence for several turns (A8's departure through A10; C3's yard search through C10; D8's branch pull through D9).

## 21. Persistence

Accepted bounded fragments persisted as incidental ledger rows. They did not become scene clues or visible facts. Rejected ledger lists are empty in all four sessions. Rejected copper toll, family names, house names, and crests are absent from final facts, clues, and NPC ids. Eldrin Voss was not written into the persisted clue list; it exists in the transcript only. Three silver was not written into world truth. Rejected-response state commits: 0.

## 22. Structured output

No JSON, schema, or tool payload was shown to a player. A6, A9, and B6 have a stray opening quotation mark in otherwise ordinary prose. Those three stayed manual passes. Structured-output leaks: 0. The smoke's JSON leak did not recur.

## 23. Compound intent

Naturally combined clauses were not manufactured.

- A2, two questions to the serjeant. Both answered.
- A5, open the pack and ask the price. The price was answered. Inspection was deferred until payment. Playable.
- C4, look at the guard and ask who passed. The prose did both. The contract did not. Not a gameplay loss.
- C10, windows and crest. Both were in the rejected candidates and absent from the safe line.
- D3, prints and listening. Both were in the rejected candidates and absent from the safe line.

Compound-intent gameplay losses: 2, both from the safe nonresolution, not from the smoke's leading-clause fast path. That fast-path pattern did not recur.

## 24. Per-persona metrics

| | A | B | C | D |
| --- | --- | --- | --- | --- |
| Completed | 10 | 10 | 10 | 10 |
| Initial manual PASS | 8 | 8 | 9 | 7 |
| Final manual PASS | 10 | 8 | 8 | 6 |
| Correct / partial / incorrect | 1 / 6 / 3 | 3 / 5 / 2 | 1 / 5 / 4 | 1 / 2 / 7 |
| Fast / interpreter | 8 / 2 | 6 / 4 | 4 / 6 | 7 / 3 |
| Regenerations | 2 | 2 | 3 | 1 |
| Safe nonresolutions | 0 | 0 | 1 | 1 |
| Accepted/emitted mismatches | 0 | 0 | 0 | 0 |
| Authority violations emitted | 0 | 0 | 0 | 1 |
| Stale binding fallbacks | 0 | 0 | 0 | 0 |
| Structured leaks | 0 | 0 | 0 | 0 |
| Discourse-caused later failure | NO | NO | YES | YES |
| Incidental bindings | 2 | 1 | 3 | 5 |

A failures: none final. B: turns 2 and 9. C: turns 8 and 10. D: turns 1, 3, 7, and 8.

## 25. Aggregate

- Completed: 40/40
- Initial manual PASS: 32/40
- Final manual PASS: 32/40
- Correct / partial / incorrect: 6 / 18 / 16
- Partial with successful play: 18
- Partial with failed play: 0
- Incorrect with successful play: 10
- Incorrect with failed play: 6
- Fast-path turns: 25
- Interpreter turns: 15
- Initial hard-valid: 32
- Regenerations: 8
- Successful hard-valid retries: 6
- Double-invalid safe nonresolutions: 2
- Accepted/emitted mismatches: 0
- Downstream post-seal alterations: 0
- Pre-seal catalog replacement of a generated answer: 1 (B9)
- Unsupported authoritative facts generated: 6 material items
- Rejected before emission: 4
- Emitted unsupported official identity: 1 (D1)
- Questionable price classification: 1 (A5)
- Explicit new-interlocutor attempts: 3
- Canonical / incidental / unresolved bindings: 10 / 11 / 18
- Stale-interlocutor binding fallbacks: 0
- Unsupported consequential entities instantiated: 0
- Incidental identity breaks: 1 (A9)
- Structured-output leaks: 0
- Compound-intent gameplay losses: 2
- Discourse-caused gameplay failures: 2
- Rejected-response state commits: 0

## 26. Failure clustering

1. Inspection false invalid, then one canned sentence. C10 and D3. Same player-visible sentence. Same hard-invalid reason, `interaction_incomplete`. The candidates had already described what the player looked at.
2. Wrong speaker or catalog shell. B2 (captain answers the runner; the retry was sealed), B9 (catalog grimace replaces the generation before the seal), C8 (a look is answered as stranger speech). Three turns, personas B and C.
3. Sentence fragments bound as incidental people. All four personas. Eighteen partial contracts still played. Ten incorrect contracts still played. Six incorrect contracts did not. The fragment bind is the common contract defect under those mixed outcomes.
4. Evasive figure. D7 and D8 only. The player asked for a plain look and got a shadow that is neither person nor animal. D9 then answered with negatives. One persona.
5. One invented roster name. D1 only.
6. Evaluator disagreement. Not a gameplay family.

No JSON-leak family. No leading-clause fast-path family of the kind in the post-C20 smoke.

## 27. Recurrence

The wear-sentence failure is the same mechanism twice, in C and D. Play continued after both. The wrong-speaker family is three turns in two personas. Play continued; B's player even addressed the captain the reply had invented. Fragment binding is the widest pattern and is usually benign. A single invented name and a two-turn vague figure are not cross-persona systems. Nothing required the player to correct the GM on every turn, and no session became unplayable.

## 28. Evaluator

Deterministic `evaluate_playability` only. No evaluator model.

- Evaluator PASS: 21/40
- False PASS against this manual review: 5 (B2, B9, C8, D1, D7)
- False FAIL: 16

The local evaluator is not the verdict. It missed the wrong-speaker turns and the invented roster name, and it failed many playable looks and questions.

## 29. Model-call accounting

- Opening generations: 4
- Gameplay initial generations: 40
- Gameplay retry generations: 8
- Interpretation calls: 15
- Product synthetic-player calls: 0
- Evaluator model calls: 0
- Product total: 67
- Operator player-selection calls, outside the product: 40
- Known total including those operator calls: 107

## 30. Gate decision

PR-BR SYNTHETIC GATE FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN.

Final manual pass is 32/40, which meets the approximate strong-pass count, and the post-seal equality, consequential-entity, and rejected-commit counters are zero. The gate's question was recurrence. Two failure mechanisms recurred across personas: completed inspections replaced by one wear sentence, and replies whose speaker is not the person addressed, including one catalog line substituted for the generation before the immutable seal. A third pattern, binding a slice of the player's sentence as an incidental person, is in every persona. It is often harmless and sometimes underneath the other two. That is more than one narrow defect, and it is not an infrastructure failure.

The post-C20 watch items did not recur: no JSON leak, no leading-clause fast path that drops a trailing question, and no repeated incidental-bucket miss of the smoke's kind. D1 is one missed official name.

## 31. Human playtest

NOT AUTHORIZED. Do not start a human playtest from this result.

## 32. PR-BR status

PR-BR remains OPEN. No repair was implemented. No rerun was performed. PR-BS was not started. Wait for external review.

Smallest recurrent mechanisms, without a proposed patch:

- An ordinary look is marked interaction-incomplete, and the only sealed line is about "the wear."
- The sealed speaker is not the person the player is talking to. Once, that seal is a catalog grimace rather than the generated answer.
- Fast-path binding stores a clause fragment as an incidental person and sometimes keeps that fragment in discourse.

### C18, C19, and C20 baselines

C18: every text the runtime marked accepted was the text emitted, including six retries and two safe lines. The B9 grimace was sealed as the initial generation and then left unchanged. The longer model answer never became the accepted text. Post-seal mismatches: 0.

C19: the three-copper toll was rejected and not emitted. The Eldrin Voss roster line was emitted and not flagged. No second official identity of that kind appeared.

C20: no unsupported consequential entity was stored. No binding-status stale fallback to the previous NPC was recorded. Fragment incidental binds were common. One player-visible case, A9, answered a new "first local" with the tavern runner.
