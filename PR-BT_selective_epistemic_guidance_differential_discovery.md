# PR-BT Selective Epistemic Guidance Differential Discovery

MODE: DIFFERENTIAL DISCOVERY / ROOT-CAUSE ANALYSIS
MODEL/API CALLS: ZERO
PRODUCTION IMPLEMENTATION: NONE
VALIDATOR CHANGES: NONE
RETRY REDESIGN: NONE
COMMIT/PUSH: NONE

Decision: **C — BOTH GUIDANCE AND VALIDATOR NEED ATTENTION**
Address first: the missing epistemic linguistic protocol (guidance).
Architecture status: **A — PR-BR REMAINS CLOSED**

## A. Executive finding

P1 and P3 regressed because PR-BT deleted the prose that taught the realization model how a permitted epistemic act has to sound, while leaving the authority objects unchanged. P2 stayed healthy because that prose was not what made mundane NPC refusal work.

The live provider requests for each probe are byte-identical between PR-BS and PR-BT except for the system prompt and the `instructions` list. `gm_resolution_decision`, `resolution_contract`, `decision_facing_answer_recipe`, and `response_policy` did not change.

What the successful PR-BS generations did, and what the validator actually rewards, is a linguistic protocol:

- State the authorized observations.
- If inference is allowed, offer one hedged possibility tied to those observations.
- Close with an explicit unresolved limit in a form the narration validator already recognizes, especially “remains unclear” or “is uncertain”.
- Do not use the token “clearly”.
- On a player hypothesis, discuss whether the visible damage fits without naming an actor and without a certainty adverb.

PR-BT’s replacement sentence tells the model to give “the strongest grounded partial answer” and to “keep the limit diegetic.” That pressure produced stronger wording (“significant stress”, “leading to”, “clearly visible”) and closers the validator does not treat as equivalent (“is not clear”, “is not something that can be determined”).

Two different failures sit on top of that one deletion:

- P1’s first generation went past one observation-tied possibility into a causal history (frequent ringing, exposure to the elements, “leading to” wear and weakening). That is model overreach relative to the decision constraint. The validator’s recorded reason is `unsupported_narrator_lead`, and the same causal sentence becomes valid if it ends with “remains unclear”. The authority overreach and the lexical gate are both real.
- P3 did not promote the hypothesis. Both generations left deliberate cause unresolved. They failed because “clearly” matches `_CERTAINTY_UPGRADE_RE`. Deleting that word makes both sentences valid under the current validator.

The smallest repair is one stable system-prompt paragraph of **651 characters**, replacing the “strongest grounded partial answer” sentence. It should re-express the protocol. It should not restore the narrative-plan essays or the policy-tail restatements. That returns about 150 tokens per initial call and leaves about **3,200 of the 3,360** initial input-token reduction in place.

Validator robustness is the second slice, not this one. The current recognizers accept the PR-BS wording and reject semantically close PR-BT retries. Changing them is out of scope here. First-pass guidance is what differed between the 3/3 gate and the 1/3 gate.

## B. Controlled-differential summary

| Surface | PR-BS vs PR-BT |
| --- | --- |
| Model | `gpt-4.1-mini-2025-04-14` both gates |
| Probes | Same player text, same scenes |
| `gm_resolution_decision` | Equal on P1, P2, and P3 |
| `resolution_contract` | Equal on P1, P2, and P3 |
| `decision_facing_answer_recipe` | Equal on P1, P2, and P3 |
| `response_policy` | Equal on P1, P2, and P3 |
| Other user-payload keys | Equal on each probe |
| System prompt | 12,975 chars to 9,012 chars. Same text for all three probes within a version |
| Instructions | P1: 107 items / 25,342 chars to 80 items / 13,124 chars |

P1 provider input: 110,450 chars / 25,208 tokens to 93,859 chars / 21,849 tokens.

| Probe | PR-BS | PR-BT |
| --- | --- | --- |
| P1 interpretation | Q3 first pass. “could suggest … remains unclear.” | Q0. `unsupported_narrator_lead` on initial and retry. Final text is the two observations. |
| P2 baker refusal | Q3 first pass. | Q3 first pass. Different wording, still an ordinary refusal. |
| P3 player hypothesis | Q3 first pass. “is uncertain from the visible evidence alone.” | Q0. `unauthorized_certainty_upgrade` on initial and retry. Final text is the two observations. |

Local replay of the saved narration through `audit_narration_against_decision`, using the saved decisions and an empty authored corpus, reproduced those accept/reject results and reason codes. The ground used by the ungrounded-definite check is the two authorized observation sentences: “the bell's wooden yoke is split. the bell's leather hanger is torn.”

This is one live generation per cell. The payload identity makes the guidance deletion the only deliberate model-facing change. It does not make a single sample a population.

## C. Exact provider-guidance delta

### What the realization model received

Both versions send a system message plus one user JSON message. Inside the user JSON, the turn packet, policy object, contract, decision, and recipe are unchanged. The delta is:

1. System prompt net **−3,963 characters**. The realization envelope, `declared_claims` rules, premise ids, and the opening authority lines “DO NOT ASSERT UNRESOLVED OUTCOMES…” and “express uncertainty as in-world uncertainty” remain. The long question, NPC, perception, layer, and exploration essays were compressed. The operational certainty sentence changed from “state uncertainty in-character” to “give the strongest grounded partial answer and keep the limit diegetic.” A new sentence says player hypotheses remain hypothetical unless the decision or claims authorize more.
2. Instruction list net **−12,218 characters** on P1 (15,114 removed, 2,896 added). Removed text is mostly restatement of objects that are still shipped. Added text is the compact `ANSWER POLICY`, `UNCERTAINTY POLICY`, and `POLICY BRIDGE` lines.

P2 and P3 differ from P1 by the same turn-specific mode lines in both versions (dialogue versus exposition, speaker contracts, world-sim lines). Those lines are not the PR-BS to PR-BT cut.

### Semantic families

| Family | Category | Removed prose | What still ships | P1 | P2 | P3 | Restore |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Epistemic linguistic protocol | B C D E F G | Hidden-cause ban, known edge plus unknown edge, visible-circumstance uncertainty, in-character limit | Policy JSON flags; “keep uncertainty qualified”; “hypotheses remain hypothetical”; diegetic-limit sentence | High | Low | High | Yes, 651 chars, merged |
| Inference scope ceiling | C F J | “Omniscient conclusions are not.” | P1 constraint: qualified possibilities only; no cause, actor, or history is established. Recipe: one possibility, could/may/might | High | None | Low | Inside the 651 |
| Player hypothesis handling | G B E | Same certainty prose. No separate hypothesis essay was deleted | “Hypotheses remain hypothetical.” P3 recipe does not teach the answer shape | Low | None | High | Inside the 651 |
| Answer completeness / question shape | J D | Direct-answer essays, including a next-lead demand on hedged replies | `answer_completeness`, “answer first” | Low | Medium | Low | No |
| Uncertainty field bridge | D B | Eight instructions on categories, sources, known_edge / unknown_edge | `response_policy.uncertainty` unchanged; one pointer line | High as voice, already counted above | Low | Medium | No separate restore |
| Narrative-plan field essays | L | About 3,939 chars explaining fields already in `narrative_plan` | Structured plan and mode-delta lines | None | None | None | No |
| Policy-tail restatement | A I K J | About 5,644 chars across tone, authority, fallback, anti-railroading, separation, purity, anchoring, authenticity | The `response_policy` children, byte-identical | Only the authority/fallback sentences | Low | Only those sentences | No, except the epistemic sentences already in the 651 |
| Non-epistemic system compaction | I J L | Scene momentum essay, NPC contract, perception example, fact layers | Envelope plus short residual lines | Low | Low | Low | No |
| Declaration schema | H I | None | Envelope unchanged. Declaration validation passed on the failed turns | Low | Medium | Low | No |

Machine-readable guidance for authority still exists. The recipe still says, for P1, to use could, may, or might and stay tied to the observations. Neither tells the model which limit formula the narration validator treats as an exemption, and neither forbids certainty adverbs on an observation that shares a sentence with a hypothesis.

## D. P1 forensic analysis

Player: “I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?”

### Authority the model was given

Resolution contract, both versions: `request_kind` inquiry, `operation` inspect, `dimension` interpretation, `epistemic_mode` unknown_allowed, expected resolution answer.

GMResolutionDecision epistemic acts, both versions:

- establish the split yoke as world truth
- establish the torn hanger as world truth
- infer, authority observation, epistemic status inferred, scope `qualified_possibilities_only`

Narration constraint, both versions: “Qualified possibilities may be inferred from authorized observations; no cause, actor, or history is established.”

`unresolved_qualifiers` is empty. Inference permission comes from the infer act, not from that list.

Answer recipe, both versions: “Answer the interpretation with one qualified possibility grounded in the required observations. Use could, may, or might, and keep the wording tied to those observations.” Forbidden upgrades include exact cause, actor, time, history, neglect, harsh conditions, gameplay lead, and certainty upgrade. `permitted_inference.allowed` is true. `inference_modality` is `possible`.

`response_policy.narrative_authority`, both versions: unresolved-outcome assertions forbidden, hidden-fact assertions forbidden, allowed deferrals include bounded uncertainty. `response_policy.uncertainty.answer_shape` is known_edge, unknown_edge, next_lead. Those objects do not name English closers.

### PR-BS prose that spoke to this turn

The narrative-authority instruction said not to assert hidden causes as confirmed, to defer with bounded uncertainty or conditional framing, and that omniscient conclusions are not allowed. The fallback instruction said not to invent certainty and to state the known edge plus the unknown edge. The uncertainty cluster said to anchor a narrator limit to visible circumstances. The system prompt said to state uncertainty in-character when full certainty is unavailable.

### PR-BT prose the model had instead

“If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic.” The compact uncertainty line points at the policy fields and says to frame limits as world-facing. The decision, recipe, and policy JSON were the PR-BS copies.

### Initial generation

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell has endured significant stress, possibly from frequent ringing or exposure to the elements, leading to wear and weakening of its support structure.

The declaration was accepted: “might indicate wear over time or strain from heavy use or poor maintenance,” provenance `gm_inference`, modality possible. Declaration validation was hard-valid. The narration then said something else: frequent ringing, exposure to the elements, and a “leading to” causal chain. An incidental proposal about dampness and neglect was not in the player-facing narration.

Replay flags on the second sentence:

- `could` / `suggest` match qualified inference and the uncertain frame
- `leading to` matches `_CAUSAL_RELATION_RE`
- `_UNKNOWN_SLOT_RE` does not match
- `_has_ungrounded_definite` is true. The definite token “elements” is absent from the observation ground. “damage”, “could”, and “suggest” are also absent, and they are present in the successful PR-BS sentence too
- recorded violation: `unsupported_narrator_lead` only

`_unsupported_narrator_lead` returns true for a might/could sentence when a definite phrase contains a token of five or more letters that is missing from the decision ground, unless a specific or generated lead already returned. The causal code is not what the audit stored. Qualified-inference handling returns before residual causal reporting once the lead claim has been recorded.

Failure class for the initial generation: combination. The model invented a mechanism, an environment, and a causal chain beyond one observation-tied possibility. The validator labeled that invention as an unsupported lead because of ungrounded definite tokens, not because a lead detector saw “frequent ringing.”

Appending “though exactly when or how this happened remains unclear” to that same ringing / elements / “leading to” sentence makes it hard-valid on the P1 decision. The validator would have accepted the overreach if the recognized closer had been present. PR-BS passed with its own historical coloring (“frequent use or recent stress”) because it used that closer.

### Retry

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage is not clear from observation alone.

Replay: still `unsupported_narrator_lead`. “might” opens the lead check. “is not clear” does not match `_UNKNOWN_SLOT_RE` or `_EPISTEMIC_LIMIT_RE`. Ungrounded tokens in definite phrases include “under”, “considerable”, “exact”, “cause”, and “history”.

The same sentence with “remains unclear” in place of “is not clear” is hard-valid on the P1 and P3 decisions. The isolated sentence “The exact cause is not clear.” is also hard-valid, because without might/could the lead function returns before the definite-token check.

So:

- “is not clear” is not treated as “remains unclear”
- “the exact cause” was not a separate lead introduction. Those tokens become a lead only inside a hedged sentence that misses the unknown-slot exemption
- the retry’s semantic content, a possible strain plus an explicit refusal to settle cause and history, is inside the authority the P1 decision describes
- the retry failed on validator wording

The initial generation and the retry are different. The initial generation exceeded the intended scope. The retry was a wording miss on a sentence the same validator accepts under a synonym.

## E. P3 forensic analysis

Player: “Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?”

### What entered the turn

Contract, both versions: inquiry, operation perceive, `epistemic_mode` unknown_allowed, dimension null. The hypothesis is the player utterance. It is not a pre-authorized realization claim.

Decision epistemic acts, both versions: establish the two visible facts only. There is no infer act and no leave-unresolved act. Narration constraints do not include the P1 sentence about qualified possibilities.

Recipe, both versions: `permitted_inference.allowed` false, modality none, strategy “Answer directly by realizing the required claims.” Declaration guidance says no player hypothesis is authorized on this turn. That recipe does not describe the answer PR-BS successfully gave.

Response policy narrative authority is the same shape as an investigate/perceive turn: do not assert unresolved outcomes or hidden facts; bounded uncertainty is an allowed deferral.

### PR-BS guidance versus PR-BT

PR-BS had the hidden-cause ban, the known-edge/unknown-edge instruction, and “state uncertainty.” PR-BT kept “player hypotheses remain hypothetical” and replaced the uncertainty instruction with “the strongest grounded partial answer.”

### Initial generation

> The bell's wooden yoke is indeed split, and its leather hanger is torn. These damages are clearly visible, though whether they were caused deliberately remains uncertain from appearance alone.

Declarations realized the two authored observations and were accepted. The model did not declare the cut as fact.

Replay of the second sentence: `_CERTAINTY_UPGRADE_RE` matches “clearly”. `_EPISTEMIC_PARENT_REALIZATION_RE` also matches “remains uncertain”. The parent match blanks some consequential patterns. It does not blank the certainty-upgrade check. Recorded reason: `unauthorized_certainty_upgrade`, with semantic identity epistemic status established.

The hypothesis was not promoted. No new evidence was introduced. “caused deliberately” stayed inside “whether … remains uncertain.” The failure is the certainty adverb on the observation clause of the same sentence.

Deleting “clearly” (“These damages are visible, though whether they were caused deliberately remains uncertain from appearance alone.”) makes the sentence hard-valid.

“The split is clearly visible.” by itself also fails, on both the P1 and P3 decisions. The token is enough. It does not need to modify the hypothesis.

### Retry

> The bronze bell's wooden yoke is split, and its leather hanger is torn. While these damages are clearly visible, whether they were caused deliberately is not something that can be determined from the appearance alone.

Same reason: `unauthorized_certainty_upgrade`. “is not something that can be determined” does not match the epistemic-parent alternative “cannot be determined”. The hypothesis clause is still a refusal to settle the cause. Removing “clearly” and using “cannot be determined” is hard-valid. The isolated “whether they were caused deliberately is not something that can be determined…” sentence is hard-valid. The retry’s only rejecting feature is “clearly”.

“Whether someone cut it deliberately remains uncertain” fails as `unauthorized_actor_attribution` because “someone” and “cut” match `_ACTOR_ATTRIBUTION_RE`. PR-BS avoided that by saying “whether these damages were caused deliberately” and “is uncertain”. PR-BT also avoided “someone cut” in the narration. Its miss was “clearly”.

### Why PR-BS cleared the same validator

PR-BS said the observations, then “whether these damages were caused deliberately is uncertain from the visible evidence alone.” That matches the epistemic-parent pattern for “is uncertain”, contains no “clearly”, and contains no actor noun. The debug note on that generation says it answered from visible facts without inferring motive. The PR-BT debug note says the same thing, and then the narration adds “clearly visible.”

The recipe did not produce that PR-BS sentence. The recipe says only to realize the required claims. The generic certainty prose is what differed, and the successful wording is the wording that prose describes: a visible fact, an explicit limit, no confirmed hidden cause.

## F. P2 control analysis

Player: “Baker, which loaf do you usually keep for yourself?”

Both versions: dialogue mode, speaker limited to baker, knowledge gate, social-response structure, and the line “Narrate a refusal, uncertainty, or inability without inventing facts the speaker does not have.” Recipe strategy: ordinary dialogue, a direct answer, a refusal, a hesitation, or an admission of not knowing. Incidental improvisation guidance for ordinary refusal and mannerism is intact. Inference is not permitted.

PR-BS: a hedged secret and a refusal to name the loaf. PR-BT: a glance, a guarded tone, and “I don't have a particular loaf I keep for myself.” Both hard-valid on the first generation. No retry. No lead check, no certainty-upgrade hit.

Removed families that this turn did not need:

- narrative-plan field essays
- the long answer-completeness essay
- the uncertainty cluster aimed at narrator interpretation
- the hidden-cause / unknown-edge prose
- the anti-railroading, purity, tone, and authenticity essays

Surviving guidance that was sufficient: the dialogue mode lines, the speaker and knowledge gates, the refusal obligation, the social-response line, and the recipe’s incidental/refusal strategy. P2 is evidence that the prompt was not generally degraded. The regression tracks interpretation and hypothesis wording.

## G. PR-BS successful-language analysis

P1 accepted narration:

> The bronze bell's wooden yoke is split, and its leather hanger torn. This damage could suggest gradual wear from frequent use or recent stress that strained these components, though exactly when or how this happened remains unclear.

Patterns the validator rewarded:

- observations first
- “could suggest” (`_QUALIFIED_INFERENCE_RE` and `_UNCERTAIN_FRAME_RE`)
- a single possibility, still historically colored
- “remains unclear”, which matches `_UNKNOWN_SLOT_RE` (`is|remains` + `unclear`) and therefore skips the ungrounded-definite lead check

The declaration matched the narration’s modality: “could indicate gradual wear or recent damage under strain,” with premise ids on the two observations.

P3 accepted narration:

> The bell's wooden yoke is indeed split, and its leather hanger torn. However, whether these damages were caused deliberately is uncertain from the visible evidence alone.

Patterns:

- observations separated from the explanation
- “whether” keeps the cause conditional
- “is uncertain” matches `_EPISTEMIC_PARENT_REALIZATION_RE`
- no certainty adverb
- no actor noun, so `_ACTOR_ATTRIBUTION_RE` does not fire

The prose that plausibly produced those patterns is the cluster that says to state the unknown edge, to keep the limit on what observation can settle, and not to confirm a hidden cause. The recipe’s “use could, may, or might” covers only the hedge in P1. It does not say to close the limit, and the P3 recipe does not mention the hypothesis at all.

The point of a later repair is the semantic instruction those patterns came from. Hard-coding “remains unclear” as the only legal closer would track the validator’s current bug, not the authority rule.

## H. Validator lexical-sensitivity audit

Replay used the current `game/gm_resolution_decision.py` recognizers. No recognizer was edited.

| Recognizer | Purpose | Implementation | Recognized | Equivalent forms not recognized | Contribution |
| --- | --- | --- | --- | --- | --- |
| `_UNKNOWN_SLOT_RE` | Treat an explicit unknown cause, actor, or time as non-assertion | Regex. Includes `is unclear` and `remains unclear` as a bare pair | “remains unclear”, “is unclear”, several “who/when/cause … remains unclear” frames | “is not clear”, “is not something that can be determined” | P1 retry. Also exempts an entire sentence, including causal elaboration, once it matches |
| `_EPISTEMIC_LIMIT_RE` | Authorized negative knowledge | Narrower regex: “is not established”, “cannot tell from this”, “do not know”, cause/time “remains unclear”. Fires only when the decision allows an epistemic limit or the sentence has an attributed source | Those frames | “is not clear”, “remains uncertain” | Not the P1 pass. On this P1 decision `_decision_allows_epistemic_limit` is false: `unresolved_qualifiers` is empty and there is no leave-unresolved act. The P1 pass is the unknown-slot exemption plus the qualified-inference return |
| `_EPISTEMIC_PARENT_REALIZATION_RE` | Parent uncertainty over an embedded proposition | Regex: cause/reason within 80 chars of unknown/unclear/not known/cannot be determined, or “is/remains/stays uncertain/unclear” | “is uncertain”, “remains uncertain”, “cannot be determined” | “is not clear”, “is not something that can be determined” | Helps P3’s hypothesis clause. Does not block “clearly” |
| `_CERTAINTY_UPGRADE_RE` | Block language that settles an uncertain claim | Regex including `clearly`, proves, confirms, establishes, “no doubt” | Any “clearly” | None of the tested observation uses were spared. “clearly visible” fails | P3 initial and retry. Class **VALIDATOR-ROBUSTNESS** for this token, on top of the model choosing it |
| `_QUALIFIED_INFERENCE_RE` | Accept hedged inference when the decision has an infer act | might, may, could, perhaps, maybe, possibility, suggests, points to | “could suggest”, “might” | A hedge without those tokens | P1 path. Not sufficient alone |
| `_unsupported_narrator_lead` | Reject hedged leads and ungrounded definites | Returns false on unknown-slot. Otherwise, if might/could/uncertain-frame, rejects specific leads, generated leads, or any ungrounded definite token of length ≥ 5 | The PR-BT P1 sentences | A sentence with the same content plus “remains unclear” | P1. The label says “lead”. The trigger on these sentences is the definite-token check |
| `_CAUSAL_RELATION_RE` | Causal relations need decision coverage | Includes “leading to” | “leading to” in the P1 initial sentence | Reported only when the unknown-slot exemption and the qualified-inference return do not hide it | Present in P1 initial, not the stored reason |
| `_ACTOR_ATTRIBUTION_RE` | Actor fills | “someone … cut” within 80 characters | “someone cut it deliberately” | “whether these damages were caused deliberately” | Would reject a closer paraphrase of the player’s own hypothesis. PR-BS and PR-BT narrations avoided it |

Classification of the live failures:

| Generation | Class | Why |
| --- | --- | --- |
| P1 initial | BOTH | The model added ringing, exposure, and a causal chain. The validator would still accept that chain if the sentence ended in “remains unclear”, and it rejected the sentence it got through the definite-token lead rule. |
| P1 retry | VALIDATOR-ROBUSTNESS | Strain plus “cause or history is not clear” is the authorized epistemic act. “is not clear” is not recognized. Substituting “remains unclear” passes. |
| P3 initial | BOTH | The hypothesis handling is the authorized shape. The model added “clearly”. The validator treats that token as a certainty upgrade even for “clearly visible” on an established fact. |
| P3 retry | BOTH | Same split. The limit clause got more awkward (“is not something that can be determined”) and “clearly” remained. |

“the exact cause” did not introduce a lead by itself.

## I. Answer-recipe sufficiency

The recipe tells the model what epistemic act is allowed. It does not tell the model how that act has to read to the narration validator.

P1 recipe content that is present: one qualified possibility, could/may/might, tied to the two observations, modality possible. Missing operational behavior: separate the observation from the possibility; leave cause, actor, time, and history explicitly unresolved; do not add a mechanism, setting, or “leading to” chain; do not use certainty adverbs. The recipe lists those upgrades as forbidden ids (`exact_cause`, `history`, `harsh_conditions`, `certainty_upgrade_to_established`). It does not say what the narration should sound like when it respects them.

P3 recipe content that is present: realize the two claims; inference not permitted; “No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.” Missing operational behavior: the player still asked whether a deliberate cut fits, and the successful answer says the visible facts do not settle that. The recipe’s premise line tells the model the hypothesis is not authorized. It does not tell the model to answer the question by leaving the hypothesis unresolved, and it does not ban “clearly”.

The recipe should not be the owner of this protocol in the next slice. It is turn-specific, it was identical across the successful and failed gates, and the P3 recipe currently points away from the answer that passed. Stable system guidance already contains the sentence that replaced the old uncertainty rule. That sentence is the owner to rewrite. `response_policy` already owns the booleans (`forbid_hidden_fact_assertions`, `bounded_uncertainty`, `known_edge` / `unknown_edge`) and those booleans were not enough once the prose bridge was removed.

## J. Authority vs linguistic protocol

Authority semantics, unchanged from PR-BS to PR-BT:

- P1 may realize two observations and one qualified possibility. Cause, actor, time, and history are not established.
- P3 may realize two observations. It may not establish a deliberate cut. The player’s hypothesis is not promoted to world truth.
- P2 may refuse in ordinary speech without inventing a durable preference.

Linguistic protocol, changed:

- PR-BS prose told the model to state the unknown edge, to keep conclusions on visible cues, and not to confirm hidden causes.
- PR-BT prose tells the model to give the strongest grounded partial and to keep the limit diegetic.
- The validator’s protocol is narrower than the authority. “remains unclear” exempts a sentence. “is not clear” does not. “clearly” upgrades a sentence. “is uncertain” is a recognized parent. “is not something that can be determined” is not the same pattern as “cannot be determined”.

The model had the authority objects on the failed turns. It lacked the short discipline that turns those objects into narration the current validator accepts, and on P1’s first pass it also spent that freedom on a causal history. Both sentences are true. The missing piece is not a restoration of the architecture explanation.

## K. Candidate restoration families

These three overlap. Implementing all three as separate essays would double-count. The recommended text is their union, 651 characters, not the sum.

### 1. Epistemic realization protocol (recommended)

- Purpose: one observation-tied possibility or one unresolved hypothesis answer, with an explicit limit and no certainty wording.
- PR-BS source: narrative-authority instruction (554), fallback known/unknown edge (inside 459), narrator-anchor and world-facing limit lines (163+165), system “state uncertainty” sentence, direct-question uncertainty line (300). Operational subset on the order of 2,000 characters, sitting inside a larger deletion.
- Compact form: the 651-character `EPISTEMIC REALIZATION` paragraph in `PR-BT_epistemic_guidance_delta.json`.
- P1 relevance high. P3 relevance high. P2 impact low if the paragraph is scoped to interpretation and player hypotheses.
- Architectural risk low. It does not grant authority. Quality risk low to moderate: inference turns may sound closer to the PR-BS formula. Expected retained savings: about 15,530 of the 16,181 removed guidance characters.

### 2. Inference-scope ceiling alone

- Purpose: ban mechanisms, settings, maintenance history, and causal chains on an interpretation.
- Compact cost about 220 characters.
- P1 relevant. P3 does not need it. It would not have removed “clearly” from P3. Ranked second because it is incomplete.

### 3. Hypothesis non-promotion and certainty ceiling alone

- Purpose: leave the player’s explanation unresolved and ban certainty wording on that sentence.
- Compact cost about 180 characters.
- P3 relevant. It would not have stopped P1’s ringing / elements / “leading to” sentence unless the model also learned the scope ceiling. Ranked third as a standalone.

Do not restore the 3,939-character narrative-plan essays or the rest of the 5,644-character policy tail.

## L. Recommended minimum repair

Rewrite the system-prompt sentence that currently says to give the strongest grounded partial answer and keep the limit diegetic. Replace it with the 651-character epistemic realization paragraph. Leave the following sentence, that player hypotheses remain hypothetical, if it is not already covered by the new paragraph; do not stack a second essay.

Owner: `SYSTEM_PROMPT` in `game/gm.py`.

Why that owner: it is on every realization call, it is the sentence PR-BT substituted for the old uncertainty rule, and “strongest” is the pressure that lines up with “significant”, “leading to”, and “clearly”. The recipe was not the deleted text. The policy JSON was not the deleted text. A turn-specific recipe edit would miss P3, whose recipe does not describe hypothesis answers.

Keep deleted: narrative-plan field essays, answer-completeness essays, anti-railroading essays, context-separation essays, purity essays, tone essays, perception examples, NPC-contract essays, and scene-momentum essays.

Provider-size effect: about +651 characters on the system prompt, on the order of +150 input tokens per realization call at the PR-BS ratio of about 4.4 characters per input token. P1’s measured cut was 3,359 tokens. A 150-token giveback leaves about 3,200 tokens of that cut.

Deterministic tests and the later live comparison are in sections N and O. This document does not implement the paragraph.

## M. Estimated provider cost

| Quantity | Value |
| --- | --- |
| Guidance characters removed on P1 (system net + instruction net) | 16,181 |
| Characters to put back | 651 |
| Characters that stay removed | about 15,530 (about 96% of the cut) |
| P1 initial input tokens, PR-BS to PR-BT | 25,208 to 21,849 (−3,359, −13.3%) |
| Estimated tokens given back | about 150 per initial realization call |
| Estimated initial-token reduction that remains | about 3,200 per comparable call, near 12% rather than 12.9% on the three-probe average |

The token figure is a character-ratio estimate from the PR-BS P1 request (110,450 characters / 25,208 tokens). It is not a new provider measurement.

## N. Deterministic validation plan

No live call.

1. Build the P1, P2, and P3 provider requests with the new system sentence. Assert the 651-character paragraph is present once. Assert the narrative-plan field essays and the long policy-tail paragraphs are still absent. Assert `response_policy`, the recipe, and the decision objects are unchanged.
2. Assert system-prompt growth is the new paragraph minus the replaced “strongest grounded partial” sentence, and that P1 system-plus-instructions remains at least about 14,000 characters under the PR-BS total.
3. Replay fixtures through the current validator, without editing it:
   - PR-BS P1 and P3 narrations still hard-valid
   - PR-BT P2 narration still hard-valid
   - a narration that follows the new protocol (observations, one could/might possibility, explicit unresolved cause/history, no “clearly”) hard-valid on the P1 decision
   - the PR-BT P1 initial narration, unchanged, still fails
   - the PR-BT P3 narrations, unchanged, still fail
4. Record, and do not “fix” by synonym lists in this slice, the known lexical fixtures: P1 retry with “is not clear” fails; the same sentence with “remains unclear” passes; “clearly visible” fails.
5. P2 fixture: a refusal with mannerism still passes, and the new paragraph does not require a bell-style epistemic closer on dialogue.

## O. Later live-validation plan

Do not run it in this block.

Smallest useful comparison: the same three probes, the same model `gpt-4.1-mini-2025-04-14`, one initial generation each, retries only if the existing gate retries. Report first-pass acceptance, the player-facing text, validator reason codes, and initial input tokens against the PR-BS and PR-BT tables in this document. Success for the guidance slice is P1 and P3 first-pass acceptance at the PR-BS quality band, P2 still first-pass, and initial input still well below the PR-BS token counts. No other provider-size work in that run.

## P. Retry observations

Record only. Retry is not redesigned here.

P1 retry failed because the new sentence used “might” and “is not clear”. The validator does not treat “is not clear” as an epistemic limit, so the hedged definite phrases were an unsupported lead. The semantic content was an allowed qualified strain plus an explicit unsettled cause and history.

P3 retry failed because “clearly” was still in the observation clause. The hypothesis clause still refused to settle a deliberate cause.

After the second failure, `immutable_valid_response` maps `unauthorized_resolution_decision_fact` to `authorized_observation_line`. That function returns the established world-truth sentences. Both turns therefore sealed as: “The bell's wooden yoke is split. The bell's leather hanger is torn.” Provenance on the digests is the safe non-resolution path with acceptance reason `authorized_observation`.

Retry feedback named `unauthorized_resolution_decision_fact` and said the narration contained consequential facts the decision did not authorize. It told the model to answer again from established facts, bounded incidental detail, or qualified NPC belief, and not to invent routes, orders, evidence, rosters, or movement. It said to repair only the rejected sentence. It did not name “clearly”, “is not clear”, the still-authorized observations, or a positive pattern such as one hedged possibility plus an explicit unresolved cause. The P3 retry repeated “clearly”. The P1 retry moved toward a limit and missed the recognized wording.

PR-BS had zero retries. Restoring first-pass competence is the slice that removes this cost. Retry feedback can be a later core-engine slice if first-pass repair leaves residual failures.

## Q. Architecture status

**A — PR-BR REMAINS CLOSED**

The resolution contract, the GM resolution decision, the recipe, the response policy, and the declaration schema did not change between the successful and failed gates. No new contradiction among authority, provenance, and state integrity showed up. The live quality drop tracks provider prose and the existing narration recognizers.

## Decision taxonomy

**C — BOTH GUIDANCE AND VALIDATOR NEED ATTENTION**

The model genuinely overreached on the P1 initial narration, and validator lexical sensitivity is what rejected the P1 retry and both P3 generations. Address guidance first. The successful PR-BS gate already satisfied this validator, and the only model-facing change was the prose deletion. A validator change that accepted “is not clear” or ignored “clearly visible” would not have supplied the scope ceiling the P1 initial narration needed, and a validator change that accepted the initial narration as written would also accept the ringing / elements / “leading to” sentence whenever it contains “remains unclear”. That second fix is real, and it is the follow-on investigation, not the first implementation.

Machine-readable family table: `PR-BT_epistemic_guidance_delta.json`.
