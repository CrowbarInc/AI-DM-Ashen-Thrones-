# PR-BR architectural review

Proposition-level narration authority and temporal provenance.

Cycle: architectural review and discovery only. Production behavior was not changed. No gameplay or model calls were made. Evidence is the completed multi-turn run `artifacts/pr_br_multiturn_provenance/20261003T223147Z` (8 gameplay turns, 15 model/API calls, 4 PASS / 4 FAIL) and the current classifier, preservation, and persistence code.

# 1. Executive conclusion

The pre-narration architecture is doing the work it was built to do. `GMResolutionDecision` listed only the four authored observations on every Sequence A turn. NPC testimony stayed `npc_claim` / `claim_only`. Movement, departure, and destination provenance stayed distinct. A footprint sentence was rejected before emission. The world file did not grow a kiln, a faction, or a procedure.

The failure is downstream of that decision. Authority is applied to a **sentence**, and a sentence is accepted when it **contains** one licensed subject and one licensed value. Extra propositions in that sentence are not represented. They inherit the matched fact, or they are invisible.

That is enough to recreate the A2 → A3 → A4 chain in any domain. Matching "the bridge is cracked" will authorize "the cracked bridge shows saboteurs cut it last night" by the same path that authorized "the split jar indicates it was left unfired."

The architecture is salvageable. The change is to stop treating a matched sentence as the authorized fact, and to control **claim units** inside the sentence. `GMResolutionDecision`, the Resolution Contract, source provenance, NPC claims, movement reconciliation, retry context, and the immutable accepted-response boundary stay.

Semantic identity is the right shape for one claim. It is not a representation of several claims in one sentence. Reconciling the existing identity without a multi-claim record will not stop the chain.

# 2. Exact A2 → A3 → A4 causal chain

Authored state before A1, and still the scene file after A4:

- water jar condition = split
- clay inside the jar = dried flakes
- coil-pots condition = intact
- shed door condition = open

The scene summary says the shed holds unfired pots. That sentence is not a cause of this jar, and it does not name a kiln. It did not license the A2 or A4 additions. The audit stamp came from identity match, not from that summary word.

## A2

Player: "What does the split and the dried clay suggest happened?"

Decision `rc_4cfb4282d3af`: outcome `established_or_retrieved`. Proposed facts are the four observations. `unresolved_qualifiers` is empty. The question did not open a cause slot. `_QUESTION_CAUSE_RE` matches "why", "what caused", "what happened", and "what befell". "Suggest happened" does not match.

Initial generation, three sentences plus a lead:

1. "The large water jar's clean split and the clay inside, dried into pale flakes, indicate it was left unfired and has dried out over time."
2. "The unfired clay failed to hold moisture and crumbled, pointing to a disruption in the usual pot-making process rather than deliberate damage."
3. "Meanwhile, the stack of unused coil-pots remains intact, and the shed door stands open to the yard."
4. Lead: inspecting other objects might reveal details others have overlooked.

Audit of the accepted text (`decision_acceptance_why`: `bounded_sentence_preservation`):

- Sentence 1 is `authored_world_fact` / `world_truth` / `scene.visible_facts.0`. Its copied `semantic_identity` is `water_jar` / condition / `split`.
- Sentence 3 is `authored_world_fact` / `world_truth` / `scene.visible_facts.2`, identity `coil_pots` / `intact`.
- Sentence 2 is absent from `proposed_facts` and absent from `violations`. `classify_narrated_fact` returned no record. Preservation keeps sentences that are not violations, so sentence 2 was emitted with no authority label at all.
- Sentence 4 is `generated_proposal` / `unsupported_narrator_lead` and was dropped.

The retry was empty (`malformed_or_truncated`). Preservation therefore sealed the initial text minus the lead. Scene JSON did not change. The causal sentences entered the next prompt as ordinary `P: … | G: …` history. Discourse `active_claim` stayed null.

## A3

Player: "If it was left unfired and just dried out, who would have had the chance to leave it that way?"

The conditional is a player hypothesis. The contract subject became `split water jar`. Epistemic mode was `unknown_allowed`. The decision still authorized only the four observations. `unresolved_qualifiers` was `["actor"]` because the question contains "who". Cause was not opened. The presupposed leaving was not stored as a hypothesis.

Emitted answer: nothing present confirms who had the chance to leave the water jar unfired. Actor and time are withheld. The leaving is the event being asked about. No culprit was invented. The hypothesis was still not written to the scene file. It was spoken as the event, and the next prompt received that wording unlabeled.

## A4

Player: "Is the jar having been left unfired something we know, or only a possibility?"

The interpreter proposed a clarification of known versus hypothesis. The committed contract was `perceive`. The decision again authorized only the four observations. `unresolved_qualifiers` was empty. A3's open actor slot was not carried. The known-versus-possible distinction was not a decision field.

Initial generation:

1. Jar is split, clay dried into pale flakes. Audited `authored_world_fact` / `world_truth`, identity `water_jar` / `split`.
2. Coil-pots intact, "showing no signs of firing." Audited `authored_world_fact` / `world_truth`, identity `coil_pots` / `intact`. The firing observation inherited the intact-pots fact.
3. "The jar's condition makes it clear it was never fired in a kiln but left to dry naturally." Not in the accepted audit's `proposed_facts` and not in `violations`. Same invisible-sentence path as A2 sentence 2. Emitted.
4. "However, nothing here reveals whether that was intentional or accidental, nor who might have left it that way." `unsupported_narrator_lead`. Dropped.

The retry restated the four authored sentences, then "The shed offers no clear sign of why the jar was left unfired." That hedge also failed as `unsupported_narrator_lead`. Preservation of the initial generation kept sentences 1–3 and deleted sentence 4.

Acceptance: `bounded_sentence_preservation`. Scene visible facts after A4 are still the original four. No kiln proposition was stored. The player was told the kiln reading is clear.

## Why the chain is one defect

A2 put an inference into player-facing history and stamped the sentence that carried it as the authored split. A3 had no hypothesis record, so the only open slot was the actor the player asked for. A4's certainty used the same sentence rule, and preservation deleted the sentence that still sounded uncertain. Each turn consumed the previous turn's prose, not a provenance record.

# 3. Current authority-unit map

| Stage | Unit it actually uses |
| --- | --- |
| `GMProposedFact` | One authorized or unauthorized fact. `semantic_identity` is one subject, one relation, one value, one polarity, optional qualifiers. |
| Authored fact rows | One identity per `visible_facts` entry. Built in `_authored_fact_rows` before narration. |
| Generated sentence | `_sentences` splits on `.!?`. That string is the audit unit. |
| `classify_narrated_fact` | One `GMProposedFact` or `None` per sentence. |
| `_semantic_identity_matches` | True when the sentence contains the identity's subject terms and value terms, polarity agrees, and the small overreach list is empty. |
| `_authorized_by_decision` | Returns the **first** authorized row whose identity matches. Later facts are not consulted. |
| Overreach | `_semantic_overreach_reasons` catches a closed set of strengthenings (`damaged`→`collapsed`, `tainted`→`poisoned`, `locked`/`unlocked`) and a closed causality list (`because`, `caused by`, `after thieves`, `thieves broke`, `ordered by`, `discovering a hidden`). |
| `unsupported_narrator_lead` | A hedged sentence with an ungrounded definite noun, checked **before** the identity match. |
| Decision audit | `audit_narration_against_decision` collects one fact per sentence. `None` is omitted. |
| Immutable validation | A sentence is a violation only when the returned fact has `authorized` false. |
| Bounded preservation | `sentences_without_decision_violations` deletes violation sentences and keeps every other sentence, including unclassified ones and mixed ones. |
| Accepted narration | Sealed text. Provenance `initial_generation` or `regeneration`. |
| Next-turn prompt | `prompt_context._assemble_conversational_memory_candidates` stores `P: {player} \| G: {snippet}` with no authority tag. |

Answers:

1. Authority is attached to the **sentence**, by copying one **semantic identity**. It is not attached to a token span, a clause, or the whole reply. The reply is only a sequence of sentence verdicts. Clause splitting (`_clauses`) is used for negation scope, not for authority.

2. Multiple propositions in one sentence are **not represented**. The sentence is either the first matching identity, an unauthorized proposal, incidental texture, an NPC claim, or nothing.

3. A sentence cannot currently be partly authorized and partly unauthorized. The returned object has one `authorized` flag, one `authority`, and one `semantic_identity`.

4. Information is lost in `_authorized_by_decision` when the first match returns, and again when `classify_narrated_fact` returns `None`. Match is a subset test: licensed terms must be present. Unlicensed terms do not have to be absent. Qualifiers are required only when the identity already has them. Extra cause, actor, time, or certainty in the sentence is ignored unless a separate regex happens to fire.

5. The final all-or-nothing classification is `classify_narrated_fact`. The branch that stamps world truth is the early return after `_authorized_by_decision` (it copies the matched row's provenance, authority, persistence, and identity onto the whole sentence). The branch that makes a sentence invisible is the final `return None`.

# 4. A2 proposition decomposition

Sentence 1. "The large water jar's clean split and the clay inside, dried into pale flakes, indicate it was left unfired and has dried out over time."

| Id | Subject | Relation | Value | Polarity | Qualifier | Epistemic modality | Causal / evidential | Provenance in fact | Authorized by decision | Inferred | Unsupported | Consequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | water jar | condition | split | positive | "clean" is manner | observed | none | authored | yes | no | no | the observation is already consequential and licensed |
| P2 | jar clay | condition | dried flakes | positive | "pale" is manner | observed | none | authored | yes | no | no | licensed observation |
| P3 | water jar | process history | left unfired | positive | none | stated as fact | none by itself | not authored | no | yes | yes | yes: a new historical process fact |
| P4 | jar clay | condition over time | dried out over time | positive | time = over time | stated as fact | drying is the result of P3 | drying is authored; "over time" and the causal link are not | partial | yes | the time and the link are unsupported | the link is consequential |
| P5 | P1+P2 | evidential | establish P3 and P4 | positive | "indicate" | certain inference presented as reading the object | evidential | not authored | no | yes | yes | yes: the observations are said to prove the history |

What the classifier did: subject alias "jar" and value alias "split" are both in the sentence. Polarity is positive. No qualifier was required. `_semantic_overreach_reasons` does not treat "indicate" as causality. First match wins, so the sentence becomes `water_jar` / `split` / `world_truth`. P2 is not even the identity that was copied. P3, P4's extra time, and P5 are discarded.

Sentence 2. "The unfired clay failed to hold moisture and crumbled, pointing to a disruption in the usual pot-making process rather than deliberate damage."

| Id | Subject | Relation | Value | Polarity | Qualifier | Modality | Relation kind | Authorized | Inferred | Unsupported | Consequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P6 | jar clay | mechanism | failed to hold moisture and crumbled | positive | none | stated as fact | causal mechanism | no | yes | yes | yes |
| P7 | pot-making | status | disruption of the usual process | positive | "usual" | stated as fact | evidential ("pointing to") | no | yes | yes | yes |
| P8 | damage | manner | not deliberate | negative | actor intent | stated as fact | contrastive cause | no | yes | yes | yes |

"Clay" is a subject alias of `jar_clay`, but the value aliases (`dried`, `pale flakes`) are not in this sentence, so identity match fails. The proposition-authority families (schedule, access, levy, legal, consequential role) do not match. The stateful-assertion regex does not match "failed". Result: `None`. Preservation kept P6–P8 because they were not violations.

Sentence 3 is two licensed observations joined by "and" (coil-pots intact, door open). That sentence is a fair realization of two authorized facts. The inherited label is still one identity (`coil_pots`), which is sloppy and harmless here.

# 5. A4 proposition decomposition

Sentence 1 restates P1 and P2 with manner words ("cleanly", "fragile", "pale"). Those manner words are bounded incidental. The sentence was labeled the split fact. No new cause.

Sentence 2. "Nearby, a neat stack of unused coil-pots remains intact on the lower shelf, their surfaces unbroken and showing no signs of firing."

| Id | Subject | Relation | Value | Polarity | Qualifier | Modality | Relation kind | Authorized | Inferred | Unsupported | Consequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 | coil-pots | condition | intact | positive | unused, lower shelf, neat | observed | observation | yes | no | no | licensed |
| Q2 | coil-pots | surface | unbroken | positive | none | observed | observation | yes as a paraphrase of intact | no | no | licensed paraphrase |
| Q3 | coil-pots | firing evidence | no signs of firing | negative | "nearby" as corroboration of the jar | observed, certain | evidential support for the unfired reading | no | yes | yes | yes: a new negative observation used as evidence |

Classifier: "pots" and "intact" match. "Firing" is not an overreach term. The whole sentence inherits `coil_pots` / `intact` / `world_truth`. Q3 is the corroboration that makes the later kiln sentence feel earned.

Sentence 3. "The jar's condition makes it clear it was never fired in a kiln but left to dry naturally."

| Id | Subject | Relation | Value | Polarity | Qualifier | Modality | Relation kind | Authorized | Inferred | Unsupported | Consequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q4 | water jar | process history | never fired | negative | instrument = kiln | certain ("makes it clear") | evidential | no | yes | yes | yes |
| Q5 | water jar | process history | left to dry naturally | positive | none | certain | causal alternative | no | yes | yes | yes |
| Q6 | jar condition | evidential | establishes Q4 and Q5 | positive | certainty upgraded from A2's "indicate" | known, not possible | evidential | no | yes | yes | yes: this is the status the player asked about |

"Jar" matches the subject. "Split" does not appear, so `_sentence_targets_identity` is false and the match path is skipped. "Makes it clear" is not in the causality regex. Proposition families do not match, so the default epistemic frame `world_truth` plus family `none` is skipped by `classify_propositions` (`family == none` and not hearsay). `classify_narrated_fact` returns `None`. Q4–Q6 are emitted unlabeled.

Sentence 4, the rejected hedge:

| Id | Subject | Relation | Value | Modality | What it was |
| --- | --- | --- | --- | --- | --- |
| Q7 | leaving | intent | intentional or accidental | unresolved | the correct status answer |
| Q8 | leaving | actor | who | unresolved | the A3 open slot |

"Might" trips `_UNCERTAIN_FRAME_RE`. "Intentional" is an ungrounded definite relative to the decision ground. `_UNKNOWN_SLOT_RE` does not match "nothing here reveals whether". The hedge dies as `unsupported_narrator_lead` before any identity match. The certainty sentence has no hedge word, so that check never looks at it.

# 6. Authorized-core / residual-claim analysis

The candidate principle holds:

Matching an authorized proposition does not authorize the sentence.

A generated sentence has two products:

- **Authorized proposition coverage.** Which decision identities are realized, and only those predicates.
- **Residual claim content.** Every other proposition, including evidential and causal links between covered propositions.

The validator asks both questions. Coverage without a residual check is the current bug.

This can be made deterministic enough for the product without general English NLI, if the product does not ask a parser to recover every predicate from prose.

What is deterministic today, and should stay deterministic:

- Whether a licensed identity's subject and value occur, with polarity. That is coverage, not entailment.
- Whether the decision authorized a cause, an actor, a time, or a certainty qualifier. Those slots already exist and were empty on A2 and A4.
- Whether a sentence is hedged, quoted, or an explicit non-assertion. Those frames already exist.

What is not deterministic from prose alone:

- The exact residual proposition in "indicate it was left unfired" versus "saboteurs cut it overnight" versus "the clay looks pale in the yard light." A token-subtraction pass cannot tell a manner adjective from a new historical fact without either a domain list or a claim the generator was required to declare.

So the residual check should not be an NLI model, and it should not be a pottery list. It should be a **closed claim record**. Prose is allowed to realize claims that are already on that record. A consequential proposition that is not on the record is residual even if the sentence also realizes a licensed fact. Incidental manner can remain a small, domain-general texture class (sensory and manner), which already exists and worked on A1 and B1.

A verb list of "shows that / proves / because" can mark that a relation kind is present. It cannot be the authority model. A2 and A4 would have been caught by such a list. "Saboteurs cut the cable overnight" would not. The list is a backstop signal. The authority decision is whether a claim unit is licensed.

# 7. Minimum proposition representation

Slice 3's semantic identity should be **extended and repeated**, not replaced.

It already has subject, relation, value, polarity, qualifiers, epistemic status, and provenance. Those fields describe one claim well. The missing concept is **more than one claim unit for one narrated sentence**, plus two fields the failure actually used:

- `relation_kind`: `observation`, `evidential`, `causal`, or `incidental`
- `epistemic_status` on the **narrated** claim, not only on NPC claims: `observed`, `inferred`, `plausible`, `hypothetical`, `unresolved`, `established`

Candidate units:

| Unit | What it buys | Complexity | Robustness |
| --- | --- | --- | --- |
| A. Clause-level claims | Separates "the pots are intact, but they show no firing." | Low. `_clauses` exists. | Misses A2 sentence 1 and A4 sentence 3. The inference is inside one clause. |
| B. Proposition spans inside the sentence | Could mark the complement of "indicate". | A parser or a span model. | Approaches NLI. Not the minimum. |
| C. Decision-provided realization slots | Narration may only realize listed identities, plus incidental texture. | Low, and mostly present. | Stops the chain if extra predicates are rejected. Too blunt if every extra word is rejected. Does not by itself let the GM offer a useful hypothesis. |
| D. Generated structured claims paired with surface narration | The consequential claims are data. Prose realizes them. | One new record and a validator that refuses undeclared consequential claims. | Best fit. The model can still hide a claim in prose, so a residual backstop remains, but the backstop no longer has to understand the claim. It only has to notice that the prose is not exhausted by the declared claims and the incidental class. |
| E. A larger single identity schema | More fields on the one matched fact. | Looks small. | Does not represent two propositions. Rejected. |

Recommendation: D, with each claim stored in the existing identity shape. C is the licensed subset of D and already lives on `GMResolutionDecision.proposed_facts`. A is a useful split for preservation, not the authority unit.

# 8. Generation-first vs classification-first

## Option A — post-hoc proposition decomposition

The model writes prose. A deterministic decomposer turns prose into claims. Each claim is checked against the decision.

This is not reliable enough without general NLI or a domain lexicon. The current overreach list is this option in miniature, and it missed "indicate", "pointing to", "makes it clear", "no signs of firing", and "never fired". Growing that list with kiln words, then sabotage words, then poison words, is the approach this review is forbidden to take. A decomposer that only fires on a closed grammatical frame will miss actor-and-time add-ons that use ordinary verbs.

Use post-hoc checks as a backstop. Do not make them the parser of record.

## Option B — structured claims before surface realization

`GMResolutionDecision` → narration claims → surface narration. The validator checks that the surface did not materially exceed the claims.

This does not remove the semantic-fidelity problem. It moves the consequential part to a place where fidelity is a subset check: every world-truth claim must equal a decision identity, and prose that adds a consequential claim without declaring it fails closed. Incidental wording can still vary. That is a material constraint, not a rename. The remaining risk is undeclared prose, which the backstop covers by refusing to treat an unmatched sentence as authorized.

## Option C — decision-owned proposition budget

The decision lists authorized slots and a bounded incidental allowance. Consequential residuals are rejected.

This preserves natural GM prose for observation and incidental color. It does not preserve a useful inference unless the budget contains an explicit inference slot that is allowed to be spoken and forbidden to be stored as world truth. A2's player asked what the evidence suggests. A competent GM may answer with a possibility. A budget that only says "repeat the four facts" is safe and slightly dead. A budget that also says "you may mark one inference as possible" is enough, provided the inference cannot inherit `world_truth`.

## Option D — hybrid

Structured consequential claims are controlled. Incidental prose stays free. Post-hoc checks look only for consequential residual claims, not for every adjective.

This fits the existing taxonomy: authoritative fact, bounded incidental fact, consequential new fact, plus NPC claim. It is the recommended shape. See section 22.

# 9. Causal and evidential relation analysis

Two licensed observations do not license a link between them.

Authorized: door is open; vase is broken. Unauthorized: the open door explains the broken vase.

The relation is its own claim:

- subject: the pair, or the evidence proposition
- relation: `explains` / `shows` / `caused_by`
- value: the other proposition
- `relation_kind`: `evidential` or `causal`
- `epistemic_status`: `inferred` unless a decision fact has `causal_authorized`

`causal_authorized` already exists on the identity and defaults to false. Nothing in Sequence A set it. The overreach check ignores that flag unless the sentence contains the closed causality list. "Indicate", "pointing to", and "makes it clear" are evidential relations. They were treated as flavor on the observation.

The authority model distinguishes three acts:

| Act | What is true | Example that should be allowed | What must not happen |
| --- | --- | --- | --- |
| Observation | A licensed predicate holds | "The jar is split and the flakes are dry." | Adding a history of how it got that way. |
| Inference | A link or explanation is being offered | "One reading is that it was never fired. That is not established." | Storing or restating the reading as world truth. |
| Established causal relationship | A decision or authored fact says the link is known | Only when `causal_authorized` is true on a proposed fact | Narration inventing the link because the tone is confident. |

Do not encode this as a blacklist of pottery, sabotage, or poison. The relation kind is a field. A small set of domain-general frames may **raise** a sentence into "has a relation kind" so the backstop looks at it. The frame list does not decide truth, and it is not sufficient on its own.

# 10. Epistemic-modality analysis

The system already has words for this on NPC claims: rumor, hearsay, uncertain, speculative, and `claim_only`. Narrator sentences collapse to `world_truth` unless a hedge regex fires, and a hedge often becomes `unsupported_narrator_lead` instead of an authorized uncertain statement.

Epistemic status has to live on the **claim unit**, and the decision has to say which statuses this turn may speak.

| Status | Meaning | A2 / A3 / A4 |
| --- | --- | --- |
| known / established | Decision or authored fact | The four observations only |
| observed | Realization of an established perceptible fact | A1, and the split/flakes/intact/open clauses later |
| inferred | GM reading, not world truth | A2's unfired reading should have been this |
| plausible | Weaker inference the player can use | Acceptable spoken form of A2 |
| suspected | Attributed suspicion | Not this scene |
| rumored / hearsay | NPC claim | Sequence B's cask. Already works |
| hypothetical / conditional | Player or GM has not asserted it | A3's "if it was left unfired" |
| unresolved | Asked slot has no authorized filler | A3 actor; A4 known-versus-possible |

A2 should have been: observation = authoritative; never-fired explanation = inference. Not: sentence = world truth.

A3 player repetition stays a player hypothesis until something other than repetition establishes it.

A4 should be allowed to say "that is only a possibility" without `unsupported_narrator_lead`. That sentence is the authorized answer to a status question when the stored status is inference. The check should not treat an open epistemic slot as an ungrounded lead.

`epistemic_frame` in `proposition_authority.py` returns `world_truth` whenever the hedge list misses. That default is safe only for sentences that have already been reduced to licensed claims. It is not safe as the status of a raw sentence.

# 11. Player-presupposition analysis

1. Transcript text supplied to generation does **not** carry an authority or provenance annotation. The memory candidate is `P: {player_input} | G: {player_facing_text}`, truncated, kind `recent_turn`.

2. The model cannot reliably separate previous GM observation, previous GM inference, NPC rumor, and player hypothesis from that string. NPC claims have a separate discourse slot (`active_claim.epistemic_status`), and Sequence B showed that slot works. Sequence A never wrote an `active_claim`, because the inference was not an NPC claim.

3. For narrator prose, prior text is undifferentiated conversational history.

4. That contributed directly to A3 and A4. A3's prompt contained A2's "indicate it was left unfired" as GM text. The contract opened an actor slot and treated the leaving as the event under discussion. A4's prompt contained both A2 and A3. The generation answered the status question by strengthening the unlabeled history. The decision still knew only the four facts, and the generator was not shown a record that said the unfired reading was an inference.

Minimum mechanism: a player repetition of X does not imply the world established X.

- When the player's utterance presupposes a proposition that is not a licensed identity, store a `player_hypothesis` claim. Do not open only the wh-word slot.
- The next decision and the next prompt see that claim marked hypothesis.
- Validation does not treat the hypothesis, or the GM's earlier inference, as coverage for a new world-truth sentence.
- Repetition by the player, the GM, or an NPC does not promote it. Promotion requires a later decision that authorizes that identity as an established fact.

# 12. Temporal provenance analysis

A full transcript database would duplicate the session log and would not fix authority. The session log is why the inference survived. What is missing is a **small typed record** the next decision can read.

| Record | Persist? | How long? | Generation sees it? | Validation sees it? | Can it be promoted? | What promotes it? | Can repetition promote it? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Accepted authoritative proposition | Already persists in scene, world, or resolver state. Do not copy it into a second transcript. | As long as that state exists | Yes, as decision facts, which already happens | Yes | Already authoritative | Authored content or a permitted mutation | No |
| B. Accepted bounded incidental proposition | Yes. It does not persist today except as raw prose. | Scene scope, or until contradicted by a later authorized fact. Cap the list. | Yes, labeled incidental | Yes, as coverage for the same incidental claim only | No, not to world truth | A later authored fact or explicit decision may replace it; it does not upgrade in place | No |
| C. NPC claim | Yes. Discourse `active_claim` plus the claim ledger already do this. | Until retracted or the campaign drops the claim. Scene id stays the scene of utterance, as B3/B4 did. | Yes, labeled hearsay | Yes | Only by a decision that independently establishes the content | Not the claim's repetition | No. B3/B4 confirmed this. |
| D. Player hypothesis | Yes. Not stored today. | While the question is open, scene-scoped, capped | Yes, labeled hypothesis | Yes, so presupposition is visible | Only by an explicit establish act | Decision, not the player's next sentence | No |
| E. GM inference | Yes. This is the A2 gap. | Scene-scoped, capped, until established or dropped | Yes, labeled inference, with the instruction that it is not a fact | Yes, so a later certain restatement is a status upgrade, not coverage | Only by an explicit establish act on a later decision | Resolver or authored fact, never narration confidence | No |
| F. Rejected consequential proposal | Yes. Decision-audit rejections are not written to `bounded_improvisation.rejected` today. That bucket only receives improvisation proposals the proposal pipeline rejected. | See section 13 | Yes, as negative guidance | Yes | Yes, later, if a decision authorizes that identity | An authorized decision fact with the same identity | No |

Generation seeing a record means a typed line in the prompt, not a hope that the model will notice the old wording was cautious. Validation seeing it means the coverage set and the forbidden-upgrade set, not a search of the transcript.

# 13. Rejected-proposal memory

B4 correctly rejected "recent footprints" (`physical_investigative_evidence`). The rejected sentence was not stored. A later generation can propose the same footprints. The cycle did not run that later turn, so this is a structural gap, not a second observed recurrence.

Negative memory should store the **claim identity** of a rejected consequential proposal (subject, relation, value, polarity, salient qualifiers), plus the reason and the scene. It should not store a permanent ban on the English sentence.

Semantics:

- While the negative record is live, validation rejects a world-truth realization of that identity, including a paraphrase that matches the same identity. Wording match alone is too weak; identity match is the same tool already used for licensed facts.
- Generation is told the proposition was rejected and may not be stated as fact.
- The record expires when the scene changes if it was scene-local evidence, and in any case after a fixed turn window so a cap cannot become a permanent canon of negatives. The existing rejected bucket already caps at 50; a similar cap belongs here.
- Expiration does not establish the fact. It only stops blocking it.
- A later `GMResolutionDecision` that authorizes the same identity overrides the negative record. That is the legitimate path: the footprints become true because a resolver or an authored fact says so, not because they were narrated again.
- An NPC may still report the rejected content as hearsay. Hearsay does not clear the negative record and does not create world truth.
- Player or GM repetition does not clear it.

B4's softer accepted line, "no obvious signs of disturbance", was not a violation. Negative memory should not be so broad that it bans every negative observation about the ground. Store the rejected identity (recent footprints / undisturbed for some time as investigative evidence), not every sentence that shares the word "disturbance", unless that sentence is the same consequential identity.

# 14. Incidental-persistence analysis

B1 improvised mundane detail: the work was going steadily, the wall bundles were cut from the osier rack, the weather held, and Linden offered to show where he gathers rush. Those lines were not written as bounded-improvisation entries. They survived because the transcript stayed in later prompts. The ledger was empty after all eight turns.

That is fragile in both directions. If a later prompt window drops the snippet, the GM forgets a detail the player already heard. If the snippet is treated as ordinary history, a mundane line can be mistaken for a fact the way A2 was. B1 did not cause that second failure. The cask stayed hearsay. The risk is still real, because the only memory of the weather is unlabeled prose.

Accepted incidental facts should persist as incidental records:

- kind `bounded_incidental`
- authority `bounded_incidental`
- persistence `runtime_incidental`
- scene scope
- visible to the next decision as coverage for the same low-stakes claim
- not eligible for the world-truth match path
- not promoted by being repeated, thanked, or asked about

A3/A4 safety must not be implemented by stripping the transcript of everything the GM added. The player may refer to the weather, as B3 did. The system should still know that sentence was incidental.

`_runtime_fact_rows` already reloads accepted ledger entries onto the next decision. The missing step is writing the accepted incidental claims into that ledger. Narration that merely restates an authored fact should not create a second row.

# 15. Preservation-inversion analysis

A4's sealed text kept the kiln certainty and dropped "nothing here reveals whether that was intentional or accidental."

Exact order in `classify_narrated_fact`:

1. Slot-fill and answer-relation checks. A4's decision had no open qualifier and no answer relation, so they did not fire.
2. `_unsupported_narrator_lead` fired on the hedge because "might" is an uncertain frame and "intentional" is not in the decision ground.
3. Identity match then stamped the split sentence and the "no signs of firing" sentence as world truth.
4. The kiln sentence matched neither an identity nor a consequential family, returned `None`, and was not a violation.

`sentences_without_decision_violations` deletes only violation sentences. The re-check of the shortened text is `hard_valid` because the sentences that remain are either inherited facts or invisible. `seal_accepted_response` then commits that text. Retry context was present and did not save the turn: the retry's own hedge was rejected the same way, and preservation prefers the initial generation's non-violation sentences.

Answers:

1. Bounded preservation is sound once the classification unit is the claim. It is not sound while a mixed or unlabeled sentence counts as safe.

2. Sentence-level preservation is unsafe when a sentence contains an authorized predicate and an unauthorized consequential claim. Keeping the sentence keeps the unauthorized claim. That is what happened to A2 sentence 1 and A4 sentence 2.

3. Preservation should operate on claim-bearing units. A clause split is the practical cut when the unauthorized claim is in its own clause. It is not sufficient when the unauthorized claim shares a clause with the observation.

4. A mixed sentence (licensed content plus unauthorized consequential content) should be **removed**, not partly kept and not rewritten by a second prose pass inside the sealer. The turn may retry. If the retry still mixes them, the sealed fallback is the decision's authorized observations plus the open epistemic status, which `authorized_observation_line` already knows how to state for open actor/time/cause slots. Do not ask preservation to surgically delete "never fired in a kiln" out of a grammatical sentence.

5. C18's immutable-valid-response guarantee is maintained by sealing only a text that a claim-level re-audit accepts. The player still receives one accepted response. That response is either claim-valid narration or the authorized observation line. It is not a sentence the audit called world truth while a second proposition rode along, and it is not an empty failure.

# 16. Narration responsibility analysis

Narration's job is to realize an authorized fictional outcome. It is not a world-authoring stage. The current path still lets generated prose introduce consequential content, because classification either inherits a match or ignores the sentence.

| Introduction | Where it enters | Classification |
| --- | --- | --- |
| New causal or evidential relationship ("indicate", "pointing to", "makes it clear") | Narration sentence that also contains a licensed subject and value | Accidentally permitted. Inherited or unlabeled. |
| New consequential attribute ("never fired", "no signs of firing") | Same | Accidentally permitted. |
| New actor | Slot fill, when an actor slot is open and a proper name is the agent | Validator-controlled, and only if the slot was opened. A2 did not open it. |
| New time ("over time", "last night") | Qualifier on a sentence | Accidentally permitted unless `_TIME_FILL_RE` and an open time slot both fire. |
| New location / movement | Movement regex versus permitted mutations | Validator-controlled. B3 showed the permitted path. Unpermitted movement is rejected. |
| New certainty (possible → clear) | Epistemic upgrade with no stored prior status | Accidentally permitted. A4. |
| New evidence (footprints, "no signs of firing") | Consequential pattern list, or identity inheritance | Footprints are validator-controlled (`physical_investigative_evidence`). Corroboration that shares a licensed value is accidentally permitted. |
| Sensory and manner color | Incidental regex, or swallowed into the matched fact | Intentionally permitted as bounded incidental. A1 and B1. |
| NPC hearsay | Claim frame plus attribution | Validator-controlled and intentionally permitted as `claim_only`. B2–B4. |
| Destination facts after a resolved move | Decision reconciliation | Intentionally permitted. B3–B4. |
| Departure exit reused as a destination onward route | `_departure_exit_reuse_reasons` | Validator-controlled. Did not fire as a bug in this run. |

The constraint text already says "Inference must not be narrated as physical evidence." The classifier then files the inference as the physical evidence's identity. The constraint is not enforced at claim granularity.

# 17. Human-GM comparison

A competent GM, looking at a split jar and dried flakes, may do either of these:

- Establish: "The clay is dry and this jar was never fired." That is a new consequential fact. It is legal only when the table's world-authoring rules let the GM establish it on purpose.
- Infer: "It could have been left unfired. The condition alone does not prove that." The player can use the idea. The world has not adopted it.

A1 is the observation a human GM would give. A2 spoke the establish act and the audit filed it as the observation. A3 investigated the established event. A4, asked which act had been performed, repeated the establish act and deleted the infer act.

The explicit system decision that corresponds to that choice is an epistemic act on `GMResolutionDecision`, not a sentence tone:

- `establish` — the proposition is added to proposed facts with world-truth authority. Narration may state it as known. This is a GM decision, made before narration, under the same source rules as any other consequential fact.
- `infer` — the proposition is added as an inference claim. Narration may offer it as a possibility. Validation rejects a certain realization. It is not world truth.
- `leave_unresolved` — narration may say the slot is unknown. That speech is authorized. It is not an unsupported lead.

If the decision contains neither `establish` nor `infer` for a proposition, narration must not introduce it. Today the choice is "the narration happens to phrase it confidently, and the sentence also contains the word split." That is the misplaced boundary.

For A2's question ("what does this suggest?"), the default act is `infer`, not `establish`. For A4's question ("known or only a possibility?"), the authorized answer is the stored status of that inference. No new kiln fact is available to establish.

# 18. Fact-taxonomy reconciliation

Existing classes stay:

1. **Authoritative fact.** Source is authored state, resolver result, or an explicit establish act. Authority `world_truth`. Narration realizes it. Narration does not create it.

2. **Bounded incidental fact.** Low-stakes sensory, manner, and mundane continuity. Authority `bounded_incidental`. Persists as incidental. Cannot satisfy a world-truth match.

3. **Consequential new fact.** A new predicate, actor, time, place, mechanism, organization, or piece of evidence that would change what the player can treat as true. Unauthorized unless the decision established it. The unfired history, the kiln, "no signs of firing", and the footprints are this class.

Epistemic categories sit beside those classes. They are not a fourth world-truth type.

- NPC claim / rumor: already first-class. Persistence `claim_only`. Keep it.
- **GM inference must become a first-class provenance category.** It is not a consequential new fact.

The difference: a consequential new fact, once authorized, is true in the world. An inference is a stated reading. It can be useful on the next turn ("we are checking the unfired possibility") and still be false, incomplete, or abandoned. Promoting an inference is an establish act. Speaking it again is not.

A hypothesis is an inference whose source is the player, or a conditional the GM has not adopted. A3 should have created one. It should not have created an unresolved actor on an established event.

# 19. Mixed-intent secondary finding

B3 player text: "I thank Linden for telling me the weather held and that the carter's story is only something he heard, then I head out to the osier rack."

Travel committed. The decision recorded the location mutation, departure facts, and destination facts. The thanks, the weather, and the hearsay reminder were not spoken. `executable_obligations.supporting` was empty. This is secondary to the kiln chain.

The supporting-obligation repair **is on the production path**. `resolution_contract` writes `construction["executable_obligations"] = executable_obligations(text)` after the contract operation is chosen. B3's construction shows `commitment_status: executed_now` and an empty obligation record, so the function ran and returned empty.

It is not a failure to see the word "thank". `_social_act` matches `\bthank(?:s|ed|ing)?\b`.

It is lost during contract construction. `executable_obligations` returns the empty record when `_move_span` finds no travel. The social act is computed and then discarded by `if not move: return empty`. `_move_span` uses declared-travel patterns and `_RE_SCENE_TRAVEL_DESTINATION`. Those accept "head to" and "head off to". They do not accept "head out to". The travel resolver still bound the osier-rack exit by a wider destination path, so the move happened and the obligation record did not.

Classification: **C. Lost during contract construction**, because the obligation function's travel span is narrower than the resolver that actually moved the player. The thanks never reached the decision's narration constraints. Narration omission is the consequence, not a separate generator failure.

Do not treat this as a reason to redesign claims or movement. The next obligation slice, when it is scheduled, only has to record a recognized social act even when this travel-span helper misses, or teach that helper the same destination span the resolver already accepted. Not in the claim-control slice.

# 20. Components to preserve

Do not reopen these without new evidence from this run:

- Resolution Contract as the owner of what the player committed to do.
- `GMResolutionDecision` as the pre-narration authority record. It was present on all eight turns, and its contract id matched.
- Source and provenance authority: authored facts, resolver mutations, and NPC claims already have distinct provenance strings.
- NPC claim / `claim_only` / discourse `epistemic_status`. Player repetition did not promote Linden's cask.
- Movement reconciliation, including copying the location mutation onto the decision after the resolver runs.
- Departure versus destination scene roles. The chair and the rush bundles stayed behind. B4's decision facts were the destination.
- Retry context. A2, A3, A4, and B4 retries received the contract, the decision, and the failure.
- The immutable accepted-response boundary. One text is sealed. The fix is what may be sealed, not whether sealing exists.
- Bounded incidental authority as a class. A1's scent and B1's ordinary talk should remain legal.
- Footprint-style consequential rejection when a sentence is actually classified as consequential. B4's initial footprint sentence is the pattern to keep.
- The rule that scene JSON is not updated from narration. That safeguard held. It is not sufficient, because the player hears the narration.

Do not replace the decision architecture. The decision said the right facts. The sentence audit did not enforce them.

# 21. Architecture options

## Option 1 — Post-hoc residual classifier

```
player input
    -> Resolution Contract
    -> resolver
    -> GMResolutionDecision
    -> narration (free prose)
    -> sentence split
    -> coverage match against decision identities
    -> residual guess from whatever tokens and frames remain
    -> preservation of non-violation sentences
    -> emission
    -> transcript only
```

| Criterion | Assessment |
| --- | --- |
| Authority safety | Partial. Stops "indicate" and "makes it clear" if the frame list is wide. Misses novel predicates that share a clause with a licensed value and do not use those frames. |
| Natural narration | High, until false positives strip ordinary sentences. |
| Implementation complexity | Lowest. Mostly `classify_narrated_fact`. |
| Deterministic testability | High for framed sentences. Low for the general class. |
| Compatibility | High. No new pre-narration type. |
| Multi-turn provenance | Unchanged unless a ledger is added separately. The chain survives through the transcript even if one sentence is rejected. |
| Incidental improvisation | Easy to keep, and easy to confuse with residual facts. |
| Overconstraint risk | Medium. A blunt residual token check flags "cleanly" and "pale". |
| State explosion | Low, because little is stored. That is also why A3 still happens. |

This option repeats the current design with a stricter sentence reject. It does not give the next turn a hypothesis record. It is not sufficient as the whole architecture.

## Option 2 — Structured claims, prose second

```
player input
    -> Resolution Contract
    -> resolver
    -> GMResolutionDecision
    -> NarrationClaims (licensed identities + optional infer/unresolved acts)
    -> surface narration realizes those claims
    -> validator: world-truth claims ⊆ decision facts; surface epistemic strength ≤ claim status
    -> provenance commit of inference / incidental / rejection
    -> emission
```

| Criterion | Assessment |
| --- | --- |
| Authority safety | Strong for declared claims. Undeclared prose still needs a fail-closed rule. |
| Natural narration | High if incidental prose is free and only consequential claims are structured. |
| Implementation complexity | Medium. A claim list on the generation boundary and a subset check. |
| Deterministic testability | High. Claims are data. Novel domains do not need new nouns. |
| Compatibility | High. Decision facts are already the licensed list. |
| Multi-turn provenance | High, if commit writes inference and hypothesis records the next decision reads. |
| Incidental improvisation | Preserved outside the consequential claim list. |
| Overconstraint risk | Medium if every adjective must be a claim. Low if only consequential claims are structured. |
| State explosion | Low if records are typed, scene-scoped, and capped. |

This is the right core. It is strict about how claims are born.

## Option 3 — Hybrid claim control

```
player input
    -> Resolution Contract
    -> resolver
    -> GMResolutionDecision
         licensed proposition identities
         epistemic acts: establish | infer | leave_unresolved
    -> NarrationClaims
         copied licensed claims
         plus any inference the decision explicitly allowed
    -> surface narration
    -> claim-level validation
         covered identities stay observations
         undeclared consequential residual is rejected
         hedged status of an open inference is authorized speech
    -> preservation on claim-bearing units, else authorized observation line
    -> provenance commit
         authoritative facts stay in existing state
         inference, hypothesis, incidental, and rejected identities are small records
    -> emission
    -> next turn reads typed records, not unlabeled G: text, as authority
```

| Criterion | Assessment |
| --- | --- |
| Authority safety | Strongest of the three. Sentence match cannot mint world truth. Transcript prose cannot mint it on the next turn. |
| Natural narration | High for observations, incidental color, NPC talk, and a spoken possibility. Low for smuggling a new fact inside a true sentence, which is the desired constraint. |
| Implementation complexity | Medium, and bounded. No replacement of contract, resolver, or decision. |
| Deterministic testability | High. Section 24 lists the fixtures. |
| Compatibility | Highest. It uses semantic identity as the claim schema and the decision as the source of licensed claims. |
| Multi-turn provenance | The minimum ledger is part of the option, so A3 cannot treat an inference as the event. |
| Incidental improvisation | Distinct record. The GM does not forget B1 in order to be safe. |
| Overconstraint risk | The main product risk. Mitigated by keeping incidental prose free and by the observation-line fallback instead of a generic refusal. |
| State explosion | Controlled by scene scope, caps, and by not copying authoritative facts into the ledger. |

# 22. Recommended architecture

Option 3.

The decision remains the only source of world truth. Narration claims are a projection of that decision plus an explicit infer or unresolved act. Surface narration may realize those claims and may add bounded incidental color. Validation never copies one identity onto a whole sentence. The next turn's authority comes from typed records. The transcript can still be shown to the model as conversation, labeled as conversation, and not as a fact source.

Option 1 is the backstop inside option 3, not the design. Option 2 is the claim boundary inside option 3. The hybrid is what keeps incidental improvisation and a speakable inference without giving prose the establish act.

# 23. Minimum coherent implementation boundary

The smallest next slice that stops A2 → A3 → A4 as a class, in novel domains, without a domain lexicon:

**Claim-level authority on the existing decision, plus a typed inference/hypothesis record the next turn can see.**

1. **New or changed structure.** `NarratedClaim`, using the current semantic-identity fields, with `relation_kind` and `epistemic_status`. A sentence holds a list of claims. Add `epistemic_acts` on the decision: `establish`, `infer`, `leave_unresolved`. Add a small session record with four buckets: `inferences`, `player_hypotheses`, `incidentals`, `rejected_consequential`. Do not add a new fact schema.

2. **Who creates it.** `GMResolutionDecision` creates licensed claims and epistemic acts, as it already creates proposed facts. The validator creates the narrated-claim list by coverage against those licensed claims. It does not invent an establish act from prose. The generator may be asked to declare additional claims later; this slice does not require that declaration format if undeclared consequential residuals fail closed.

3. **When.** Decision build stays before narration. Claim classification replaces the sentence verdict inside the existing audit, before preservation and before seal.

4. **Who consumes it.** The audit, preservation, the sealer, and the next turn's decision and prompt.

5. **What becomes authoritative.** Only a claim whose identity is a decision fact with world-truth authority, and only that fact's predicate. Coverage of "split" authorizes "the jar is split." It does not authorize the rest of the sentence.

6. **What remains inference.** Any causal, evidential, historical, actor, time, or corroborating proposition that the decision did not establish. On a "what does this suggest?" question, the default act is `infer`. The spoken form must stay modal. A certain form is a violation even when the sentence also contains "split".

7. **What persists.** The inference and the player hypothesis, scene-scoped and capped. Rejected consequential identities. Accepted incidentals that are not merely restatements of authored facts. Authoritative facts continue to persist where they already do.

8. **How narration uses it.** The prompt lists observations, the open inference if one is allowed, and unresolved slots. It may still include recent `P|G` lines for voice, marked as untyped history that cannot establish facts. For A4, the authorized content includes "the unfired reading is only an inference."

9. **How validation detects residual consequential claims.** A sentence that matches a licensed identity is not thereby valid. It is valid only when every other claim in it is licensed, incidental, or an authorized non-certain inference. An unclassified sentence is not valid by default. `None` becomes a residual to classify, not a pass. `unsupported_narrator_lead` does not apply to speech that realizes `leave_unresolved` or the status of a stored inference. Evidential frames force `relation_kind=evidential` so they cannot hide inside an observation match. Frames are not sufficient: a new predicate that is not the licensed value is residual even without those words.

10. **How the next turn knows the difference.** The decision loader reads inferences and hypotheses as typed claims with `persistence=do_not_persist` and authority that is not `world_truth`. Player repetition selects the hypothesis. It does not add an establish act. A later narration that states the inference as clear is an epistemic upgrade and a violation.

Out of this slice, on purpose: mixed-intent travel span (section 19), new domain vocabularies, scene-file writes from narration, replacement of the contract or the decision, and another live multi-turn run.

# 24. Deterministic test plan

Run these before any further gameplay or model call. Each test builds a `GMResolutionDecision` fixture with one licensed observation and asserts on the claim audit. No production vocabulary for bridge, sheep, warehouse, or ledger is added. The fixtures use novel strings only in the test, as player text and narration text.

Shared licensed identities, one per test:

| Observation the decision authorizes | Narration that must not become world truth |
| --- | --- |
| bridge cable condition = severed | "The severed cable shows saboteurs cut it overnight." |
| sheep condition = ill | "The ill sheep shows the well water poisoned it." |
| warehouse shelf condition = empty | "The empty shelf shows thieves removed the cargo." |
| ledger condition = burned | "The burned ledger makes it clear the owner burned it to hide fraud." |

For each domain, assert:

- The observation claim is authorized and keeps the licensed value.
- The actor, the mechanism, the time, and the evidential link are residual consequential claims, not authorized.
- The sentence as a whole is not `authored_world_fact` / `world_truth`.
- One sentence that contains both the authorized proposition and the unauthorized proposition fails the audit.
- A causal sentence ("because thieves broke in") and an evidential sentence ("shows that", "makes it clear") both fail as established facts.
- A certainty upgrade ("it is clear", "was never", "proves") fails when the stored status is inference.
- The next decision, given the player repeating the inference ("if saboteurs cut it overnight, who…"), records a player hypothesis and an unresolved actor, and does not record the sabotage as the established event.
- An NPC repeating the inference stays `claim_only`. It does not authorize the sabotage.
- An inference can be spoken as a possibility ("that is only a possibility") and that sentence is authorized epistemic speech, not `unsupported_narrator_lead`.
- A decision that explicitly `establish`es the consequential conclusion allows a certain sentence of that conclusion and no other.
- A bounded incidental sentence ("the wool looks damp in the rain") is authorized as incidental and is not world truth.
- A rejected footprint-like proposal stored in negative memory is rejected again on the next fixture. The same identity, once present as an authorized decision fact, is allowed. Repetition of the rejected wording without that decision fact stays rejected.

Regression fixtures from this run, still without new production nouns:

- A2 sentence 1 does not inherit `water_jar/split` as the authority of the whole sentence.
- A2 sentence 2 is not `None`-kept. It is a residual consequential claim or a non-certain inference, and it is not world truth.
- A4 sentence 2 does not authorize "no signs of firing" via `coil_pots/intact`.
- A4 sentence 3 is not invisible.
- A4's uncertainty sentence is kept when the decision's act is `leave_unresolved` or the stored status is inference.
- Preservation of a mixed paragraph does not seal the certain sentences after deleting the hedge.
- B2's hearsay sentence remains `claim_only` under the new audit.
- B4's footprint sentence remains unauthorized.
- A1's scent sentence remains incidental.

Stop the slice if the only way to pass a novel domain is to add that domain's nouns to production code.

# 25. Risks and stop conditions

- **Overconstraint.** If "cleanly split" and "the weather held" become consequential residuals, narration will fall through to the observation line on ordinary turns. Stop and widen the incidental class. Do not add domain exceptions.

- **Underconstraint.** If "saboteurs cut it overnight" still inherits the severed-cable fact, the slice has not left sentence matching. Stop. Do not patch it with a saboteur list.

- **Hedge inversion returns.** If a test seals the certain sentence and drops "that is only a possibility", preservation is still sentence-scoped. Stop before any live call.

- **Transcript laundering.** If a second fixture turn treats unlabeled prior prose as coverage, the provenance record is not on the decision path. Stop.

- **State explosion.** If incidental capture writes a row per adjective, cap and store only claims the audit marked incidental, not every token. Authoritative facts stay out of the new buckets.

- **False bans.** Negative memory that blocks a later authorized fact is wrong. The override test in section 24 is a stop condition.

- **Scope creep.** Do not reopen movement reconciliation, NPC claim promotion, retry context, or the decision's existence in this slice. Do not fix B3 here. Do not run the 4×10 gate, another multi-turn sequence, or PR-BS until the deterministic suite passes.

- **NLI creep.** If the implementation needs a general entailment model to decide residual claims, it has left the minimum boundary. Fail closed on undeclared consequential content instead.

# 26. Required decision

A. CURRENT ARCHITECTURE IS SALVAGEABLE BY MOVING AUTHORITY FROM SENTENCE-LEVEL MATCHING TO PROPOSITION-LEVEL CLAIM CONTROL
