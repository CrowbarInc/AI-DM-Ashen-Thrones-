# PR-BR architectural reassessment

Claim ownership, proposition decomposition, and temporal authority.

Cycle: discovery only. Evidence is the saved four-turn run
`artifacts/pr_br_final_live_validation/20261004T035044Z`
(HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`).
This cycle made no gameplay call, no model call, no production edit, no new detector, and no test patch.

## 1. Executive conclusion

The semantic claims that reach the player are owned, today, by the narrator. The GM Resolution Decision owns a list of facts it already knew. After prose exists, `audit_narrated_claims` tries to reconstruct what the prose meant. When a sentence contains enough aliases of an authored observation, that reconstruction copies the observation's authority onto the whole sentence.

That is what Turn 3 did. Authoritative state established only that the bathhouse pump handle is bowed and its pivot pin is sheared. Narration added that sudden, violent pressure seems a likely cause. The accepted audit stored one `NarratedClaim` whose text is that whole sentence and whose identity is the pump observation: `authored_world_fact`, `world_truth`, `established`, source `scene.visible_facts.0`.

`NarratedClaim` is an annotated sentence. It is not a proposition. The temporal ledger is a descriptive memory written after sealing. It is not an input to authorization. `gm_inferences` stayed empty because nothing in the live path creates a `gm_inference` row unless narration is later recognized as one. Uncertainty is treated as a reason to stop accounting, so a hedged cause, a negative-evidence sentence, and an investigative lead can be consequential and still produce no decision claim.

The stated contract of `game/gm_resolution_decision.py` is already the right ownership rule: the decision is source-owned, and prose does not become consequential world truth. The implementation violates that rule by authorizing sentences after they are written. The architecture is salvageable by making the decision own the complete consequential claim set before narration, and by making narration realize that set.

Turn 2's "person you addressed" fallback is a separate routing defect. It should not drive the redesign. It did choose Nessa as Turn 3's speaker, which made "from what I saw" sound like testimony. The laundering mechanism does not depend on that speaker.

The 333 passing deterministic tests measured detector vocabulary and direct function calls. They did not measure this production composition: unrestricted prose, loose alias coverage, uncertainty exemptions, and a ledger that is written too late.

## 2. Four-turn proposition timeline

The full timeline is `artifacts/pr_br_claim_ownership_reassessment/PROPOSITION_TIMELINE.md`.

Compressed authority path:

| ID | Proposition | Born | Ends as |
| --- | --- | --- | --- |
| P1 | Handle bowed | Authored state | `world_truth`, then used as a stamp |
| P2 | Pin sheared | Authored state, same fact as P1 | Same stamp |
| P3 | Excessive wear is possible | Turn 1 prose | Unresolved speculation. Not a `gm_inference`. |
| P4 | Sudden pressure is possible | Same Turn 1 sentence as P3 | Same speculation row |
| P5 | Sudden pressure is likely | Turn 3 prose | Audit says authored `world_truth` |
| P6 | Sudden pressure caused the damage | Entailed by P5 | No separate object; inherits P5's stamp |
| P7 | Some actor applied it | Turn 2 question; Turn 3 presupposition | Decision says unresolved; prose still presupposes the event |
| P8 | Recent pump users may know | Turn 3 prose | Emitted, no decision claim |
| P9 | Nearby witnesses may know | Same Turn 3 sentence | Emitted, no decision claim |
| P10 | No hint of recent disturbance | Turn 1 prose | Non-consequential uncertain NPC claim, because the word `around` is a hedge token |
| P11 | Speaker saw the event | Turn 3 "from what I saw" | Absorbed into the world-truth sentence |
| P12 | Nessa looks up briefly | Turn 4 manner on an authored action | Emitted, no claim row |
| P13 | Lavender soap | Turn 4 NPC speech | `claim_only` hearsay, then persisted nowhere |
| P14 | Prefers lengthwise folding | Same quotation | Same missing persistence |

Sealed text equaled emitted text on all four turns. The seal worked. It sealed the auditor's classification.

## 3. Turn 1 ownership

Player: "I examine the bowed pump handle and the sheared pivot pin closely. What does this damage suggest?"

The contract `rc_9c97a3580116` kept the subject and the operation `inspect`. It lost the requested epistemic operation. `dimension` is null. Construction used the deterministic fast path. `model_interpreter_invoked` is false.

`_INTERPRETATION_RE` in `game/resolution_contract.py` accepts "what does this suggest" and "what does the damage suggest". It does not accept "what does this damage suggest", because `this` consumes the determiner and `damage` then blocks `suggest`. No interpretation dimension is stored. `build` of the decision appends `INFER` only when `interpretation` is in the dimension set (`game/gm_resolution_decision.py`, the block that starts `if "interpretation" in dims`). Turn 1's epistemic acts are five `establish` rows. There is no `INFER`.

Initial narration introduced three extra propositions: great force twisted the handle, wear is possible, sudden pressure is possible, and there is no hint of recent disturbance. The great-force sentence contains `suggests`, which `_EVIDENTIAL_RELATION_RE` matches, so it was rejected as `unauthorized_evidential_relation` and preserved out. The wear/pressure sentence contains `is unclear`, which `_UNKNOWN_SLOT_RE` matches, so it was accepted as `speculation` / `unresolved` / `do_not_persist`. The disturbance sentence produced no decision claim.

Answers:

1. No component authorized P3 or P4. The decision's narration constraints say narration may not establish consequential facts absent the decision. They do not list wear or pressure as permitted inferences.
2. They were emitted because generation is unrestricted prose. The auditor then failed to see two cause propositions. It saw one sentence that matched an uncertainty pattern, and uncertainty is authorized.
3. Classification was `speculation` / `observation` / `unresolved` / `unknown_cause_actor_or_time`. It was not `gm_inference`. The disturbance sentence was classified by the older proposition classifier as a non-consequential uncertain NPC claim, and it was absent from `claim_results`.
4. `remember_temporal_claims` writes `gm_inferences` only for authorized claims whose provenance is already `gm_inference`. A `speculation` row is skipped. Discourse focus stored the sentence as `active_claim` with source `speculation`. That is focus, not authority.
5. Yes. Unresolved speculation is currently treated as safe to emit and safe to forget. `_ordinary_residual_reasons` returns immediately when `epistemic_frame` is uncertain, rumor, hearsay, or speculative. `_structured_consequential_reasons` returns immediately when `_is_claim_or_uncertain` is true.
6. That treatment is conceptually wrong. Modality and consequence are different axes. "Maybe the duke ordered the murder" is uncertain and still introduces an actor, an act, and a cause. Turn 1's "whether it was excessive wear or sudden, violent pressure" introduced two causes. Turn 2's player immediately treated one of them as a premise. The hedge did not make the proposition harmless.

## 4. Epistemic modality versus authority

The code mixes these axes in three places.

- `epistemic_frame` in `game/proposition_authority.py` returns empty for "can't swear", uncertain for a hedge list that includes `might`, `could`, and `around`, and `world_truth` otherwise. Family `none` plus an uncertain frame becomes `npc_claim` with `consequential=false`.
- `_is_claim_or_uncertain` in the decision auditor uses that frame plus a second hedge list. Uncertainty then suppresses residual claims.
- `_claim_from_row` does not read modality at all. If an authorized observation matches, the sentence's epistemic status becomes `established` whenever the observation's authority is `world_truth` and the identity has no `epistemic_status`.

So low certainty is implemented as "stop looking" or "not consequential". It is not implemented as "record a low-authority proposition".

Conceptual matrix, used as a diagnostic rather than a mandatory schema:

|  | Authorized source | No authorized source |
| --- | --- | --- |
| Certain | Established fact. P1 and P2. | Unsupported assertion. The rejected "great force" sentence is this when the detector fires. |
| Likely | Grounded inference. No live example. The decision never created one. | Generated inference. P5. Live audit put it in the established cell. |
| Possible | Grounded hypothesis. What an `INFER` act should have produced for P3 and P4. | Generated hypothesis. P3 and P4 as actually emitted. |
| Unknown | Epistemic limit. "The cause is not established." | Unsupported lead or absence if the sentence adds a new proposition. P8, P9, and P10. |

P5 should occupy "likely / no authorized source". The audit placed it in "certain / authorized source" because the sentence also contained P1 and P2.

## 5. Exact Turn 3 laundering path

Sentence:

> I can't swear to it, but from what I saw, sudden, violent pressure seems a likely cause of the bowed handle and sheared pin.

It contains at least:

- A. The handle is bowed. Authored.
- B. The pin is sheared. Authored.
- C. Sudden, violent pressure likely caused that damage. Not authored.
- D. The speaker saw the relevant event. Not authored.

Pipeline for the accepted initial generation:

1. `audit_narration_against_decision` splits on sentence punctuation and calls `audit_narrated_claims` per sentence.
2. `epistemic_frame` sees `can't swear`, matches `_NOT_AN_ASSERTION_RE`, and returns an empty frame. The sentence is therefore not uncertain. `classify_propositions` drops it. That is why the parallel `authority` array contains only sentences 2 and 3.
3. `_is_claim_or_uncertain` is false. `_UNCERTAIN_FRAME_RE` lists `couldn't swear`, not `can't swear`. The early NPC-claim return does not run. "from what I saw" is not in `_ATTRIBUTED_SOURCE_RE`, which lists "from what i heard".
4. `_authorized_rows_for_sentence` walks `proposed_facts`. The pump row has a semantic identity, so the empty-identity extra-token rule is skipped.
5. `_semantic_identity_matches` succeeds. Subject aliases `pump` and `pivot pin` are absent, but `_text_has_subject_or_head_with_value` accepts the head `handle` once a value alias is present. Value aliases `bowed`, `sheared`, and `sheared pin` are present. Relation `observation` is not required when a value matches. Polarity is positive. The identity has no cause qualifier to enforce. `_semantic_overreach_reasons` looks for `because`, `caused by`, `after thieves`, and similar forms. `likely cause` misses.
6. `_claim_from_row` builds one `NarratedClaim`. `text` is the entire sentence. `semantic_identity`, `provenance`, `authority`, `persistence`, and `source_ref` are copied from the observation. Missing epistemic status is filled with `established` because authority is `world_truth`.
7. Residual detectors then run on the same string and miss:
   - `_CAUSAL_RELATION_RE` wants `because`, `caused by`, `due to`, `therefore`, `led to`, `responsible for`. It does not want `cause of`.
   - `_EVIDENTIAL_RELATION_RE` wants `suggests`, `indicates`, `shows`, `proves`. It does not want `seems`.
   - `_EVENT_CAUSE_ATTRIBUTION_RE` wants forms such as `died from` and `explains the`.
   - `_CERTAINTY_UPGRADE_RE` wants `proves`, `clearly`, `confirms`, `no doubt`.
8. `classify_narrated_fact` sees only authorized claims and returns `claims[0]` as the sentence's fact. Hard validation is valid. No retry. The seal stores that classification.

The exact point where some authorized content becomes "the sentence is authorized" is step 6: `_claim_from_row`, called from `audit_narrated_claims` after `_semantic_identity_matches`.

A second gate would also launder. After residuals, if any covered row exists and no unauthorized claim object has been appended, reasons named `unowned_stateful_world_assertion`, `proposition_authority`, and `unauthorized_consequential_residual` are discarded. This sentence did not need that gate. The identity copy had already decided.

`_empty_identity_covers` already says a second proposition must not inherit a fact's authority, and it allows at most one extra content word. That function is used only when the fact has no semantic identity. Giving the pump fact an identity disabled the stricter rule. Structured identity matching is looser than the lexical fallback it was meant to replace.

Sentences 2 and 3 of the same reply never appear in `claim_results`. Sentence 2 contains `might` and `possibility`. Sentence 3 contains `could`. Both are uncertain, so residual collection returns nothing, identity coverage fails, and the decision audit stores no claim. The older classifier marks both `npc_claim` / `uncertain` / `consequential=false`, which is not a hard violation. The witness/recent-user lead and the "possibility rather than certainty" sentence are therefore emitted without decision ownership. The uncertainty sentence happens to be the right thing to say. Its lack of a claim row is still an accounting hole.

## 6. NarratedClaim reality check

For the Turn 3 causal sentence there was one `NarratedClaim`.

Proposition decomposition failed because the unit of audit is `_sentences` output: one punctuation-delimited string. The claim constructor copies that string and overlays the first matching authorized identity. It does not split actor, cause, object, time, or modality into further claims.

There is also a residual-detector layer that can append more `NarratedClaim` objects for the same string when a regex hits. Those extra objects still use the full sentence as `text`. They are sentence annotations with a reason code, not extracted propositions. On Turn 3 the residual layer appended nothing.

`NarratedClaim` is an annotated sentence or span. It is not a proposition.

The fields that look propositional (`semantic_identity`, `relation_kind`, `epistemic_status`) are copied from the authorized fact that happened to match, or filled with a detector label such as `evidential`. On Turn 3 the identity says `relation=observation` while the sentence asserts a cause.

## 7. Claim generation versus claim reconstruction

Architecture A, the current one, is reconstruction:

1. The decision authorizes material it already has, mostly authored observations.
2. The model writes unrestricted prose.
3. The validator infers propositions from that prose with alias overlap and residual patterns.
4. Authorized overlap can license the rest of the sentence.
5. Sentences the patterns do not recognize are either dropped or labeled non-consequential.

The practical limit of this reconstruction is visible in one ordinary reply. The same subsystem rejected "suggests great force" on Turn 1 and accepted "seems a likely cause" on Turn 3. The difference is which words were in the pattern lists. A deterministic validator that must discover every consequential proposition in arbitrary English is doing NLI with a growing phrase list. This project has already rejected general NLI. Further residual patterns would repeat the 333-test failure mode.

That does not prove no reconstruction algorithm could exist. It does prove that sentence coverage plus residual vocabulary cannot be the authority mechanism. The empty-identity rule shows the codebase already knows a sentence can contain an authorized fact and a second proposition. The identity path does not apply that knowledge.

Architecture B, claim-first realization:

1. The decision creates or accepts explicit claims.
2. Narration realizes those claims.
3. Narration may add bounded incidental texture.
4. Validation checks that realization did not add a consequential claim outside the set.

Turn 3 is the evidence that B's check has to happen against an explicit set. If the set contains only "handle bowed", "pin sheared", and "cause unknown", a realization that asserts a likely cause is outside the set even if the validator cannot paraphrase English in general. The structured claim is the object that is authorized. The prose is not.

## 8. Minimal claim-first architecture

Smallest object that prevents the Turn 3 outcome without general NLI:

```text
RealizationClaim
  claim_id
  proposition_identity   # actor, relation, object, cause, time, polarity, modality
  provenance             # authored_world_fact | gm_inference | player_hypothesis | npc_claim | ...
  epistemic_status       # established | inferred | hypothesis | unresolved
  authority              # world_truth | observation | claim_only | unauthorized
  realization_role       # MUST_STATE | MAY_STATE | MAY_INFER | MUST_PRESERVE_UNCERTAINTY | INCIDENTAL_TEXTURE
  persistence            # world_truth | claim_only | do_not_persist | temporal bucket
```

For the bathhouse confidence turn the decision set is:

- MUST_STATE P1 and P2, authority `world_truth`.
- MUST_PRESERVE_UNCERTAINTY on cause, actor, and event time.
- No MAY_INFER cause, because this turn's act is a confidence answer, not a new inference, and a player hypothesis must not be promoted.
- INCIDENTAL_TEXTURE may add manner. It may not add a cause, a witness class, or a roster.

The narrator is asked to realize that set. If the model still emits "likely cause", the seal compares the realization's structured claims to the set. A cause slot with modality `likely` and provenance `authored_world_fact` is rejected because the authorized cause slot is unresolved. The rejection does not require the validator to understand the paraphrase "the pump was damaged by a sudden force" as English. It requires the realization channel to name the slots it used.

This prevents Turn 3's recorded outcome: the mixed sentence can no longer become `world_truth` by containing the words `bowed` and `sheared`. It does not, by itself, stop a model from hiding a cause in prose while omitting it from the structured channel. The compatibility rule for that hole is the one `_empty_identity_covers` already states for identity-less facts: extra propositional content does not inherit coverage. Applied to identity matches, the Turn 3 sentence fails closed because it adds a cause. That check is structural once cause is a slot, and it is a compatibility fallback rather than a new domain vocabulary list.

## 9. Natural inference ownership

A competent GM may offer "it could be age, or something may have struck it" without an author having prewritten those alternatives. Those hypotheses are still claims. They are owned by the GM Resolution Decision, as accepted inferences, before they are narrated.

Sufficient flow when the alternatives are generic:

- Player asks what the damage suggests.
- Contract operation is interpretation. Epistemic act is `INFER`.
- A bounded resolver creates hypothesis claims: more than one ordinary physical explanation is compatible; none is established; actor, time, and specific cause stay unresolved.
- Provenance `gm_inference`. Authority `observation` or a dedicated hypothesis authority. Persistence bounded. Modality `possible`.
- Narration realizes those claims in ordinary language, which may surface as wear versus force.
- The surfaced wording is stored as the claim's realization text. Repeating it later does not raise authority.

The generic claim can be deterministic. The attractive wording cannot. Model creativity belongs in realization, or in a structured candidate that the decision accepts. It does not belong in untyped prose that the auditor must rediscover.

If the specific alternatives themselves must be invented, the model can propose them as structured candidates first:

```text
{relation: cause, object: pump_handle, cause: sudden_pressure, modality: possible, polarity: positive}
{relation: cause, object: pump_handle, cause: excessive_wear, modality: possible, polarity: positive}
```

The decision accepts both as `gm_inference` and rejects any candidate that fills actor, time, or certainty. Narration then realizes the accepted pair and the uncertainty. The player can later ask "if sudden pressure, who?" and the decision sees a player hypothesis whose cause slot matches an existing inference, and answers that the actor is unresolved. It does not reclassify the cause as world truth.

## 10. One-stage versus two-stage model use

The measured run used 7 model calls: 4 initial generations, 2 retries, 0 interpretation calls, 1 preflight. Retries were Turns 1 and 2.

A two-stage call, proposal then prose, adds a completion on turns that invent inferences. That is the wrong default. Most turns realize authored or already-accepted claims and need no new semantic invention. An extra round trip costs latency and a second prompt full of state.

A single generation call can carry the authorized claim set in and return `claims[]` plus narration. Output tokens grow by the claim list. The round trip count stays one when the returned claims are inside the authorized set. When the model adds a candidate cause, that candidate is classified before seal. Unauthorized candidates force the same kind of retry the system already uses, scoped to the extra claim rather than to an unlabeled sentence. Expected cost on a Turn 3-like failure is one initial call plus one retry, which this run already spent on Turns 1 and 2.

Deterministic inference covers the epistemic limit ("cause, actor, and time are not established") and the generic "more than one explanation is compatible". It does not need to name wear or pressure. Those names are realization. Structured candidates are warranted when a specific new hypothesis should persist. They are not warranted for towels, soap, or a glance.

Reliability favors the structured channel because the object under test is a slot record the tests can construct without a model. Complexity is the new claim object and the rule that sentence coverage no longer grants sentence authority. That is smaller than another residual-pattern campaign.

## 11. Temporal provenance authority

1. The ledger is not consulted before claim authorization. `audit_narrated_claims` takes the sentence, the decision, and the authored corpus. It does not take the session ledger.
2. It is consulted as prompt text for a later turn, via `prompt_projection_for_temporal_provenance`, and it is written after seal by `remember_temporal_claims` from `sealed_temporal_claims`. The prompt instructions say inferences are not world truth. The auditor does not enforce that sentence.
3. Yes. A proposition known as `player_hypothesis` was accepted as `authored_world_fact` because its sentence mentioned the authored observation. The ledger row itself was not mutated. A parallel audit classification said world truth. The invariant failed at authorization, not inside the ledger writer.
4. No monotonicity invariant is enforced. `remember_temporal_claims` refuses to copy an existing row into a higher bucket only by ignoring world-truth claims entirely (`else: continue`). It does not compare a new world-truth claim against an existing hypothesis.

The invariant belongs in the decision, before narration and again at seal:

A proposition cannot gain authority through repetition, paraphrase, or co-occurrence. Promotion requires an explicit authorized event: resolver establishment, authored state, an accepted state mutation, or an authoritative discovery result.

Concretely, authorization of a cause slot reads the ledger. If the best existing record is `player_hypothesis` or `gm_inference`, the slot's ceiling stays at that authority unless an establish act names that slot. Co-occurrence with an observation is not an establish act.

`player_hypothesis` persisted on Turn 2 because `player_hypothesis_claims` classifies the player utterance directly, using a pattern for `if` and `so ... bent`. That path is independent of narration quality. It is why the ledger can be right while the audit is wrong.

## 12. Proposition identity

Assignment today:

- Authored facts carry a hand-built identity: `kind`, `subject`, `subject_aliases`, `relation`, `value`, `value_aliases`, `polarity`. Matching is phrase substring, with a head-word fallback.
- Generated inferences, when a test inserts one, often carry only `{relation_kind: epistemic_status, epistemic_status: inferred}`. The live Turn 1 speculation claim is that thin. The rejected force claim is `{relation_kind: evidential}` plus the raw sentence.
- Player hypotheses carry `{relation_kind: epistemic_status, epistemic_status: hypothesis}` plus the entire player utterance. The fingerprint in `remember_temporal_claims` is normalized text, provenance, authority, and source turn.
- Identity does not survive paraphrase. "Sudden violent pressure caused the damage" and "the pump was damaged by a sudden force" share no structural key.
- Identity is tied to raw text for ledger rows, and to alias lists for authored facts.
- A structural identity can exist without general NLI if claims are created as records. The minimum slots are actor, relation, object, cause, time, polarity, and modality. Alias lists remain a realization aid for wording, not the definition of sameness.

The pump identity has no cause, actor, time, or modality slot. Matching therefore cannot notice that a sentence adds one. The player-hypothesis identity has no cause slot either, so Turn 3 could not ask whether the narrated cause was the same proposition as the stored hypothesis.

## 13. Gameplay leads

P8 and P9 are actionable leads, not world facts. They still change what a player does next. The current taxonomy can call them an NPC claim or miss them. `active_actionable_lead` stayed null.

| Kind | Example | Permissible? | Owner |
| --- | --- | --- | --- |
| A. Generic capability | "You could ask around." | Yes, as incidental texture. No new entity. No persistence as evidence. | Narration, inside INCIDENTAL_TEXTURE. |
| B. State-grounded lead | "Nessa said the mechanic keeps notes," when that statement is an accepted claim or authored fact. | Yes. Authority follows the grounding claim. | Decision, as a lead claim whose source is that fact. |
| C. Invented specific lead | "Recent pump users may have seen what happened." | No, unless a recent-user set or witness is already authorized. | Decision. Absent a source, the realization is rejected. |
| D. Invented evidence-bearing lead | "The ledger may contain the culprit's name." | No. This invents a clue. | Decision. Same rejection as an unauthorized discoverable. |

Turn 3 emitted kind C. A first-class `gameplay_lead` is warranted as a realization role and a provenance, with the same authority ceiling as other claims. It does not need a large planner. It needs the rule that a lead introducing a new class of person or object is a consequential claim.

## 14. Negative evidence

P10, "no hint of recent disturbance around the pump", is an absence claim. Absence of footprints, forced entry, blood, reaction, or disturbance can close an investigation. The current system treated P10 as harmless because:

- `_HEDGE_RE` includes `around`, so `epistemic_frame` returned `uncertain`.
- Uncertain plus family `none` became a non-consequential NPC claim.
- The decision auditor emitted no claim row.
- Preservation kept the sentence.

Required behavior: an epistemic limit ("the damage does not show who did it") is authorized by `LEAVE_UNRESOLVED` or `MUST_PRESERVE_UNCERTAINTY`. A world-absence ("nothing nearby was disturbed") is a negative proposition and needs an authored observation, an inspection result, or an explicit decision claim. Narration may not invent it as texture. The word `around` must not be what decides.

## 15. Turn 2 routing classification

Turn 2 is a local semantic routing defect.

Player: "So if sudden, violent pressure bent the handle and sheared the pin, who could have put that pressure on the pump?"

Saved contract `rc_aaecd4f6bceb`:

- Fast path captured target `pump` from a preposition and canonicalized it to the place `Dunmere public bathhouse pump alcove`.
- `active_claim_inherited` is false, even though the Turn 1 speculation claim was in the candidate list.
- Entity binding proposed the span `So` as a new interlocutor and rejected it as `proposal:not_referential_entity`. `interlocutor_rejected` is true. `interlocutor_id` is null.
- Expected resolution became `clarification`.
- Narration answered in Nessa's voice. Response validation rejected `wrong_interlocutor` twice, because the contract had no interlocutor to preserve.
- The sealed fallback was "The person you addressed cannot be identified clearly enough to answer."
- Independently, `player_hypothesis_claims` stored the player sentence correctly and did not promote it.

This does not share the coverage-laundering mechanism. The decision did not stamp a cause as world truth. The failure is referent and speaker selection on the fast path, followed by a speaker-enforcement fallback that assumes an addressee the contract had already rejected. It should be repaired as routing. It should not be solved by a new claim ontology.

Coupling to note, without merging the defects: after this turn the session's social target became Nessa, and Turn 3's contract inherited `interlocutor_id=nessa` with `epistemic_mode=npc_claim`. That is why the confidence answer was spoken as testimony. The testimony sentence was then laundered by the claim auditor. Fixing routing would change the speaker. It would not stop the same sentence, in narrator voice, from inheriting `world_truth`.

## 16. Turn 4 incidental classification

The lavender soap and the lengthwise folding preference are real incidental NPC invention. They are not authored knowledge. They are not consequential mystery facts. Classifying them `npc_claim` / `claim_only` / `hearsay` is the right authority ceiling.

They should persist as NPC claims so a later turn can stay consistent. They should not persist as world truth.

They persisted nowhere:

- `accepted_incidentals` remained empty because `remember_temporal_claims` ignores authorized claims that are not incidental, `gm_inference`, or `player_hypothesis`.
- `bounded_improvisation.entries` remained empty and `last_bounded_improvisation_promotion.accepted_count` is 0. The promoter reads improvisation proposals, not decision `claim_results`.
- The quoted claim in the audit is one span for both soap and folding. The glance sentence was not a claim at all.

NPC dialogue does have a separate persistence path. This turn did not enter it. The architecture can distinguish mundane invention from authored knowledge at audit time, and then drops the distinction before the next turn. That is an ownership gap between the claim audit and the two ledgers, not a failure of incidental freedom. The prose itself was the successful part of Turn 4.

## 17. Why 333/333 failed to predict live behavior

Immediately before this live run, the localized-repair campaign recorded 333/333 broad deterministic tests and 51/51 targeted claim-control tests (`handoff/history/pr-br-localized-live-repair/REVIEW.md`). Those tests call auditors and ledger writers with hand-built decisions. The live session called the fast-path contract, unrestricted generation, preservation, speaker enforcement, the proposition classifier, the decision auditor, and the temporal writer in that order.

| Live failure | Class | Why the green tests stayed green |
| --- | --- | --- |
| Turn 1 lost `interpretation` / `INFER` | A, D, E | `_INTERPRETATION_RE` is tested on phrasings it accepts. "What does this damage suggest?" is a missing scenario. The decision-builder test that expects `INFER` supplies the dimension the fast path failed to produce. |
| P3/P4 never became `gm_inference` | D, F | Ledger tests insert a row that is already `provenance=gm_inference`. They do not run Turn 1's speculation classification through `remember_temporal_claims`. |
| Turn 2 place/addressee fallback | A, E | The 333-test band does not compose incidental-entity binding, place canonicalization of `pump`, and `wrong_interlocutor` rejection. |
| Turn 3 cause laundered to `world_truth` | C, D, E | Slice 2 rejects "died from", "killed", "explains", and "because". It does not include "seems a likely cause" beside an observation alias. Tests assert `hard_valid is False` for those phrases. They do not assert that a mixed sentence's copied identity stays non-world. The empty-identity extra-token rule is not what identity-bearing facts use. |
| Turn 3 leads survived | C, E | The lead pattern requires clue/evidence/useful/answer. "Recent users" and "witnesses" are outside it. Uncertainty then suppresses residuals. |
| Temporal ledger did not bind the audit | F | Tests check that an inserted hypothesis row is not rewritten in place. They do not check that a later audit refuses to classify overlapping prose as `world_truth`. |
| Turn 4 incidentals vanished | E, F | Tests do not connect `claim_results` of kind `npc_claim` to either persistence bucket. |

Future deterministic testing should replay saved production traces through the real composition, with no model call:

- Feed the saved Turn 3 sentence and the saved decision into `audit_narration_against_decision` and assert the cause slot is not `world_truth`.
- Feed the saved Turn 1 sealed text into `sealed_temporal_claims` and assert a spoken cause alternative becomes `gm_inference` or is rejected, and does not disappear as unlabeled speculation.
- Replay the four saved player utterances through contract construction and assert interpretation, claim inheritance, and interlocutor separately from authority.
- Assert the monotonicity invariant on slot identity: an existing `player_hypothesis` cause is not authorized as `authored_world_fact` by co-occurrence.
- Keep phrase-list tests only as fixtures for a slot, not as the definition of the slot.

A new passing test that adds `likely cause` to a regex would reproduce the 333-test mistake.

## 18. Responsibility map

| Responsibility | Current owner | Should own | Current failure | Change required? |
| --- | --- | --- | --- | --- |
| Player intent interpretation | Deterministic fast path; model interpreter was not invoked | Resolution Contract | Turn 1 dropped interpretation. Turn 2 bound a place and the token `So`. | Yes, local routing and the interpretation pattern. Separate from claim ownership. |
| Requested epistemic operation | Contract dimensions, then decision acts | Resolution Contract, copied onto the decision | `INFER` exists only if the dimension survived | Yes. The act must be present before narration. |
| Authoritative observations | Authored state, copied into the decision | Decision, as MUST_STATE claims | Sound for P1/P2, then copied onto other sentences | Yes. Coverage must not export their authority. |
| Generated inference | Narration, reconstructed later | Decision, as accepted `gm_inference` claims | P3–P6 created in prose; ledger empty; P5 stamped world truth | Yes. This is the ownership change. |
| Player hypothesis | `player_hypothesis_claims` on player text | Decision, reading the ledger | Row stored correctly and ignored by the audit | Yes. Ledger becomes an authorization input. |
| NPC claim | Decision audit when a quote or speech verb matches; otherwise the older classifier | Decision, as `claim_only` | Turn 3 testimony was not a claim. Turn 4 quote was. | Yes. Speaker stance is a claim slot. |
| Consequential new fact | Whichever layer first matches a pattern | Decision only | Narration created causes and the audit promoted one | Yes. |
| Bounded incidental | Improvisation promoter and, separately, incidental regex | Decision role INCIDENTAL_TEXTURE, then the incidental ledger | Turn 4 manner and NPC color missed both ledgers | Yes. One persistence consumer for accepted non-truth claims. |
| Negative evidence | Nobody; hedges suppress it | Decision, as a negative proposition or an epistemic limit | P10 emitted as texture | Yes. |
| Gameplay lead | Lead regex, suppressed by uncertainty | Decision, as `gameplay_lead` | P8 and P9 emitted with no row | Yes. |
| State mutation | Decision `permitted_state_mutations` | Decision | No illicit world mutation in this run | No. |
| Epistemic promotion | Not implemented | Decision, explicit establish act | Co-occurrence promoted P5 | Yes. |
| Temporal persistence | Post-seal `remember_temporal_claims` | Decision at acceptance; ledger is the store | Writer ignores speculation and NPC claims; auditor never reads the store | Yes. |
| Prose realization | Unrestricted generation | Narrator, constrained to the claim set | Created P3–P11 | Yes. |
| Proposition decomposition | Sentence splitter plus residuals | Claim constructor before prose | One claim per sentence, identity copied | Yes. Retire sentence-identity copy. |
| Final authorization | `classify_narrated_fact` taking `claims[0]` | Decision claim set | First covered row wins | Yes. |
| Final sealing | Immutable accepted response | Seal, of the authorized realization | Seal faithfully stored a wrong classification | No change to the seal. Change its input. |

## 19. Architecture option comparison

|  | Authority | Natural GM | Improvisation | Complexity | Tokens | Latency | Deterministic tests | Fits current pipeline | PR-BR salvage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Keep narration-first. Stronger decomposition and residuals. | Still fails when wording misses the list. Turn 3 is this option's next bug. | High, because prose stays free. | High | Looks small and becomes another pattern campaign. | Same | Same | Easy to turn green without predicting live prose. | Highest | Low. Repeats the cycle that just failed. |
| B. Decision-owned claim set. Narration realizes it. Inference is accepted before prose. | Matches the module's stated rule. Stops co-occurrence promotion. | High if realization may phrase accepted claims freely, including generic damage hypotheses. | High for texture and accepted NPC claims. Closed for new causes, leads, and absences. | Moderate. One claim object, one authorization read of the ledger, realization check. | One call if claims ride with narration. Retry only when a candidate is outside the set. | Close to today | High. Tests construct slot records and saved sentences. | Contract, decision, seal, and mutation gates stay. | High. |
| C. One model call returns `claims[]` and narration. Validate claims, then prose against the accepted set. | Strong when the claim channel is complete. Weak if prose can smuggle a slot the channel omitted. | High | High | Moderate, plus a correspondence rule for smuggling. | Higher output tokens. Same round trips in the success case. | Close to today | High for the claim channel. The smuggle check still needs the coverage rule. | Fits as the realization format for option B. | High, as the mechanism inside B, not as a second architecture. |
| D. Two-stage proposal, then prose. | Strongest separation. | High | High | Highest operational cost. | About double on infer turns. | Extra completion | High | Adds a call the current turn loop does not have. | Medium. Use only if one-call structured claims prove unable to reject candidates before seal. |
| E. Apply the existing extra-proposition rule to identity matches, and stop treating uncertainty as "do not account". | Fixes this Turn 3 sentence and P10's disappearance. | Unchanged | Unchanged | Small | Same | Same | A saved-sentence test would go red immediately. | Local edit inside the auditor | Partial. Necessary compatibility fallback. Insufficient, because narration would still create the proposition and the ledger would still not own it. |

Option A of this section is the reconstruction path. It is the limit the live run hit. Option B is the salvage. Option C is how B should call the model. Option D waits. Option E is the fallback that stops a matched identity from swallowing a second proposition while B is built.

## 20. Salvageability

KEEP

- Resolution Contract as the place that names the requested operation, subject, and epistemic act. Turn 3's confidence binding worked.
- GMResolutionDecision as the authority record for observations, mutations, unresolved slots, and, after this change, the consequential claim set.
- Provenance labels (`authored_world_fact`, `gm_inference`, `player_hypothesis`, `npc_claim`, `speculation`, `generated_proposal`).
- Temporal ledger buckets and the rule that writing a hypothesis does not rewrite it into world truth.
- C18 sealing and exact sealed/emitted equality.
- State-mutation authorization.
- The incidental-versus-consequential distinction as a ceiling.
- NPC epistemic distinction (`claim_only` versus `world_truth`).
- Semantic identity as a slot record for authored facts.
- Preservation's ability to drop a sentence the audit actually rejected. Turn 1 dropped the great-force sentence.

MODIFY

- Contract fast path, so interpretation survives "what does this damage suggest?" and a hypothetical actor question inherits the active claim. Local. Do not bury it inside the claim redesign.
- Decision builder, so `INFER` creates claim objects rather than a permission flag, and so authorization reads the temporal ledger.
- `NarratedClaim`, from a sentence annotation into a slot claim created before prose. Sentence text becomes realization text.
- `audit_narrated_claims` / `classify_narrated_fact`, so identity coverage cannot set the sentence's provenance. Residuals become the fallback for slots missing from the structured channel.
- `remember_temporal_claims`, so accepted inferences, hypotheses, NPC claims, and incidentals each have one bucket, and speculation is not a silent discard.
- `epistemic_frame` and the uncertainty exemptions, so low certainty does not mean low consequence or "skip this sentence".
- Lead and absence handling, as claim roles.
- Turn 2 interlocutor and place canonicalization, on its own track.

RETIRE

- Copying the first matching semantic identity onto the entire sentence (`_claim_from_row` as used now).
- The rule that an uncertain frame produces no residual and no ledger row.
- Using `_HEDGE_RE` token `around` as epistemic status.
- Treating "no NarratedClaim" as "safe to emit".
- Expanding `_CAUSAL_RELATION_RE`, `_EVIDENTIAL_RELATION_RE`, and `_GENERATED_LEAD_RE` as the remedy for the next live paraphrase.

## 21. Minimum next implementation boundary

One slice: the decision owns a consequential claim set before narration, and sentence coverage cannot grant world truth.

Abstraction: `RealizationClaim` as specified in section 8, stored on the GM Resolution Decision.

Responsibility: the decision accepts every consequential claim. Narration realizes the set. The auditor rejects a realization that adds a cause, actor, time, absence, witness, or lead slot the set does not contain. The temporal ledger is read during acceptance and written from the accepted claims.

Inputs: Resolution Contract, authored semantic identities, epistemic acts, unresolved qualifiers, and the current temporal ledger.

Outputs: the ordered claim set; narration constraints that quote those claims; ledger rows for `gm_inference`, `player_hypothesis`, `npc_claim`, and accepted incidentals; a seal input whose authority is the claim set.

Pipeline position: after the contract exists, inside decision construction, before the generation prompt. Seal and C18 stay after generation. The ledger write stays at seal and now records the decision's claims, not whatever identity a sentence happened to match.

Compatibility fallback: `_empty_identity_covers`'s rule that extra propositional content does not inherit a fact. Apply it to identity-bearing matches. Residual detectors remain a backstop for a structured channel that omitted a slot. They are not the authority source. `_claim_from_row` may still attach an observation identity to the span that states the observation. It may not attach that identity to a larger sentence that also states a cause.

Deterministic tests, with no model call, using the saved Turn 3 decision and sentence:

- The causal sentence is not `authored_world_fact` / `world_truth` / `established`.
- A decision claim `{relation: cause, modality: unresolved}` plus an observation claim does not become a likely cause when the realization says "seems a likely cause".
- An accepted `{modality: possible, provenance: gm_inference}` row is written to `gm_inferences` and is still `gm_inference` after the same wording is narrated again beside the observation.
- A stored `player_hypothesis` with the same cause slot blocks promotion.
- "No hint of recent disturbance" is an absence claim or a rejection, and `around` does not classify it as a hedge.
- "Recent users or nearby witnesses" is an unauthorized lead claim.
- Turn 4's soap and folding preference, given a `claim_only` NPC claim, appear in the NPC-claim store.

Live success criteria for a later cycle, not this one:

- A confidence answer may say the cause is unknown.
- If it offers a cause, that cause is a `gm_inference` or a player hypothesis, never authored world truth.
- Repeating or paraphrasing it inside an observation sentence does not promote it.
- `gm_inferences` is non-empty exactly when a cause alternative was accepted.
- No new domain phrase list is required for the saved Turn 3 wording to fail closed.

## 22. Risks and tradeoffs

- Realization can become stiff if INCIDENTAL_TEXTURE is too small. Turn 4 shows the product goal includes ordinary NPC color. The claim set should obligate consequential slots and leave manner free.
- A structured channel can be lied to. The model can narrate a cause and omit the slot. The coverage fallback must fail closed on extra cause, actor, time, absence, and lead material. That fallback must stay slot-based.
- Deterministic generic inferences ("more than one explanation fits") may sound thin until realization phrases them. That is acceptable. Specific invented history is not required for a competent answer.
- Reading the ledger before authorization can over-block a later genuine discovery. Promotion has to remain possible through an explicit establish act, or a real clue can never become true.
- Fixing Turn 2 inside this slice will hide whether claim ownership actually changed. Keep routing on a separate change.
- One-call structured output increases output tokens and can fail schema validation. The existing retry path can carry that failure. A second semantic stage is the expensive alternative, not the starting point.
- Tests that only add the live sentence to a regex will go green and miss the next paraphrase. The slice's tests should assert slot authority on the saved sentence without teaching a new phrase.

## 23. Exact model and API call count

This reassessment: 0 gameplay turns, 0 generation calls, 0 retry calls, 0 interpretation calls, 0 preflight calls, 0 other model calls, 0 total.

The live run under review, unchanged by this cycle:

| Call class | Count |
| --- | ---: |
| Gameplay turns | 4 |
| Initial generation | 4 |
| Retry generation | 2 |
| Interpretation | 0 |
| Preflight | 1 |
| Other | 0 |
| Total model/API calls | 7 |

## 24. Recommendation

Keep the Resolution Contract, the GM Resolution Decision, the temporal ledger, mutation authorization, and C18 sealing. Stop using them as a reconstruction pipeline.

The next implementation slice is section 21. It makes the decision the owner of every consequential claim before narration, including inferences, hypotheses, absences, and leads. Narration realizes that set. Identity overlap with an observation no longer authorizes a cause in the same sentence. A new inference is stored as `gm_inference` and cannot be promoted by being said again.

Do not add a regex for "likely cause". Do not start PR-BS. Do not run the 4x10 gate. Repair Turn 2's addressee binding separately, as routing.

A.
CURRENT ARCHITECTURE IS SALVAGEABLE BY MAKING THE
GM RESOLUTION DECISION OWN THE COMPLETE CONSEQUENTIAL CLAIM SET
BEFORE NARRATION
