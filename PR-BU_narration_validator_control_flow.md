# PR-BU narration validator control flow

Production function: `audit_narrated_claims` in `game/gm_resolution_decision.py`.

This is the control flow the code executes. It is not a target design.

The unit of audit is one sentence from `_sentences`. `_clauses` exists and is used by `_negation_scopes_over`. `audit_narrated_claims` does not split a sentence on `but`, commas, or `perhaps`.

`classify_narrated_fact` rejects the sentence if any returned claim has `authorized` false. A terminal return that still carries an earlier unauthorized claim therefore rejects. A terminal return that carries only authorized claims accepts, and every later check is skipped.

`audit_realization_envelope_against_decision` validates declarations first. Accepted declarations are copied into `proposed_facts` by `_decision_with_accepted_declarations` before the narration audit. That copy is part of the narration ground.

The narration audit does not read `forbidden_upgrades`, `narration_constraints`, or the answer recipe.

## Branch order

1. **Attributed uncertain claim.** If `_is_claim_or_uncertain` and `_attributed_epistemic_source`, return one authorized `epistemically_qualified` claim. Terminal.

2. **Authorized epistemic limit.** If `_authorized_epistemic_limit`, append `authorized_epistemic_limit` and return. Terminal. This requires `_EPISTEMIC_LIMIT_RE` plus either unresolved qualifiers, a `leave_unresolved` act, or an attributed source.

3. **Unsupported narrator lead.** If `_unsupported_narrator_lead`, append an unauthorized `unsupported_narrator_lead` claim. Not terminal. Processing continues.

4. **Authorized qualified inference.** If the decision has an `infer` act, `_QUALIFIED_INFERENCE_RE` matches, and neither lead regex matches, append `authorized_qualified_inference` and return. Terminal. Cause, history, evidential, certainty, slot-fill, and consequential checks below this line do not run.

5. **Explicit non-assertion.** If `_NONASSERTION_FRAME_RE`, append an authorized non-assertion and return. Terminal.

6. **Interrogative.** If the sentence ends in `?` and the early slot list has no location fill, append an authorized interrogative claim and return. Terminal.

7. **Unknown slot.** If `_UNKNOWN_SLOT_RE`, append an authorized `unknown_cause_actor_or_time` claim. Not terminal.

8. **Relationship residuals.** `_relationship_residual_claims` may append unauthorized causal, evidential, or certainty claims. Not terminal. This helper returns nothing when `_UNKNOWN_SLOT_RE` or `_authorized_epistemic_limit` matches.

9. **Slot fill.** `_slot_fill_reasons` may append `unauthorized_qualifier:actor|time|cause|location`. Not terminal. The helper returns nothing when `unresolved_qualifiers` is empty, and also when `epistemic_frame` is `uncertain`, `speculative`, `rumor`, or `hearsay`.

10. **Answer-relation, departure-exit, and structured semantic rejection.** Each may append an unauthorized claim. Not terminal.

11. **Negative evidence.** May append `unauthorized_negative_evidence`. Not terminal.

12. **Consequential tail.** Domain patterns, ordinary residuals, structured consequential reasons, movement, group-place, residue, and definite-history. An epistemic-parent match suppresses proposition-authority and structured-consequential reasons. If any covered authorized row exists and no claim so far is unauthorized, three residual codes are dropped: `unowned_stateful_world_assertion`, `proposition_authority`, `unauthorized_consequential_residual`.

13. **Legacy fallback.** If the claim list is still empty, `_classify_narrated_fact_legacy` may add one claim. If that also returns nothing, the sentence produces no claim. `audit_narration_against_decision` then records no violation. Omission is acceptance.

## Early returns that matter here

| Gate | Terminal | What it skips |
| --- | --- | --- |
| `authorized_epistemic_limit` | yes | lead, inference, cause, history, certainty |
| `authorized_qualified_inference` | yes | non-assertion, unknown-slot append, relationship residuals, slot fill, certainty, history, consequential tail |
| `_UNKNOWN_SLOT_RE` inside `_unsupported_narrator_lead` | yes, for the lead function only | the ungrounded-definite test in that same function |
| `_UNKNOWN_SLOT_RE` inside `_relationship_residual_claims` | yes, for that helper | causal, evidential, and certainty residuals |
| uncertain `epistemic_frame` inside `_slot_fill_reasons` | yes, for that helper | actor, time, and cause slot fills |

`_decision_allows_inference` is true when any epistemic act is `infer`. It does not read `scope: qualified_possibilities_only`.

## `_unsupported_narrator_lead`

1. If `_UNKNOWN_SLOT_RE` matches, return false. The rest of the function does not run.
2. If the sentence has an attributed epistemic source, return false.
3. If neither `_NARRATOR_MODAL_RE` nor `_UNCERTAIN_FRAME_RE` matches, return false. `could` and `might` match the uncertain frame. `could` alone does not match the narrator-modal pattern, which requires `you`/`one` plus a modal, or `perhaps`/`maybe`.
4. Specific-lead and generated-lead patterns can return true.
5. Otherwise return `_has_ungrounded_definite`.

`_has_ungrounded_definite` takes each `the`/`this`/`that` span of up to six words. A span is ungrounded only when every content token of length 5 or more is absent from the ground. One in-ground token grounds the whole span. The ground is the authored corpus plus every `proposed_facts` text, including accepted declarations merged on the envelope path. `these` is not a definite determiner. `_EPISTEMIC_FRAME_NOUNS` (`damage`, `condition`, `observation`) is not consulted here.

The lead function does not call `_EPISTEMIC_PARENT_REALIZATION_RE` or `_EPISTEMIC_LIMIT_RE`.

## Shared concept, three patterns

Uncertainty about a cause, actor, time, or explanation is implemented three times:

| Helper | `remains unclear` | `remains uncertain` | `cannot be determined` | `cannot be established` |
| --- | --- | --- | --- | --- |
| `_UNKNOWN_SLOT_RE` | matches | no | no | no |
| `_EPISTEMIC_LIMIT_RE` | matches when the subject is cause/actor/time/timing/sequence/explanation | no (`uncertain` is absent) | no | no (`not established` does not match `cannot be established`) |
| `_EPISTEMIC_PARENT_REALIZATION_RE` | matches | matches | matches | matches |

`_CERTAINTY_UPGRADE_RE` matches `clearly` and `establish(es/ed)`. It has no negation test. `_negation_scopes_over` is not called on certainty keywords.

`suggest` / `indicate` / `point to` are in both `_QUALIFIED_INFERENCE_RE` and `_EVIDENTIAL_RELATION_RE`. The inference return treats them as permission. The relationship residual, if reached, treats them as `unauthorized_evidential_relation`.

`_CAUSE_FILL_RE` and `_CAUSAL_RELATION_RE` both match `due to`, `because`, `caused by`, and `as a result of`. They do not match `from` or `possibly from`. Neither pattern names `neglect`.

## P1 path

Production call: `audit_realization_envelope_against_decision`.

The declaration is accepted by `_proposal_is_bounded_inference` before narration. That helper checks inference permission, relation kind, negative evidence, specific leads, and modality rank. It does not run cause, history, or definite-ground checks. The accepted text is then a proposed fact.

Narration sentence, after that merge:

1. Not an attributed claim.
2. Not an epistemic-limit sentence.
3. Lead check is false. The definite span `This damage might suggest the bell has` contains `might`, and `might` is now in the ground because the declaration says `might indicate`.
4. Inference is allowed. `might` matches. Lead regexes do not. Append `authorized_qualified_inference` and return.

Not reached: `_relationship_residual_claims`, which matches `due to` as `unauthorized_causal_relation` and `suggest` as `unauthorized_evidential_relation`. Also not reached: slot fill. Slot fill would still return nothing on this sentence, because `epistemic_frame` is `uncertain`, even if `unresolved_qualifiers` were copied from the recipe.

On the saved decision before the merge, step 3 is true instead: `damage`, `might`, and `suggest` are all out of the ground, so the lead claim is appended, then step 4 still returns. `classify_narrated_fact` rejects because the lead claim is unauthorized. The cause residual is still not the reason for that rejection.

## P3 path

The perceive decision has no `infer` act. `unresolved_qualifiers` is empty.

Narration sentence `...could be consistent with being deliberately cut, but ... that motive remains uncertain.`:

1. Not an attributed claim. `could` is not an attributed source.
2. Not an epistemic limit. `remains uncertain` is outside `_EPISTEMIC_LIMIT_RE`.
3. Lead check is true. `_UNKNOWN_SLOT_RE` does not match. `_UNCERTAIN_FRAME_RE` matches `could`. The span `that motive remains uncertain` has no in-ground content token. Append `unsupported_narrator_lead`.
4. Inference return does not run. The decision does not allow inference.
5. Unknown-slot append does not run.
6. Relationship residuals do not run their patterns in a way that adds claims. `_relationship_residual_claims` is not blocked by the parent match. This sentence simply does not match cause, evidential, or certainty patterns. `cut` matches `_DEFINITE_HISTORY_RE` and `_STATEFUL_ASSERTION_RE`, and both later tails are suppressed because the sentence is uncertain or, for structured consequential reasons, because `_is_claim_or_uncertain` is true.
7. The only unauthorized claim is `unsupported_narrator_lead`.

`_EPISTEMIC_PARENT_REALIZATION_RE` does match `remains uncertain`. Nothing in this path consults it.

The same sentence with `remains unclear` exits the lead function at step 3's first line. `motive` is never tested. The unknown-slot append then authorizes the sentence as `unknown_cause_actor_or_time`.

The accepted retry sentence contains `cannot be determined` and `are clear`. It matches the parent recognizer, not the unknown-slot recognizer, not the lead opener, and not `clearly`. No claim is emitted. The audit accepts it by omission.
