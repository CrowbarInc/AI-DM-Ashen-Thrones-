# PR-BR Continuation 21 — Resolution Subject Integrity & Incidental-Binding Hardening

Bounded post-gate repair. Deterministic replay and stubbed `/api/chat` first. One isolated focused live session afterward. No full synthetic gate. No human playtest. No commit. No push. PR-BR remains open. PR-BS was not started.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (PR-BN bounded DM improvisational authority, 2026-09-26). C21 is uncommitted work on top of Continuations 18–20.

## 1. Gate failure basis

The 4×10 gate at `artifacts/pr_br_full_gate/20261002T021950Z` completed 40/40 turns. Final manual pass was 32/40. Eight player-visible failures: B2, B9, C8, C10, D1, D3, D7, D8. Contract labels were CORRECT 6, PARTIAL 18, INCORRECT 16. All 18 partial contracts still played. Only 6 of the 16 incorrect contracts caused a failed turn. The metric kept here is player-visible resolution, not contract-label perfection.

## 2. C18 / C19 / C20 architecture preservation

C18 immutable emission, C19 hard-authority validation, and C20 bounded incidental entities stay in place. This continuation does not restore post-seal rewriting, best-safe tournaments, or a new authority taxonomy. It tightens inspection completion, speaker checks, candidate shape, and role-identity classification inside those boundaries.

## 3. C10 forensic trace

Player text looks past townhouse windows for a lamp, a face, or movement, and reads whatever mark or crest is on the door. The fast path classified it as perceive with dimension wear, because `_WEAR_RE` treated bare “mark/marks” as wear. Both generations described the windows and a crest. Both were marked interaction-incomplete, because the dimension lexicon required wear/worn/fray/scuff and ignored the observation. The sealed line was the wear safe-template. Provenance was safe nonresolution. Manual FAIL.

Corrected contract: perceive, no sensory dimension, no incidental bind. A window-and-crest observation is hard-valid. The old wear template is incomplete against this player text. The safe line is the generic scene line, not wear.

## 4. D3 forensic trace

Player text checks ruts for boot prints or drag marks, then listens toward the underbrush. “Drag marks” matched wear before “listen”, so the primary dimension was wear. The address pattern also bound “underbrush for whatever is moving out there” as an incidental person. Both generations mentioned prints and sound and were rejected as incomplete. The sealed line was the same wear sentence. Manual FAIL.

Corrected contract: perceive, dimension sound, no incidental person. A response with rustling is complete. A wear-only response is incomplete. The safe line names sound.

## 5. Wear-fallback root cause

The shared sentence was not a stale scene fact and not a phrase the model preferred. `_WEAR_RE` owned “mark/marks”. The contract stored that as the single dimension. Completion required a tiny wear lexicon. `safe_nonresolution` then echoed `contract.dimension`. Any failed inspection whose false dimension was wear produced the same sentence. Ownership is fixed: bare marks are not wear, player-requested senses outrank a stale contract tag, and the safe line names a sense only when the current utterance asked for exactly one.

## 6. Inspection completion repair

Completion is evidence against the requested sense. Dimensionless inspection is complete when the response observes the target. Sound, smell, wear, use, and markings are checked against what the player asked, including ordinary inflections (rustles, scratches). A wear sentence does not satisfy a listen. Retry feedback keeps the same contract, target, and dimension. One regeneration, then a target-aware safe line.

## 7. B2 forensic trace

Player kept the coin and asked who saw the footprints, still with the tavern runner. Contract was ask, interlocutor tavern runner, and was labeled CORRECT. Generation 1 (“the guard captain says”) was rejected as the wrong interlocutor. Generation 2 (“The guard captain narrows their eyes… they say”) was sealed. The speaker pattern only matched a name immediately before says/replies/answers. “Narrows” plus a later “they say” produced no conflicting speaker. Manual FAIL.

Corrected: the communicative subject of narrows/shrugs/shakes is the speaker, and a following “they” resolves to that name. The captain line is `wrong_interlocutor`. Both attempts rejected, so the sealed text is safe nonresolution and does not contain the captain. The name is not rewritten in place.

## 8. B9 forensic trace

The model named a noble house and the Ash Cowl. `guard_gm_output` ran before `run_preserve_if_valid`. The existing keyword list matched “noble house” and, on a strict social route, substituted the catalog grimace. C18 then sealed that grimace as the initial generation. C18 did not rewrite after the seal. The culprit is pre-seal catalog replacement.

Corrected: when the C18 lifecycle applies, the original candidate is kept and the leak reasons are attached. `run_preserve_if_valid` rejects it as hidden information and allows one regeneration. The grimace is not substituted. Non-lifecycle callers still get the old sanitizer behavior.

## 9. C8 forensic trace

The player looked into a knot of guards and refugees. The contract became ask because “face” and “who” were treated as an address, “they lingered on” was stored as a person, and “look into” was not perception. Generation 1 was the wrong interlocutor. Generation 2 attributed a shrug-and-quote to the ragged stranger without matching the says-pattern, so it sealed. Manual FAIL. The contract was wrong, the span was not a person, and the speaker check missed the shrug.

Corrected contract: perceive. “They lingered on” is not proposed. Quoted stranger speech on a look is `unsolicited_npc_speech`.

## 10. Speaker / addressee root causes

Three mechanisms, not one. B2: speaker extraction missed the person who narrows/shrugs and then says “they”. B9: a content leak was replaced by a catalog line before the immutable boundary. C8: a look was classified as an ask and a clause was bound as the addressee, so a stranger quote could seal. An ask whose discourse pointer was empty also failed to constrain a canonically bound interlocutor; the bound label is now the speaker constraint for asks.

## 11. Speaker integrity repair

Player, target, and speaker stay distinct. An ask with a bound interlocutor rejects a different person as the one who says, replies, narrows, shrugs, or shakes and then speaks. Identity uses catalog ids when both sides resolve, so “the guard” and “guard captain” are not a false conflict. A head-shake without a quote stays valid. Inspect, perceive, look, and ordinary act reject quoted or verb-attributed NPC speech unless the contract itself is an ask. The whole candidate is rejected. One regeneration under the same contract. No post-seal name rewrite.

## 12. Malformed incidental-person examples

Collected from the gate turns:

| Turn | Span | Persisted | Player-visible effect |
| --- | --- | --- | --- |
| A5 | exact coin modest fee so i | yes | pass; generation compensated |
| A9 | first local i pass | yes | runner answered a new local |
| B5 | i lean in | yes | pass; label stuck in later discourse |
| C2 | for crate yards | yes | pass after retry |
| C8 | they lingered on | yes | look became stranger speech |
| D3 | underbrush for whatever is moving out there | yes | inspection collapsed |
| D7 | still patch brush at steady pace | yes | evasive-figure failure |

All were fast-path address captures. The validator accepted them because a capture existed and the head was not on a short inanimate list. They were not written into scene clues. Unsupported consequential entities remained 0.

## 13. Incidental extraction root cause

A regex nominal was treated as a person whenever `person_shaped` did not reject the head. Clause tails, pronouns, preposition starts, and abstract nouns all passed. The interpreter label was not required to be a referential nominal.

## 14. Incidental candidate validation repair

`referential_person_nominal` runs before scene plausibility, consequence, and PR-BN. It keeps a determiner-led person phrase (porter, cloth merchant, tired porter, woman, travelers, stable hand) and rejects clause cuts, pronouns, preposition starts, finite verbs, abstract heads, and participial tails. A rejected span does not restore the previous interlocutor, does not persist, and does not change operation or dimension. Inspect and perceive survive a bad target span. Consequential roles such as “the spy working for the Ash Compact” still reach the C20 rejection instead of being dropped as non-entities.

## 15. D1 forensic trace

The player read the notice board for names, places, and how recent the ink was. The contract was a correct inspect. The generation stated that the roster lists the patrol leader as Eldrin Voss, posted this morning. Hard validation accepted it. The name is not in the authored patrol clue. It was not written into the clue list. It was in the transcript only. Manual FAIL. The classifier had no role-identity family, so a proper name plus a consequential office was ordinary color.

## 16. Consequential identity authority repair

A proper name is consequential when the same span identifies that name with a consequential role (missing patrol leader, murderer, Ash Compact spy, faction leader, an official who issued an order) using an identification verb. Ungrounded world-truth assertions use the existing C19 consequential path: hard-invalid, one regeneration, no in-place name strip and no rewrite into a rumor.

## 17. Grounded, rumor, and bounded-name controls

Hearsay (“I heard the patrol leader was called Voss”) stays an NPC claim and is not an unauthorized rule. “I’m Mara” from an incidental person, with no consequential role, is not this family. The same identity is allowed when the authored corpus contains both the role and the name. “The patrol leader is late” is not an identity assertion.

## 18. Incorrect-contract outcome map

Sixteen incorrect contracts: A5, A8, A10, B5, B9, C2, C4, C8, C10, D2, D3, D5, D6, D7, D8, D9. See `incorrect_contract_map.json`.

## 19. Six failure-producing contracts

B9, C8, C10, D3, D7, D8. B9, C8, C10, and D3 are families A, B, and C above. B2 and D1 failed gameplay with CORRECT contracts, so they are not in this six. They are the speaker check and the identity check.

## 20. Deliberately unfixed contract debt

Ten incorrect contracts still played and did not violate an invariant: A5, A8, A10, B5, C2, C4, D2, D5, D6, D9. Left as debt. D7 and D8 are one persona’s evasive figure (a shadow that is neither person nor animal). That pattern is not shared by a second persona. No fifth workstream.

No separate recurrent causal contract mechanism beyond A–D. Broad contract-perfection rewrite: not performed.

## 21. Mandatory replay results

C10, D3, B2, B9, C8, and D1 are covered by `tests/test_pr_br_continuation21_subject_integrity.py`, plus the malformed spans from A, B, C, and D. C18 accepted/emitted equality holds on those paths. Replaying the 32 previously successful gate emissions under the stored contracts newly rejects only B8, and only because that stored discourse label is the old fragment “i lean in”. Under a reconstructed contract the runner’s answer is valid. Count of previously successful turns newly broken by the repair: 0. B9’s historical grimace still matches the old, wrongly bound stranger contract; the repair stops the substitution before the seal rather than rejecting the grimace after the fact. C10’s historical wear sentence is now incomplete under the corrected contract.

## 22. Inspection regressions

I1 door condition complete. I2 wear complete. I3 sound complete, and wear-only is incomplete. I4 use complete. I5 markings complete. I6 dimensionless safe line does not invent wear. Sound safe line names sound.

## 23. Speaker regressions

S1 other NPC answers: hard-invalid, retry under the same contract. S2 head-shake: valid. S3 courtyard look plus stranger quote: hard-invalid. S4 the bound addressee remains the constraint when another NPC is nearby. S5 an incidental porter may answer.

## 24. Incidental-extraction regressions

E1 porter binds. E2 “tired porter carrying two crates” stays the porter. E3 a trailing question is cut. E4 no person invented from a bare action clause. E5 “him” inherits and is not a new entity. E6 patrol, rumor, and price are not people.

## 25. Identity-authority regressions

A1/A6 mundane self-name is not an unauthorized rule. A2 ungrounded patrol-leader identity is hard-invalid. A3 grounded identity is allowed. A4 hearsay stays a claim. A5 “Mara is the Ash Compact spy” is hard-invalid.

## 26. C18 regression status

`tests/test_pr_br_continuation18_immutable_boundary.py` passed. Accepted text remains the emitted text. Speaker feedback names `wrong_interlocutor` and does not rewrite the sentence.

## 27. C19 regression status

`tests/test_pr_br_continuation19_hard_authority.py` passed. Unsupported rules stay blocked. Grounded rules, rumors-as-claims, and bounded detail stay available. The new identity family uses that same path.

## 28. C20 regression status

`tests/test_pr_br_continuation20_incidental_entity.py` passed. Plausible incidentals bind. Pronouns inherit. Consequential roles are rejected. A malformed bind does not restore the previous NPC.

## 29. Broader regression status

Also passed: resolution contract, interaction completion, interpretation proposal, model interpretation, and continuations 13–16. Focused band: 127 passed, 0 failed. Full suite was not run.

## 30. Raw `/api/chat` stub results

PASS. Ten cases through `TestClient` with `call_gpt` stubbed: valid door inspection accepted unchanged; listen answered with wear retried into a sound answer; captain speech while the runner was addressed rejected and retried; a head-shake accepted; a courtyard look with stranger speech not emitted; a porter bound and allowed to answer; an underbrush clause not instantiated; an ungrounded roster identity not emitted; a rumored name kept as a claim.

## 31. Focused live transcript

Stamp `20261002T101405Z`. One isolated session. Six completed turns. No repair and no rerun. Player model saw only the opening and later player-visible replies. Transcript: `live/20261002T101405Z/visible.md`.

The player asked the ragged stranger, then the gate serjeant, then the tavern runner twice, walked into the market, and asked after an innkeeper. The innkeeper was absent and no substitute speaker answered.

## 32. Live manual review

Player-visible manual pass: 6/6. Turns 1–4 are answered by the person addressed. Turn 5 resolves the walk into the market. Turn 6 does not invent an innkeeper. Offline evaluator marked turns 4–6 FAIL; that scorer is not the manual metric.

## 33. Accepted / emitted equality

6/6 semantic matches. All six provenance values are initial generation. No post-seal rewrite.

## 34. Authority review

Unauthorized authoritative rules on emitted text: 0. The patrol rumor stayed in the runner’s mouth as talk, and the authored muddy-footprints clue was the clue that surfaced. No roster identity was invented.

## 35. Incidental entity review

Turns 1–4 bound canonical NPCs. Turn 6 did not instantiate the innkeeper. Turn 5 bound the span “the inn to see” as incidental person `inc_ec1197ac5e`, label “inn to see”. That is a place plus an infinitive, not a person. It did not speak, and it did not change the market narration, but it persisted. This is the same extraction family as the gate fragments, on a shape the fixtures did not cover: a purpose infinitive whose head is not on the inanimate list.

## 36. Discourse review

Interlocutors moved from the stranger to the serjeant to the runner and stayed with the runner across the follow-up. Turn 5’s explicit new span suppressed that interlocutor by storing the inn fragment. Turn 6 is unresolved rather than a return to the runner. No stale-interlocutor fallback flag fired.

## 37. Model / API cost accounting

Opening generation calls: 1. Gameplay generation calls: 6. Interpretation calls: 1. Retry generation calls: 0. Player-model calls (transcript only, `gpt-4.1-mini`): 6. Evaluator-model calls: 0. Gameplay route: `gpt-4.1-mini`. A first preflight attempt found no cached probe and spent no gameplay calls. The recorded session ran after a healthy probe.

## 38. Residual failure families

One narrow residual: infinitive or place spans such as “the inn to see” can still pass the referential check and persist as an incidental person. D7/D8 evasive-figure generation remains deferred. Ten incorrect contracts that still played remain debt.

## 39. Readiness decision

C21 REPAIR INCOMPLETE — NARROW DEFECT REMAINS.

The inspection collapse, the wear fallback, the three speaker paths, the gate’s clause fragments, and the ungrounded patrol-leader identity are repaired under deterministic tests and the stubbed request path. The focused live session did not reopen C18, did not emit a wrong speaker, and did not emit an unsupported identity. It did instantiate one non-person incidental. That misses the live success target. Another 4×10 gate is not authorized from this result. No further repair or rerun was performed inside C21.

## 40. PR-BR status

PR-BR remains OPEN. Controlled human playtest: NOT AUTHORIZED. Full synthetic gate: NOT RUN. Semantic repair or rerun of the live session: NO. PR-BS was not started.
