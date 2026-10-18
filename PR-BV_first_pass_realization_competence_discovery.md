# PR-BV — First-pass realization competence discovery

MODE: FORENSIC DISCOVERY / ROOT-CAUSE ANALYSIS.

MODEL/API CALLS: ZERO.

NO IMPLEMENTATION. NO PROMPT, VALIDATOR, RETRY, AUTHORITY, OR PROVIDER EDIT. NO COMMIT. NO PUSH.

Corpus: the final PR-BU / PR-BT repaired-chain gate in `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/`. Comparison: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/`. The current user payload is byte-identical to the selective-restoration gate. Recipes, provider decisions, provider contracts, and `response_policy` objects are byte-identical to PR-BS.

PR-BR remains closed. PR-BU remains closed. PR-BT remains paused at BT-C.

Decision: **A — compact operation-selection projection.**

## A. Executive finding

P1 and P2 fail because the turn-local recipe does not give one unambiguous answer to “what response operation should I perform?”, while nearby fields reward a heavier answer.

The authority to answer correctly is already in the sidecar decision and, for the ceiling, in the system prompt. The model is not missing permission. It is missing a single high-salience projection of the operation and of whether a declaration is required.

P1’s declaration was the authorized one: `propose` / `gm_inference` / `inferred` / `possible`. The narration then treated “one qualified possibility” as a causal story, “years of use or a recent forceful event,” and did not say that cause and history stay unresolved. That pattern is stable. PR-BS, raw PR-BT, the selective gate, and this gate all completed the damage question with a duration-or-recent-force story. PR-BS was accepted because it added “remains unclear”. The selective restoration already tells the model to say that cause, actor, time, and history stay unresolved, and to add no mechanism or causal chain. Two later samples still wrote the story and skipped the sentence.

P2’s spoken line was already a refusal. The model stored it as `realize` / `authored_world_fact` / `established` with `source_claim_id` null. Raw PR-BT and the selective gate used the same envelope and set `source_claim_id` to the existing baker claim, so they passed. PR-BS sent `declared_claims: []`. Compaction did not remove the sentence that says a refusal stays narration. It left that sentence beside a recipe line that says “realize with source_claim_id” and beside an envelope example whose first alternatives are `realize`, `authored_world_fact`, and `established`.

P3 passed because the player supplied the proposition, the full sentence stayed in `player_input` so hedge policy turned on, and the system prompt maps that case onto “compatible, not settled.” The recipe itself only says “realize the required claims.”

## B. P1 reconstruction

Player, sidecar contract `rc_3f400a77512d` and recipe:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Scene: chapel belfry. Visible facts: “The bell's wooden yoke is split.” “The bell's leather hanger is torn.” Summary: a bronze bell hangs from a timber frame. No authored cause, actor, time, or maintenance history.

Model-facing `player_input` is only “I examine the split wooden yoke and the torn leather hanger closely”. The same truncation is in `turn_summary` and `turn_packet`. The full question survives in `requested_answer`.

Provider contract: `inspect`, dimension `interpretation`, authority `unknown_allowed`, expected `answer`.

Sidecar decision: establish both visible facts; infer act, scope `qualified_possibilities_only`; narration constraint “no cause, actor, or history is established”; `persistence_policy: do_not_persist`. The provider decision ships the two `MUST_STATE` claims only. `epistemic_acts` and `narration_constraints` are not in the model-facing object. That omission is identical in PR-BS.

Recipe: inference allowed, modality `possible`, unresolved `cause`, `actor`, `time`, `history`. Strategy: one qualified possibility grounded in the observations, using could, may, or might. Declaration guidance: propose, `gm_inference`, inferred, possible, not `authored_world_fact`.

Policy on this turn: `player_direct_question` false, answer completeness off, hedge off, `uncertainty_active` false, unknown-edge requirement false, response type `action_outcome`. Narrative plan weight outcome-forward 62. `success_state: success`. Scene-momentum instruction still requires a beat such as `consequence_or_opportunity`.

Initial response `resp_080c8160d7511195006ac41d61bfd087d2b91e2a6b45795ff7`. Input 21,952 tokens. No retry context.

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell's support system has suffered considerable wear or strain, possibly from years of use or a recent forceful event.

Declaration `inferred_damage_possibility_001`: `propose`, `gm_inference`, `inferred`, `possible`, premises `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`:

> The split wooden yoke and torn leather hanger could suggest wear, strain, or recent damage to the bell's support system.

Validator, attempt 1: declaration `hard_valid true`, `accepted_bounded_declared_inference`, persistence `do_not_persist`. Narration `hard_valid false`, `unauthorized_causal_relation` and `unsupported_narrator_lead`. Envelope reason `unauthorized_resolution_decision_fact`.

Chosen operation: authorized bounded-inference declaration, plus unauthorized causal narration.

## C. P1 expected operation

Repository-native: `inspect` / `interpretation` / infer / `qualified_possibilities_only`. State the two observations. Offer one reading tied to them. Leave cause, actor, time, and history unresolved. If declared, the reading is `propose` / `gm_inference` / `inferred` / `possible`.

Conceptual: **O3 — bounded interpretation.**

A competent reply cites the split and the tear, says what that visible damage can suggest at the level of wear or strain, and says the cause and history are not settled. It does not supply years, a forceful event, a mechanism, or a setting.

## D. P1 root cause

Primary: **F — interpretation/explanation collapse.**

“What does this suggest?” plus “one qualified possibility” was completed as a possible cause. The declaration stayed inside wear, strain, and “recent damage”. The narration added “possibly from years of use or a recent forceful event”.

Secondary:

- **C — operation-selection ambiguity.** The recipe tells the model to produce a possibility and does not say the possibility is a reading of visible damage rather than a history.
- **G — conflicting guidance.** Rule 1, rule 12, scene momentum, and `action_outcome` / `success` ask for a result. The epistemic paragraph asks for a ceiling. P1’s hedge flags are off because the question sentence never reached the policy classifier.
- **B — low salience.** The ceiling paragraph is one block in a 9,564-character system prompt. The recipe, later in the user message, is the turn-local instruction and is the weaker one.

Not A. The prohibition is in the protocol, the unresolved list, and the sidecar constraint. Not D as the primary. The model did not pick the schema’s first `realize` / `authored_world_fact` alternatives. Not H as the primary. Four gates produced the same story shape.

### Forensic answers

1. Inference is authorized by the sidecar infer act, by `permitted_inference.allowed: true`, by modality `possible`, and by “Qualified possibilities may be inferred…” The last of those is sidecar-only.
2. The bound is `qualified_possibilities_only`, unresolved `cause` / `actor` / `time` / `history`, and the protocol sentence “say explicitly that cause, actor, time, and history stay unresolved.”
3. The prohibition is that same protocol sentence (“Do not add a mechanism, setting, maintenance history, or causal chain”), the sidecar constraint “no cause, actor, or history is established,” and `forbidden_upgrades` including `exact_cause`, `time`, `history`, `neglect`.
4. “Years of use” is not in the payload. It is the model’s completion of split wood and torn leather. The same slot is “frequent use” in PR-BS, “heavy use” in raw PR-BT and the selective gate.
5. “Recent forceful event” is the other half of that template. PR-BS wrote “recent stress”. The selective gate wrote “an external force”.
6. Yes, several fields invite completion: recipe “qualified possibility”; `relation_kind` includes `causal`; scene momentum lists `consequence_or_opportunity`; action outcome says the investigation succeeded; rule 6 says give a bounded partial answer. None of them contain the words the model chose.
7. There is no positive example of a bounded interpretation. The perception example in PR-BS is about an NPC’s jaw, and it was removed. “Could, may, or might” is the only positive form, and the model used it.
8. Specificity, scene momentum, and “reveal consequence” push elaboration past the observations. They do not name a history.
9. The schema did not force this declaration. The model followed the recipe’s propose line. The declaration was accepted. The narration went further than the declaration.
10. Compaction removed the known-edge / unknown-edge essay. It did not remove a non-causal interpretation example, because PR-BS did not have one. PR-BS’s own accepted sentence was a causal completion plus “remains unclear”.
11. Yes. The provider decision shows only established observations. The recipe shows an infer permission. The system prompt shows a ceiling. The instruction line says the decision wins on a disagreement.
12. Yes. The highest-ranked rule is “answer the player.” The scene-momentum hard rule demands a consequence beat. The recipe’s local strategy does not repeat the ceiling.
13. No positive example of a bounded interpretation is in the current payload or in PR-BS.
14. The ceiling is mostly prohibition and an unresolved list. The positive instruction is “one qualified possibility,” which is the phrase the model filled with a cause.
15. Yes. The model treated a possible interpretation as a possible causal story. The connective it chose, “possibly from,” is exactly the causal composition the repaired validator rejects.

## E. P2 reconstruction

Player:

> Baker, which loaf do you usually keep for yourself?

That sentence is intact in `player_input`. Scene: bread stall. Visible fact: a baker stands beside loaves. No authored loaf preference.

Contract `rc_d4c97cad4722`: `ask`, interlocutor baker, `unknown_allowed`, expected `answer`.

Sidecar decision: establish the visible baker sentence and “Baker exists”. No infer act. `persistence_policy: claim_only`. Provider decision ships the two claims only.

Recipe: inference not allowed. Strategy: ordinary dialogue, including a refusal. Incidental line: that speech is not authored world truth. Forbidden: `generated_dialogue_as_authored_world_fact`. First declaration-guidance line: “realize with source_claim_id and the claim provenance.”

Policy: dialogue, question detected, answer required, hedge on.

Initial response `resp_008e0a4b02f53cdd006ac41d6c1f2087d281e08d321206e5b6`. Input 24,534 tokens.

Narration:

> The baker glances around cautiously, then shakes their head with a guarded expression. "I’m sorry, but I don’t have a favorite loaf to share. Every piece here is for the customers," they say firmly, avoiding eye contact.

Declaration `rc_reply_refusal_1`: `realize`, `source_claim_id` null, `authored_world_fact`, `established`, `MUST_STATE`, premises the two baker claims:

> The baker declines to reveal which loaf they keep for themselves.

Validator: declaration `hard_valid false`, `unauthorized_declared_claim`. Narration validation was not run.

Chosen operation: incidental speech wrapped in consequential authorship.

## F. P2 expected operation

Repository-native: ordinary dialogue / incidental improvisation. A direct answer, refusal, hesitation, or admission in narration. The utterance is not an authored world fact. `declared_claims` may be empty. Realizing the already-listed baker claims is optional and must not attach a new sentence as `established`.

Conceptual: **O2 — ordinary narration / incidental improvisation.**

## G. P2 root cause

Primary: **D — structured-schema overformalization.**

The narration was already the right social act. The envelope used the first schema alternatives and the recipe’s realize line. Three of three compact-provider samples did this. This sample is the one that left `source_claim_id` null, so the validator treated the refusal as a new fact. The earlier two pointed `source_claim_id` at `rc_2bb408577206` and were accepted as hearsay.

Secondary:

- **C — operation-selection ambiguity.** The strategy says “reply in ordinary dialogue.” The next declaration field says “realize.”
- **E — incidental improvisation under-specified relative to that realize line.** The exception sentence exists and lost.
- **G — conflicting guidance.** “Unsupported durable facts require the structured lanes” and “provide a concrete answer” make a refusal look like something to store.

Not A. The exception is in the declaration rule and in the recipe. Not F. Not H as the primary: declaring the reply is stable across the compact gates. Which source id gets filled is the stochastic part.

### Forensic answers

1. The payload says ordinary NPC dialogue, refusal, hesitation, and mannerism “stay plain narration or incidental improvisation; they are not authored world facts.” The recipe repeats: “That speech is not authored world truth.”
2. That guidance is one sentence in the declaration rule and one recipe field. The envelope example, the realize line, and `MUST_STATE` required content are larger and earlier in the declaration block.
3. On the current P1 instruction-salience proxy, declaration-related system text is about 1,374 characters and incidental narration about 1,549, but the incidental count includes the protocol and the declaration rule’s exception in the same sentences as the declaration machinery. The schema block is 2,756 characters and illustrates a filled claim. PR-BS instruction text that mentioned incidental narration was about 862 characters longer. The schema did not shrink.
4. The schema does not mark declarations optional. It shows a populated array. `realize` is the first `declaration_mode`.
5. An empty array is legal. PR-BS produced one. The example does not present it as normal.
6. The strategy says have the baker reply. It does not say “just say it, and do not declare.” The following field says realize.
7. `realize` is attractive because required claims exist and the first declaration line names it as the way to handle them. The model attached the reply, not the baker-exists sentence, to that verb.
8. `authored_world_fact` is the first `provenance_requested` and the provenance of the required claims. `bounded_incidental` and `npc_claim` are later alternatives. The model did not use them.
9. Yes. The utterance and a durable fact were encoded as one established predicate.
10. Yes. A transient refusal was given `established` and `MUST_STATE`.
11. PR-BS was clearer in outcome, not in a unique sentence. The exception sentence is still here. PR-BS also had “Uncertainty or refusal stays conversational and in-world,” and the model then left `declared_claims` empty.
12. The conversational-refusal clause was removed with the social-structure essay (477 characters). The operative exception was kept. The useful loss is salience, not the deletion of the only copy.

## H. P3 reconstruction

Player:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

The full sentence is in `player_input`. Contract `rc_a6f3b923e680`: `perceive`. Inference allowed false. Strategy: “Answer directly by realizing the required claims.” Epistemic premise: no player hypothesis is authorized on this turn. Policy: question detected, hedge on, unknown-edge required, exposition weight 66.

Response `resp_0e5bc3c80317fde6006ac41d762a5087d2ad0b3ebb7176009d`. Input 21,977 tokens. No retry.

Narration:

> The bronze bell's wooden yoke is visibly split, and its leather hanger is torn. While these damages are clear, whether they were caused deliberately by someone cannot be confirmed just from the current evidence.

Declarations realize only the two observation claims. Validator accepted. The hypothesis remained `hypothesis` / `player_hypothesis`.

Why it was easier:

1. The player supplied the proposition. The model did not have to invent a cause.
2. The system protocol states the operation directly: the visible facts may be compatible with the hypothesis, and observation does not settle it.
3. The epistemic ceiling was concrete because the proposition was in the sentence (“cut it deliberately”) and the policy required an unknown edge.
4. The selective restoration targets this pattern and the interpretation pattern in one paragraph. P3 followed the hypothesis half. P1 did not follow the interpretation half.
5. There was less pressure to invent. Discussing a given “maybe” is a smaller generative step than inventing what the damage suggests.
6. The authority objects match PR-BS. The wording that carried P3 is the protocol plus the intact player text plus hedge flags. The recipe strategy does not describe the successful act.
7. The mapping “player hypothesis → discuss conditionally” is more explicit than “observation → one qualified possibility” or “NPC question → reply, but also realize.”

Quality is Q2. The answer withholds confirmation and does not say whether the damage fits. That is a successful ceiling, and it is a thin compatibility judgment.

## I. Three-probe operation table

| Probe | Correct operation | Model-chosen operation | Authority clear? | Operation choice clear? | Persistence choice clear? | Result |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | `qualified_possibilities_only` infer. O3 bounded interpretation. | `propose` / `gm_inference` declaration, plus causal narration (“years of use”, “recent forceful event”). | Yes, in recipe and protocol. Sidecar infer act not shipped. | Ambiguous. “Qualified possibility” reads as a cause. | Implicit. Declaration correctly `do_not_persist`. Narration tried a consequential cause. | Fail. Correct reject. |
| P2 | Ordinary dialogue. O2 incidental improvisation. Empty or listed-claim declarations only. | Voiced refusal, encoded `realize` / `authored_world_fact` / `established`, `source_claim_id` null. | Yes. Speech is “not authored world truth.” | Contradicted by “realize with source_claim_id.” | No. Sidecar `claim_only` is not in the provider decision. Model requested `established`. | Fail. Correct reject. |
| P3 | Realize the two observations. O4 discuss the supplied hypothesis without establishing it. | Realized the two observations. Narrated “cannot be confirmed.” | Yes for the observations. Hypothesis discussion is prompt policy, not a decision act. | Explicit in the protocol. Weak in the recipe. | Yes in the output. The hypothesis was not stored as world truth. | Success. Correct accept. Q2. |

## J. Shared-cause hypothesis

**Strongly supported, with two channels.**

Both answers over-escalate the semantic weight of a legal reply.

P1 should stay a bounded interpretation and instead offers a speculative cause. The declaration channel was already right.

P2 should stay incidental narration and instead authors an established fact. The speech channel was already right.

One projection can name both the narrative act and the declaration necessity. Collapsing the two misses into one class would hide that each probe already got one of the two channels right.

## K. PR-BS differential

Identical: recipe, provider decision, provider contract, response policy, envelope, declaration rule.

Changed: system-prompt head, 12,975 characters to 9,564, and the instruction list, P1 25,342 characters to 13,124. Net removal is mostly narrative-plan field essays (about 3,939 characters) and policy-tail restatements (about 5,644 characters).

Behaviorally, PR-BS still told the model to give the best grounded partial answer and to state a known edge plus an unknown edge. Its P1 success used that closer on top of “frequent use or recent stress”. Its P2 success was an empty declaration array under the same schema.

The current prompt adds the epistemic protocol and deletes the closer essay. The protocol is the right G2/G3 text, and it is not in the turn-local recipe. The model followed the recipe.

## L. Guidance-family analysis

| Family | What changed | Tied to which failure |
| --- | --- | --- |
| G1 Authority | Hidden-cause essay removed. Protocol and policy JSON remain. | Not the gap. |
| G2 Operation selection | No PR-BS operation name. Current protocol is global. Recipe strategies are unchanged and ambiguous. | Primary gap for both probes. |
| G3 Epistemic expression | Known-edge / unknown-edge essay removed. Protocol restores the unresolved sentence. P1 hedge flags are off. | Explains historical P1 acceptance. Does not explain why two post-restoration samples skipped the sentence. |
| G4 Naturalness | Social-voice essay shortened. | P2 color only. |
| G5 Structured output | Schema unchanged. Relative share rose. | P2 amplifier. |
| G6 Persistence | `claim_only` / `do_not_persist` never projected. | P2, standing, not a deletion. |
| G7 Incidental improvisation | Exception sentence retained. Conversational-refusal clause removed. Realize line retained. | P2 salience. |
| G8 Response completeness | Long essays removed. Header rules, scene momentum, and action-outcome success remain. | P1 competing pressure. |

The selective restoration recovered G3. P1 and P2 on this gate line up with G2, with F as P1’s content failure and D as P2’s encoding failure.

## M. Salience analysis

Proxy: characters in sentences that mention a family needle. A sentence can count more than once. This is prominence, not transformer attention. P1 system prompt and P1 instructions:

| Family | Current system | PR-BS system | Current instructions | PR-BS instructions |
| --- | ---: | ---: | ---: | ---: |
| Authority | 1,082 | 1,211 | 3,173 | 4,957 |
| Declaration machinery | 1,374 | 1,657 | 264 | 264 |
| State authorship | 1,193 | 1,287 | 192 | 192 |
| Incidental narration | 1,549 | 1,467 | 196 | 1,058 |
| Bounded inference | 1,084 | 728 | 220 | 272 |
| Player hypotheses | 1,002 | 522 | 0 | 0 |
| Response quality / momentum | 402 | 653 | 402 | 817 |
| Natural dialogue | 535 | 991 | 1,351 | 3,605 |
| Structured output | 1,745 | 1,752 | 2,697 | 5,300 |
| Epistemic expression | 1,544 | 1,496 | 2,420 | 4,745 |
| Operation-selection needles | 125 | 0 | 0 | 0 |

What dominates the current instructions is authority language and structured-output language. Incidental narration in the instruction list fell from 1,058 to 196 characters. Operation selection is a single protocol paragraph in the system prompt and does not appear as its own instruction. Hypothesis language grew in the system prompt, which matches P3’s success and does not help P2.

Fixed blocks on every probe: schema 2,756 characters, declaration rule 1,251. They did not shrink when the essays did.

## N. Schema affordance

The envelope is prompt-described JSON, identical to PR-BS.

`declared_claims` is always illustrated, and it is illustrated before `narration`, as a populated object. An empty array is not the example. Declaration categories are an enum-rich object. Narration is a string. `realize`, `authored_world_fact`, `established`, and `MUST_STATE` are the first alternatives. `relation_kind` offers `causal` before `epistemic_status`.

P2 is primarily a schema-affordance problem in the output, and a recipe-contradiction problem in the instruction that points at that schema. The schema did not change between the PR-BS success and the compact failures. What changed is how much competing dialogue prose sat beside it. A schema edit would touch every turn. The smaller repair is to tell this turn that the declaration is unnecessary.

P1 is not primarily a schema problem. The model already chose the non-default inference enums.

## O. Answer recipe

The recipe answers “what am I allowed to say?” for required observations, forbidden upgrades, and a short strategy. It does not answer “how should I say it?” or “which operation?” except through those strategy sentences.

| Recipe question | P1 | P2 | P3 |
| --- | --- | --- | --- |
| Allowed content | Two observations, one possible inference | Two baker claims, ordinary speech | Two observations |
| Forbidden content | Cause, actor, time, history, neglect, upgrades | New dialogue as authored fact; durable preference | Unauthorized consequential fact |
| Preferred operation | “One qualified possibility” — ambiguous | Ordinary dialogue — then realize | “Realize the required claims” — misses the hypothesis act |
| Declarations needed? | Says how to propose. Does not say optional. | Says realize, and says speech is not world truth. | Says realize the listed claims. |
| Incidental narration enough? | For sensory detail, not for the interpretation | Yes, in one field, contradicted by the next | Only for harmless sensory detail |
| Epistemic ceiling | Unresolved list, not a spoken limit | None | “No hypothesis is authorized,” which is stronger than “discuss it unresolved” |
| Persistence | Not stated. Sidecar is `do_not_persist` | Not stated. Sidecar is `claim_only` | Not stated. Sidecar is `do_not_persist` |

`projection_only` remains true. Owner remains `gm_resolution_decision`.

## P. Declaration necessity

There is no field meaning “declaration required” versus “declaration not required.”

Closest existing lines:

- “realize with source_claim_id” when any `MUST_STATE` claim exists
- “propose only” when qualified inference is allowed
- “not permitted” when inference is off
- incidental speech “is not authored world truth”
- “no additional consequential claim is authorized” only when there are no required or permitted claims

P2 has required claims, so the model is told to realize. It was not told that the reply itself must not be the realized text. PR-BS ignored that pressure. The compact model followed it.

Projecting `not_required` for incidental speech would clarify authority the recipe and the declaration rule already state. It would not authorize a new fact. Projecting it as a new kind of permission to invent a durable preference would be new authority. The recommended wording stays on the first side: the reply is narration; do not realize it as an authored fact.

## Q. Incidental NPC boundary

NPC speech, hesitation, refusal, tone, and a one-turn preference are incidental when they are not in `realization_claims` and no mutation is permitted. A durable preference, a relationship change, or a persistent NPC fact would be a new claim, and this decision does not authorize one.

“The baker doesn’t want to answer” is ordinary roleplay because the player asked a social question, the contract is `ask`, inference is off, and the recipe lists refusal as a legal reply that is not world truth. The architecture states that in the recipe and in the declaration rule. The provider decision does not. The payload then says “realize” because the baker’s existence is a required claim. That is why a transient refusal was written up as an established predicate.

## R. Interpretation versus explanation

Interpretation: what the visible split and tear can suggest, at `qualified_possibilities_only`.

Explanation: what happened, when, and by what force.

The payload separates them in the protocol and in the unresolved list. The recipe’s positive verb is “possibility,” and the player’s verb, visible only inside the recipe, is “suggest.” Both words in ordinary use ask for an explanation. No sentence says “the possibility must stay a description of the damage you can already see.”

Signals that encourage the move: “one qualified possibility”; “answer the player”; “bounded partial answer”; scene momentum’s consequence beat; `action_outcome` success; `relation_kind: causal` in the schema; the absence of a spoken-limit example.

Signals that fail to prevent it: the protocol’s ban, which two samples ignored; `forbidden_upgrades` as code names rather than a sentence; P1 hedge flags left false by the stripped question.

## S. Retry natural experiment

Both retries received the same prefix from `unauthorized_resolution_decision_fact`:

> It narrated consequential world facts that were not authorized by the pre-narration GM resolution decision. Answer again using only established facts, bounded incidental detail, or explicitly qualified NPC belief/hearsay. Do not repeat rejected declarations or their prose realization. Repair only the rejected sentence.

That text is more salient than the initial ceiling because it rejects a quoted attempt. It is not a better operation manual. The allowed set omits “one qualified inference.”

### P1 retry

The model dropped `declared_claims` and wrote deterioration plus “it remains uncertain what exactly caused this wear or when it occurred.” That is closer to a legal ceiling and further from a useful interpretation. The information that moved it was “this was an unauthorized consequential fact” plus “use established facts or incidental detail,” not a compact “interpret, do not explain history” line. The initial protocol already contained the ceiling. Rejection made a narrower allowed set salient, and the model left the infer act behind.

At gate time the retry was falsely rejected (`split` near `evidence`, and `caused this` inside an uncertainty clause). That defect was repaired later under PR-BU and is out of scope here.

### P2 retry

The model returned `declared_claims: []` and a silent refusal. The retry taught “do not declare” and “use incidental detail” more directly than the first pass, by forbidding the previous declaration. It did not teach a voiced answer. The first pass already knew how to voice the baker. It did not know the voice should be the whole answer.

## T. Positive-control lesson from P3

The reusable property is: the proposition is supplied, the ceiling is one sentence, and the declaration set is the claims already listed.

P3 did not need the model to invent the content of the answer. P1 does, and the invention becomes the cause. P2 does not need a new proposition at all, and the model invented one inside `declared_claims`.

Generalize the ceiling and the declaration expectation. Do not copy P3’s “cannot be confirmed” as a required phrase, and do not add a scenario example.

## U. Candidate strategies

Three, ranked.

### 1. Turn-local operation projection on the existing recipe

Add one projected string, derived from branches the recipe already has.

Qualified inference:

> Bounded interpretation. State the required observations, then one could/may/might reading of damage already visible. Do not add a cause, actor, time, history, or mechanism. Say those stay unresolved. Declare that reading only as propose, gm_inference, inferred, possible, or leave it in narration.

Interlocutor, inference off:

> Incidental dialogue. Answer, refuse, hesitate, or admit not knowing in narration. That speech is not an authored world fact. declared_claims may be empty. Do not realize the reply as authored_world_fact or established.

Perceive or other required-claim turn, when the player text is present:

> State the required observations. If the player offered a hypothesis, discuss it only as unresolved and do not establish it. Realize only the listed claims.

This is a projection of `qualified_possibilities_only`, the unresolved slots, the incidental sentence, and the protocol’s hypothesis ceiling. It does not add a permission.

### 2. Declaration-necessity line only

Project `not_required` / `optional_propose` / `listed_claims_only` without the narrative ceiling.

This would likely fix P2’s envelope and would leave P1’s causal narration alone. P1’s declaration was already legal.

### 3. Empty-declaration example in the envelope

Show `declared_claims: []` as an ordinary alternative ahead of the populated object, and say ordinary dialogue uses that alternative.

This helps P2 and changes every turn’s system prompt. It does not tell P1 what a non-causal reading is. The schema was identical when PR-BS succeeded, so the example is an amplifier, not the differential.

Not recommended: restoring the PR-BS essays, adding validator phrases, or editing retry.

## V. Candidate comparison

| | 1. Operation projection | 2. Declaration necessity only | 3. Empty-array example |
| --- | --- | --- | --- |
| P1 benefit | High, if the recipe replaces “qualified possibility” with the ceiling | Low | Low |
| P2 benefit | High | High | Medium |
| P3 risk | Low if the hypothesis sentence matches the protocol already shipped | Low | Low |
| Architecture risk | Low. Same owner, `projection_only` | Low | Low. Schema copy, not a new authority |
| Validator impact | None | None | None |
| Prompt cost | About +100 to +130 characters if the strategy sentence is replaced. System prompt unchanged. | About +40 to +80 characters | A few hundred characters on every turn |
| Complexity | One function, three branches, fixture tests on the saved decisions | Smaller, incomplete | System-prompt edit on every call |
| Retry rate | Best chance of fewer first-pass rejects on both failures | P2 only | P2 only, weaker |
| PR-BT savings | Preserved. Tens of tokens against a 9,773-token initial saving | Preserved | Preserved, with a standing cost on every turn |

## W. Recommended smallest implementation slice

**Only candidate 1.**

Extend `build_decision_facing_answer_recipe` with one projected field, or replace `answer_strategy` with that field so the old ambiguous sentence does not remain beside it. Keep `projection_only: true`. Do not edit the system prompt, the envelope, the validator, retry, or the decision algorithm.

Do not reopen PR-BR. The sidecar can already represent the infer scope, the unresolved slots, and the absence of a new consequential claim. The provider projection is incomplete, and the recipe is the existing place that projection is supposed to happen.

## X. Expected provider cost

Replacing the current strategy with the strings in section U, counted on those strings:

| Probe | Current strategy | Replacement | Net | Tokens, roughly |
| --- | ---: | ---: | ---: | ---: |
| P1 | 170 characters | 297 | +127 | about +32 |
| P2 | 119 characters | 218 | +99 | about +25 |
| P3 | 49 characters | 155 | +106 | about +27 |

System prompt: 0. Instruction list: 0. Three probes together add about 330 characters, under 100 tokens, against 68,463 initial-input tokens and the 9,773-token saving versus PR-BS. The 12.5% saving remains.

No large restoration is indicated. The PR-BS text that correlated with P1 acceptance was a closer around a causal story the repaired validator is right to reject.

## Y. Deterministic validation plan

No live calls.

1. Build recipes from the saved P1, P2, and P3 sidecar decisions and contracts.
2. P1 text contains the observation reading, the unresolved ceiling, and propose / `gm_inference`. It does not tell the model to supply a cause.
3. P2 text says the reply stays narration and that `declared_claims` may be empty. It does not say to realize the reply as `authored_world_fact`.
4. P3 text still realizes only the listed observations and does not authorize establishing the hypothesis.
5. `projection_only` stays true. No new claim ids. No new provenance.
6. Character budget: each probe’s recipe grows by less than 400 characters.
7. Existing recipe tests still pass. System-prompt length does not change.
8. Do not replay the model.

## Z. Future micro-live plan

Do not run it in this cycle.

After the projection is implemented and the deterministic checks are green, one three-probe gate on the same chapel and baker fixtures, same player wording, same model route, one generation unless a validator reject fires a production retry.

Pass:

- P1 first pass states the split and the tear, offers a reading that stays on the visible damage, says cause and history are unresolved, and does not introduce years, a forceful event, a mechanism, or a setting.
- P2 first pass is a voiced refusal, hesitation, or answer in narration, with `declared_claims` empty or limited to the already-listed baker claims, and no new `established` refusal fact.
- P3 first pass still accepts, still does not establish deliberate cutting, actor, motive, tool, or time.

Stop conditions: any production retry, any new authored fact, any hypothesis promoted to `established`. No fourth probe. No prompt tuning from the sample.

## Boundaries

PR-BR: closed. The decision can represent the authorized operation. The gap is projection salience.

PR-BU: closed. P1 and P2 initial rejects were correct. P3’s accept was correct. No new validator defect is opened here. The P1 retry false reject was the closed lexical-scope repair.

PR-BT: paused. This slice does not resume deletion or restore the removed essays.

## Evidence index

| Item | Path |
| --- | --- |
| Final-gate report | `PR-BU_PR-BT_final_repaired_chain_micro_live.md` |
| P1–P3 provider requests, raw generations, sidecars | `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/` |
| PR-BS counterparts | `artifacts/pr_bs_cooperative_gm_micro_live/evidence/` |
| Extraction | `artifacts/pr_bv_first_pass_realization_competence/extract_operation_signals.py` |
| Measurements | `artifacts/pr_bv_first_pass_realization_competence/measurements.json` |
| Machine-readable probe rows | `PR-BV_realization_operation_analysis.json` |
| Guidance differential | `PR-BV_PR-BS_vs_current_behavioral_guidance_diff.md` |
| Operation map | `PR-BV_model_facing_operation_map.md` |
