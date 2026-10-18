# PR-BU validator semantic robustness discovery

MODE: FORENSIC DISCOVERY / ROOT-CAUSE ANALYSIS ONLY

MODEL/API CALLS: ZERO

PRODUCTION CHANGES: NONE

PR-BT: PAUSED

PR-BR: REMAINS CLOSED

DECISION: **D — CLAIM-COMPOSITION REPAIR NEEDED**

Diagnostic sample: 41 zero-call cases against the saved P1 and P3 decisions. 13 correct accepts, 14 correct rejects, 9 false accepts, 5 false rejects, 0 ambiguous. Nine of the accepts are accept-by-omission: the sentence produced no claim, and the narration audit records no violation. This is a targeted sample, not a product metric.

## A. Executive finding

P1 and P3 are not two isolated bugs. They are two outcomes of one composition: `audit_narrated_claims` lets one epistemic match finish a sentence, and the helpers that share an epistemic concept do not share a vocabulary.

P1 should not have passed. On the production envelope path the accepted declaration puts the word `might` into the definite-phrase ground, so the lead check does not see `damage`. `authorized_qualified_inference` then returns. The causal residual that matches `due to` never runs. Prolonged neglect, heavy use, and an external force are not inspected as their own claims.

P3 should not have failed as `unsupported_narrator_lead`. `could` opens that check. `remains uncertain` does not take the unknown-slot exemption, even though `_EPISTEMIC_PARENT_REALIZATION_RE` matches it. `that motive` is an ungrounded definite, so the whole sentence is rejected. The same sentence with `remains unclear` is accepted, including `motive`. A conditional fit with no new motive noun is rejected for `remains uncertain` and `is uncertain`, and accepted for `remains unclear` and `is unclear`.

The smallest robust repair is compositional. An epistemic match may record the status of its own clause. It must not accept or exempt the rest of the sentence. A licensed hedge must not be reclassified as evidential establishment, and it must not hide a cause, history, actor, time, or ungrounded noun. `uncertain` and `unclear` have to enter that exemption through one predicate. Adding `remains uncertain` to one regex, or deleting the inference return without that split, would move the errors rather than close them.

## B. P1 exact reconstruction

Source: `artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/evidence/P1/`.

Player request, from `resolution_contract.json`:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Scene facts: `The bell's wooden yoke is split.` `The bell's leather hanger is torn.` Location: Chapel belfry. Contract operation `inspect`, dimension `interpretation`, contract `rc_3f400a77512d`.

Decision `epistemic_acts`: `establish` for each visible fact, plus `infer` with `scope: qualified_possibilities_only`, subject `chapel bell`. `unresolved_qualifiers` is `[]`. `answer_relations` is `[]`. Realization claims are only the two authored observations. Constraint text includes: "Qualified possibilities may be inferred from authorized observations; no cause, actor, or history is established."

The answer recipe projects that infer act into `permitted_inference.allowed: true` and adds `cause`, `actor`, `time`, `history`, and `neglect` to guidance. The narration validator does not read the recipe or `narration_constraints`.

Declaration, accepted:

> The split wooden yoke and torn leather hanger might indicate the bell has been under significant stress or neglect, possibly from heavy use or an external force.

`validate_declared_claims_against_decision` returns `hard_valid: true`, reason `accepted_bounded_declared_inference`. `_proposal_is_bounded_inference` does not scan for cause or history wording. `possibly from` matches neither `_CAUSE_FILL_RE` nor `_CAUSAL_RELATION_RE`.

Narration, accepted on attempt 1, no retry:

> The bell's wooden yoke is visibly split, and its leather hanger is torn. This damage might suggest the bell has been subjected to significant stress or prolonged neglect, perhaps due to heavy use or an external force acting upon it.

Narration validation `hard_valid: true`. The second sentence's only claim is `authorized_qualified_inference`, provenance `gm_inference`, epistemic status `inferred`, persistence `do_not_persist`.

Reproduced in this discovery with zero model calls. `audit_realization_envelope_against_decision` on the saved decision and that envelope is `hard_valid: true`.

State effect, from `state_after.json`: `visible_facts` stay the two authored sentences. Both the declaration and the narration sentence are stored in `temporal.gm_inferences`. The active claim label is the declaration, which names neglect, heavy use, and an external force. They were stored as inference, not as world truth.

### Decision trace for the second sentence

Production ground: authored corpus plus the merged declaration.

| Step | Helper | Match | Branch | Continues |
| --- | --- | --- | --- | --- |
| 1 | attributed uncertain claim | `might` is uncertain; no speaker or quote | not taken | yes |
| 2 | `_authorized_epistemic_limit` | `_EPISTEMIC_LIMIT_RE` does not match | not taken | yes |
| 3 | `_unsupported_narrator_lead` | uncertain frame matches `might`; definite span `This damage might suggest the bell has` is treated as grounded because `might` is in the declaration | false, no claim appended | yes |
| 4 | qualified inference | infer act present; `might` matches; lead regexes do not | **return** `authorized_qualified_inference` | no |

Skipped residuals, measured by calling them on the same sentence and the merged decision:

- `_CAUSE_FILL_RE` matches `due to`
- `_CAUSAL_RELATION_RE` matches `due to`
- `_EVIDENTIAL_RELATION_RE` matches `suggest`
- `_DEFINITE_HISTORY_RE` matches `has been`
- `_relationship_residual_claims` would append `unauthorized_causal_relation` and `unauthorized_evidential_relation`
- `_slot_fill_reasons` returns `[]` even after `cause`/`actor`/`time`/`history` are written onto `unresolved_qualifiers`, because `epistemic_frame` is `uncertain` and that helper returns before the cause regex

Before the declaration merge, step 3 is different. `damage`, `might`, and `suggest` are all absent from the ground, so an unauthorized `unsupported_narrator_lead` claim is appended, and step 4 still returns. Classification rejects because of the lead claim. The cause residual is still skipped. The live accept is the merged path, not this one.

The first narration sentence, `The bell's wooden yoke is visibly split, and its leather hanger is torn.`, produces no claim. Empty-identity coverage allows at most one extra content word, and the conjoined sentence has more. Omission accepts it.

## C. P1 atomic claim analysis

Sentence under audit:

> This damage might suggest the bell has been subjected to significant stress or prolonged neglect, perhaps due to heavy use or an external force acting upon it.

| Claim | Source | Strength | Permitted by the infer act and the "no cause, actor, or history" constraint | What the validator did |
| --- | --- | --- | --- | --- |
| This damage refers to the split yoke and torn hanger | Deictic observation. The previous sentence states those facts. The validator does not bind the pronoun to that sentence. | Established, if bound | Yes, as observation | Not a separate claim. On the live path the span is grounded by the hedge word `might`, not by `damage`. |
| The bell has been under significant stress | Model-created possibility tied to the observation | Possible (`might`) | A qualified possibility is the act that is permitted. Stress is not a named forbidden upgrade. | Swallowed by the sentence-level inference return |
| Prolonged neglect | Model-created history. The recipe lists `neglect` and `history`. The scene does not state it. | Possible on the surface, historical in content | No | Never a separate claim. `neglect` is not a recognizer term. |
| Heavy use | Model-created history/cause after `due to` | Possible (`perhaps`) | No | Inside the `due to` span. Not reached. |
| An external force acting upon it | Model-created cause. No actor is named. | Possible (`perhaps`) | No. This is a cause fill. | `_CAUSAL_RELATION_RE` matches `due to` and is skipped by the return |
| Cause, actor, and time stay unresolved | Not said | The sentence does not preserve the limit | The constraint requires that they not be established | No unknown-slot match. The inference return does not require a limit sentence. |

The unauthorized components that escaped are prolonged neglect, heavy use, and an external force, joined by `due to`. Significant stress is the only piece that fits a qualified possibility with no causal connective. The validator accepted the mixture as one inference.

## D. P1 early-return analysis

`authorized_qualified_inference` is a terminal success path. Lines 2537–2558 of `audit_narrated_claims` append that claim and return.

A sentence can contain both a licensed hedge and an unauthorized cause. After declaration merge, the mixed sentence is accepted whole.

| Case | Text shape | Result |
| --- | --- | --- |
| Control A, `A04` | Hedge only, grounded subject, no `due to` | Accept `authorized_qualified_inference` |
| Control B, `B01` | `due to prolonged neglect`, no hedge | Reject `unauthorized_causal_relation` |
| Mixed E, `C02` / `G02` | Hedge, then `perhaps due to prolonged neglect` | **False accept.** Inference return. |
| Mixed D, `G01` | `Perhaps due to prolonged neglect`, then the hedge | **False accept.** Same return. Order does not matter. |
| Live P1, `C01` | Production sentence after declaration merge | **False accept.** |

`C01b`, the live sentence before the merge, rejects. The reason is `unsupported_narrator_lead` on the ungrounded span `this damage`, not the cause residual. That reject does not show that cause checking works.

`C04`, `The split wooden yoke might point to neglect.`, is a false accept. The subject tokens ground the definite span, `might` and `point to` license the inference return, and `neglect` has no pattern of its own.

Removing the return without a further split would also reject Control A. `suggest` is in `_QUALIFIED_INFERENCE_RE` and in `_EVIDENTIAL_RELATION_RE`. On the live sentence the skipped residual list contains both `unauthorized_causal_relation` (`due to`) and `unauthorized_evidential_relation` (`suggest`). Only the first is the unauthorized content.

The original hypothesis is confirmed for the production path, with one correction. The check that would have rejected `due to`, and that the return skips, is `_relationship_residual_claims`. It is not `_slot_fill_reasons`. Slot fill is already blind to this sentence because the hedge marks the epistemic frame uncertain, and because the saved decision's `unresolved_qualifiers` is empty. The recipe's unresolved list is not the list the validator reads.

## E. P3 exact reconstruction

Source: `artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/evidence/P3/`.

Player request:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Contract `rc_a6f3b923e680`, operation `perceive`, dimensions empty. Same two authored facts. Epistemic acts are only the two `establish` acts. No `infer` act. No player-hypothesis realization claim. `unresolved_qualifiers` is `[]`. The recipe says inference is not permitted and that no player hypothesis is authorized on the turn. That line is what the recipe prints when the decision has no epistemic claim rows. The player's `maybe` is not copied onto the decision before narration. `player_hypothesis_claims` records it later, from the player text, because `_PLAYER_HYPOTHESIS_RE` matches `maybe`.

Initial narration, rejected:

> The bell's wooden yoke is indeed split, and its leather hanger is torn. These visible damages could be consistent with being deliberately cut, but without additional evidence, that motive remains uncertain.

Declarations for the two observations were accepted. Narration validation `hard_valid: false`, reason `unsupported_narrator_lead` on the second sentence only. No retry was required for the observations. The turn retried. The accepted retry was:

> The bell's wooden yoke is split, and its leather hanger is torn. These damages are clear, but whether they were made deliberately cannot be determined from what is visible here.

Reproduced: the initial second sentence rejects with `unsupported_narrator_lead`. The retry narration audit is `hard_valid: true`. The retry's second sentence emits no claim.

State effect: `gm_inferences` stays empty. The player sentence is stored as `player_hypothesis`. The rejected sentence is stored in `rejected_consequential` with `unsupported_narrator_lead`. `visible_facts` are unchanged. No deliberate-cutting fact was persisted.

### Decision trace

| Step | Helper | Match | Branch | Continues |
| --- | --- | --- | --- | --- |
| 1 | attributed claim | `could` is not a speaker, quote, or hearsay verb | not taken | yes |
| 2 | epistemic limit | `remains uncertain` is not in `_EPISTEMIC_LIMIT_RE` | not taken | yes |
| 3 | `_unsupported_narrator_lead` | unknown-slot does not match; uncertain frame matches `could`; span `that motive remains uncertain` has `motive`, `remains`, and `uncertain` all out of the ground | append unauthorized `unsupported_narrator_lead` | yes |
| 4 | qualified inference | decision does not allow inference | not taken | yes |
| 5 | non-assertion, interrogative | no | not taken | yes |
| 6 | unknown-slot append | no | not taken | yes |
| 7 | relationship residuals | no cause, evidential, or certainty match. Parent match does not exempt or trigger this helper. | no claim | yes |
| 8 | later tails | `cut` matches history and stateful patterns; both are suppressed because the sentence is uncertain | no further claim | end |

`_EPISTEMIC_PARENT_REALIZATION_RE` matches `remains uncertain`. The lead function never calls it. `_NARRATOR_MODAL_RE` does not match `could` without `you` or `one`. The uncertain-frame regex is what opens the lead check.

The rejection is the ungrounded definite `that motive`, reached only because `could` opened the check and `remains uncertain` did not close it.

## F. P3 uncertainty-variant analysis

Semantic proposition held constant: the split yoke and torn hanger could be consistent with deliberate cutting, and that conclusion is not settled. Authority object: the saved P3 decision.

| Surface | Unknown slot | Parent | Certainty | Lead | Result |
| --- | --- | --- | --- | --- | --- |
| `the explanation remains unclear` (`D03`) | `remains unclear` | `remains unclear` | no | no | Accept `unknown_cause_actor_or_time` |
| `the explanation is unclear` (`D04`) | `is unclear` | `is unclear` | no | no | Accept, same code |
| `the explanation remains uncertain` (`D02`) | no | `remains uncertain` | no | yes | **False reject** `unsupported_narrator_lead` |
| `the explanation is uncertain` (`D05`) | no | `is uncertain` | no | yes | **False reject** `unsupported_narrator_lead` |
| `cannot be determined` (`D06`) | no | `cannot be determined` | no | no | Accept by omission |
| `cannot be established` (`D07`) | no | `cannot be established` | `established` | no | **False reject** `unauthorized_certainty_upgrade` and `unauthorized_evidential_relation` |
| `might be consistent with` (`D08`) | no | no | no | no | Accept by omission |
| `may fit` (`D09`) | no | no | no | no | Accept by omission |
| `is possible` / `not rule it out` (`D10`) | no | no | no | no | Accept by omission |
| live sentence, `remains uncertain` plus `motive` (`D01`) | no | `remains uncertain` | no | yes | Reject `unsupported_narrator_lead` |
| live sentence with only `unclear` swapped in (`H01`) | `remains unclear` | `remains unclear` | no | no | **False accept**, including `motive` |

Certainty strengtheners on the same cutting proposition:

| Surface | Result | Why |
| --- | --- | --- |
| `clearly comes from deliberate cutting` (`E01`) | Reject `unauthorized_certainty_upgrade` | `clearly` is in `_CERTAINTY_UPGRADE_RE` |
| `definitely cut` (`E02`) | Reject `unowned_stateful_world_assertion` | `definitely` is not a certainty term. `cut` is stateful, and this sentence has no hedge, so the uncertain-frame suppression does not apply. |
| `certainly cut` (`E03`) | Same stateful reject | `certainly` is not in the certainty regex |
| `obviously cut` (`E04`) | Same stateful reject | `obviously` is not in the certainty regex |

`clearly` is enforced. `definitely`, `certainly`, and `obviously` are not certainty terms. They rejected here only because `cut` is a stateful verb.

The live P3 outcome is not a principled rejection of `motive`. `H01` keeps `motive` and changes one word to `unclear`, and the sentence passes. `D02` removes `motive` and keeps `uncertain`, and the sentence fails. The exemption, not the noun, decides.

The conditional clause itself should pass when it stays unresolved and adds no new noun. `D02` and `D05` are the false rejects of that clause. `D01` rejects a sentence that also contains an unauthorized noun, but it does so through a synonym the sibling recognizer already understands, and the synonym swap accepts the noun.

## G. Cross-recognizer vocabulary map

| Helper | Purpose | What it recognizes | Normalization | Shared utility |
| --- | --- | --- | --- | --- |
| `_QUALIFIED_INFERENCE_RE` | Licensed hedge | `might`, `may`, `could`, `perhaps`, `maybe`, `possibility`, `cannot rule out`, `suggest`, `point to` | case insensitive; no negation | no |
| `_UNCERTAIN_FRAME_RE` | Opens lead and marks a sentence uncertain | the inference modals plus `not sure`, `not certain`, hearsay verbs, `speculation`, `guess` | case insensitive | no |
| `_NARRATOR_MODAL_RE` | Narrator-shaped hedge inside the lead check | `you/one might|could|may`, `perhaps`, `maybe` | `could` alone does not match | no |
| `_UNKNOWN_SLOT_RE` | Exempts and authorizes unresolved cause/actor/time | `unclear`, `unknown`, `unsettled`, `not established`, `not known`, `remains unclear`, `is unclear`, `cannot tell from`, `nothing establishes` | `uncertain` is absent | no |
| `_EPISTEMIC_LIMIT_RE` | Terminal authorized limit | `do not know`, `cause/explanation remains unknown/unclear/unresolved`, `not established`, `cannot tell from`, `does not establish` | `uncertain` and `cannot be determined` are absent | no |
| `_EPISTEMIC_PARENT_REALIZATION_RE` | Marks an epistemic parent so some later tails stand down | `unknown`, `unresolved`, `uncertain`, `unclear`, `cannot be determined`, `cannot be established`, `is/remains uncertain` | this is the list that already contains `uncertain` | not used by the lead check or the limit check |
| `_CERTAINTY_UPGRADE_RE` | Forbids certainty upgrade | `proves`, `establish`, `makes clear`, `confirms`, `demonstrates`, `no doubt`, `now we know`, `clearly` | no negation; `clear`, `definitely`, `certainly`, `obviously` are absent | no |
| `_CAUSE_FILL_RE` / `_CAUSAL_RELATION_RE` | Cause connectives | `because`, `caused by`, `due to`, `as a result of`, plus a few verbs | `from` and `possibly from` do not match. `neglect` does not match. | no |
| `_DEFINITE_HISTORY_RE` | History/action stem | `was/were/had been/has been`, `cut`, `never`, `last night`, `to hide` | suppressed when the sentence is already uncertain | no |
| `_EVENT_HISTORY_ASSERTION_RE` | Specific history events | `happened overnight`, `came through`, `few hours old`, and similar | `neglect` does not match | no |
| `_ACTOR_ATTRIBUTION_RE` | Actor fill | `someone` plus `broke/cut/did/...` | `someone cracked` does not match. `cracked` is not in the verb list. | no |
| epistemic frame in `proposition_authority.py` | Hedge versus world | `_HEDGE_RE` / `_SPECULATIVE_RE` include `might`, `could`, `perhaps` | `remains uncertain` is not a hedge by itself, so `cannot be established` and `the cause is clear` stay `world_truth` | separate module |
| `_proposal_is_bounded_inference` | Declaration gate | relation kind, modality rank, lead and negative-evidence regexes | does not use the cause or history regexes | no |

Divergences that changed results:

- Helper `_EPISTEMIC_PARENT_REALIZATION_RE` understands `remains uncertain`. Helper `_UNKNOWN_SLOT_RE`, which decides the lead exemption, does not.
- Helper `_QUALIFIED_INFERENCE_RE` treats `suggest` as permission. Helper `_EVIDENTIAL_RELATION_RE` treats `suggest` as a forbidden evidential relation. The return picks the first.
- `clearly` is a certainty term. `clear` is not. `not clearly` still matches `clearly`.
- `cannot be determined` is a parent. `cannot be established` is a parent and also a certainty/evidential hit, because the pattern matches the stem `established`.

## H. Ordering and composition

Terminal accepts in `audit_narrated_claims`: attributed claim, epistemic limit, qualified inference, explicit non-assertion, interrogative.

Terminal reject of the lead function only: `_UNKNOWN_SLOT_RE` at the top of `_unsupported_narrator_lead`.

Fall-through: unknown-slot append, relationship residuals, slot fill, semantic rejection, consequential tail, legacy.

One accepted property can mask an unauthorized property in the same sentence. The live P1 sentence is the case. `G01` and `G02` show that putting the cause first or second does not change the accept.

One lexical trigger can override an otherwise matching epistemic structure. `H01` shows `remains unclear` exempting `motive`. `F04`, `It clearly could be neglect.`, shows `could` taking the inference return and skipping `clearly`. The certainty regex does match `clearly` on that sentence. The return happens first. On a decision with no infer act, `E01` rejects `clearly`.

`classify_narrated_fact` does not let an authorized claim erase an unauthorized claim that was appended earlier. `C01b` rejects because the lead claim is still in the list when inference returns. The mask happens when the earlier check returns false, not when a later authorized claim deletes it.

## I. Claim granularity

The validator reasons over a sentence, then over a handful of keyword spans inside that sentence. It does not extract atomic propositions. It does not use `_clauses` on this path. Declarations are a separate earlier pass, and an accepted declaration is then one more sentence-level fact in the ground.

P1 is a granularity failure. One sentence contains an observation deictic, a qualified possibility, a history noun, and a cause connective. It receives one classification.

P3 is the same unit. The compatibility clause and the `motive` clause are not judged separately. Whichever sentence-level gate fires first assigns the only code.

`covered_rows` can authorize a sentence by lexical overlap with an empty semantic identity. That overlap allows at most one extra content word. It did not cover the live P1 inference sentence. The inference return did not need it.

## J. Negation and scope

`_negation_scopes_over` applies to identity values inside a clause. Certainty detection does not call it.

| Sentence | Result | Reading |
| --- | --- | --- |
| `The cause is clear.` (`F02`) | Accept by omission | `clear` is not `clearly`. No cause slot is open. False accept. |
| `The cause is not clear.` (`F01`) | Accept by omission | The outcome is tolerable. The reason is that `clear` is invisible, not that `not` was scoped. |
| `It is not clearly neglect.` (`F03`) | False reject `unauthorized_certainty_upgrade` | `clearly` matches inside the negation. |
| `It clearly could be neglect.` (`F04`) | False accept | `could` returns at inference before the certainty claim is built. |
| `There is no clear evidence of deliberate cutting.` (`F05`) | Accept by omission | `clear` is invisible, and `no evidence` is not the negative-evidence pattern used here. |
| `Deliberate cutting cannot be established.` (`F06`) | False reject | `established` matches certainty and evidential patterns. The `cannot` is ignored. |
| `Deliberate cutting remains possible but unproven.` (`F07`) | Accept by omission | No hedge opener, no certainty stem. |

Keyword certainty is interpreted without grammatical scope. The inversions that use the exact stem `clearly` or `established` go the wrong way. The inversions that use `clear` are not seen at all.

## K. Semantic invariants

These are already stated by the decision docstring, the infer-act constraint, and the existing PR-BS expectation that a grounded qualified possibility passes while an unqualified cause fails.

1. **Authorized qualified inference is permitted.** Holds for `A03` and `A04`.
2. **Qualification does not authorize a forbidden cause or history.** Fails on `C01`, `C02`, `C04`, `G01`, `G02`.
3. **A player hypothesis may be discussed conditionally without promotion.** The authority model can represent a hypothesis (`player_hypothesis`, conditional premise text). The P3 decision did not carry one into narration. The validator then treats equivalent conditional sentences differently. `D03` passes and `D02` fails. The invariant is not enforced consistently.
4. **Equivalent uncertainty should not flip the authority outcome.** Fails for `unclear` versus `uncertain`, and for `cannot be determined` versus `cannot be established`.
5. **Certainty detection must respect negation.** Fails for `not clearly` and `cannot be established`.
6. **One accepted clause does not immunize a neighbor.** Fails when the inference return or the unknown-slot exemption is terminal for the sentence.
7. **Rejected consequential content stays rejected regardless of order.** Fails. `G01` and `G02` both accept. Order is not an enforcement axis. The first terminal epistemic gate is.

The code's own docstring on `audit_narrated_claims` says authorized coverage never licenses causal, evidential, temporal, actor, history, or certainty residuals in the rest of the sentence. The inference return does not implement that sentence.

## L. Diagnostic matrix

Forty-one cases. Machine-readable copy: `PR-BU_validator_semantic_matrix.json`. Runner: `artifacts/pr_bu_validator_semantic_robustness/run_diagnostic.py`. No production function was edited. No model was called.

Authority objects are the saved P1 and P3 decisions. `C01` uses the decision after the accepted declaration is merged, which is what `audit_realization_envelope_against_decision` audits. Corpus is the belfry visible facts, summary, and location.

Expected results follow the infer-act constraint and the audit docstring: a qualified possibility passes; a cause, actor, time, history noun, ungrounded consequential noun, or certainty upgrade in the same sentence fails; equivalent unresolved wording stays accepted; negated certainty is not a certainty upgrade.

## M. Matrix results

| | Count |
| --- | --- |
| Cases | 41 |
| Correct accepts | 13 |
| Correct rejects | 14 |
| False accepts | 9 |
| False rejects | 5 |
| Ambiguous | 0 |
| Accept by omission (included in the accept tallies) | 9 |

False accepts:

- `C01` live P1 after declaration merge
- `C02`, `G01`, `G02` hedge plus `due to`, either order
- `C04` grounded `might point to neglect`
- `F04` `clearly could be neglect`, inference return first
- `H01` live P3 with `uncertain` changed to `unclear`, `motive` included
- `B04` `Someone cracked the wooden yoke.` No actor pattern contains `cracked`. No claim.
- `F02` `The cause is clear.` `clear` is not a certainty term. No claim.

False rejects:

- `D02` `remains uncertain`
- `D05` `is uncertain`
- `D07` and `F06` `cannot be established`
- `F03` `not clearly`

Correct rejects include unqualified `due to`, `last night`, `caused`, and `clearly`, plus several sentences that reject for an ungrounded definite rather than for the cause noun. `C05` (`The damage might point to neglect.`) rejects because `damage` is ungrounded, which is why the existing PR-BS test passes. `C04` is the same neglect sentence with a grounded subject, and it passes. The current test does not pin the neglect prohibition.

`C06` narrates the live declaration on the pre-merge decision and rejects it as a lead, because `the bell has been under significant stress` is an ungrounded span. The declaration validator accepted that same text. The two entry points disagree. The stored active claim is the declaration entry.

## N. Root-cause classification

Ranked by what changed the live P1 accept and the live P3 reject.

1. **C — Ordering / early-return defect.** Highest impact. The inference return skips the causal residual. The unknown-slot line inside the lead function skips the ungrounded-definite test. The uncertain frame inside slot fill skips cause fill even when the slots are populated.

2. **D — Claim-granularity defect.** Same impact, same sentences. Mixed operations are one sentence and one code. This is why C and D are one repair rather than two patches.

3. **B — Cross-recognizer vocabulary drift.** High impact on P3 and on any repair of C. `uncertain` versus `unclear`. `suggest` as permission versus `suggest` as evidential establishment. Parent versus unknown-slot versus epistemic-limit.

4. **E — Negation / scope defect.** Local, demonstrated, not the live P1/P3 wording. `not clearly` and `cannot be established` invert. `clear` versus `clearly` is the companion lexical gap.

5. **A — Local lexical gap.** `neglect` and `from` have no pattern. `someone cracked` misses `cracked`. `definitely` / `certainly` / `obviously` are absent. These matter after the composition fix. They are not sufficient to explain the live sentences: P1's `due to` is already in the cause pattern, and P3's `uncertain` is already in the parent pattern.

6. **G — Declaration ground pollution.** The merged declaration grounds a hedge token inside a six-word definite span, which disarms the lead check on the narration. `_proposal_is_bounded_inference` also accepts the neglect declaration that narration, before the merge, would reject. This is part of the composition bug, not a separate authority type.

**F — Authority-model defect** is not supported. See section O.

## O. Architecture status

PR-BR remains closed.

The decision can represent an infer act with `qualified_possibilities_only`, unresolved qualifier slots, a player hypothesis with its own provenance, and a conditional-premise constraint. P1's decision has the infer act and the constraint sentence. P3's decision has neither an infer act nor a hypothesis row. That is an empty field, not a missing kind.

What fails is enforcement. The validator does not read the infer scope, the constraint sentence, or the recipe. The recipe's unresolved list is not written back onto `unresolved_qualifiers`. The perceive builder does not attach the player's `maybe` as a hypothesis claim before narration. None of those gaps make the authority objects unable to represent "qualified possibility" versus "cause fill" versus "conditional hypothesis."

Reopening PR-BR would be justified only if those objects contradicted each other. They do not. The recipe is marked `projection_only` and names the decision as the authority owner.

## P. Repair candidates

Three. No others.

### Strategy 1 — Composition repair

Stop a sentence-level epistemic match from accepting or exempting every other operation in the sentence.

- Defects: C, D, and the P1 mask. Also the declaration entry if the same residual helper runs on proposal text.
- Scope: `audit_narrated_claims`, `_unsupported_narrator_lead`, `_relationship_residual_claims`, `_proposal_is_bounded_inference`.
- Behavior: a licensed `might`/`could`/`may` records an inference. `due to` / `because` / `caused by` in the same sentence still fail. An unknown-slot phrase records unresolved status and still leaves an ungrounded noun such as `motive` failing. `suggest` used as the hedge is not also `unauthorized_evidential_relation`.
- Regression risk: high if `suggest` is left in both lists and the return is simply deleted. Control A must stay accepted. Existing PR-BS test `USEFUL_A1` must stay accepted. Grounded `might point to neglect` should start failing. Do not edit current tests to bless the false accepts.
- Architecture impact: none. The decision objects stay as they are.
- Runtime: more regex checks on sentences that currently return early. No model call.
- Test burden: promote this 41-case matrix, especially `C01`, `C02`, `C04`, `D02`, `D03`, `H01`, `F03`, `F04`.

### Strategy 2 — Shared uncertainty predicate only

One function for `unclear` / `uncertain` / `cannot be determined` / `cannot be established`, used by the unknown-slot, limit, and parent checks.

- Defects: B, and part of E if negation is included.
- Does not fix P1. The live sentence has no uncertainty coda. The inference return would still skip `due to`.
- Makes P3 worse if `uncertain` is added to the lead exemption without removing that exemption's early return: `H01` already shows the exemption accepting `motive`.
- Use this predicate inside Strategy 1. Do not ship it alone.

### Strategy 3 — Definite-span and declaration grounding only

Do not let one in-ground token, especially a hedge copied from the model's own declaration, ground a six-word span. Run cause and history checks inside `_proposal_is_bounded_inference`.

- Defects: the live P1 disarm, and the declaration that stored neglect.
- Does not fix `C02` or `G01`/`G02`, where the subject is already grounded and the inference return accepts `due to` with no need for a polluted span.
- Does not fix `unclear` versus `uncertain`.
- Worth doing as part of Strategy 1's definite test. Not sufficient alone.

An LLM validator is not recommended. The failing distinctions are already lexical and already computed by deterministic helpers. The failure is that those helpers do not all run, and they do not share a predicate. A model call would add tokens, latency, and a second authority.

## Q. Recommended smallest repair

Strategy 1, with the shared uncertainty predicate and the hedge-versus-evidential split as parts of that same change.

Do not start by inserting `remains uncertain` into `_UNKNOWN_SLOT_RE`. Do not ban the word `neglect`. Do not special-case the two live sentences. Do not change prompts, retry, or the answer recipe in that change.

Implementation order inside the one repair:

1. Keep the inference and unknown-slot results as claims, and stop returning before residual checks.
2. Teach the residual pass that the hedge verb which licensed the inference is not itself an evidential establishment.
3. Use one uncertainty predicate so `uncertain` and `unclear` take the same status path, and so that path does not return before ungrounded nouns and cause connectives are tested.
4. Run that residual pass on bounded inference proposals so `possibly from` neglect cannot be stored as the active claim while narration is held to a stricter standard.

## R. PR-BT implications

Validator behavior currently blocks a fair PR-BT closeout.

P1's first pass was accepted and scored as a useful-looking answer while it narrated neglect, heavy use, and an external force. That accept is the composition bug, not evidence that the restored epistemic protocol held the cause boundary.

P3's first pass was a conditional fit that stayed unresolved, plus an ungrounded `motive`. It was rejected as a narrator lead. The unclear paraphrase of that sentence would have passed. The retry then dropped the conditional fit. The Q2 on the retry is not a clean reading of the initial realization.

PR-BT stays paused. Do not add prompt text back. Do not remove the selective epistemic protocol. Do not rerun the live gate in this discovery. After the validator repair and the zero-call matrix are green, a tiny live gate can reassess PR-BT.

## S. Retry implications

No retry change in this discovery.

P3's misclassified rejection is what spent the retry. The saved gate records P3 initial input 21,977 and retry input 23,241. One rejected generation became two provider calls, and the three-turn input total rose from the initial 68,463 to 91,704. A false reject at this layer is a full extra generation, not a local string fix.

The retry text was accepted by omission (`cannot be determined` emits no claim), not because a conditional-fit strategy was validated. That is cost and classification evidence only.
