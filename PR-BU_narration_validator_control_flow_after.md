# PR-BU narration validator control flow after the composition repair

Production function: `audit_narrated_claims` in `game/gm_resolution_decision.py`.

The audit unit is still one sentence from `_sentences`. This repair does not add a parser. Inside that sentence, each consequential operation is checked on its own. A licensed hedge or an unresolved-status marker records that operation and leaves the other checks running.

## Branch order

1. **Attributed uncertain claim.** If `_is_claim_or_uncertain` and `_attributed_epistemic_source`, return one authorized `epistemically_qualified` claim. Terminal. Unchanged.

2. **Authorized epistemic limit.** If `_authorized_epistemic_limit`, append `authorized_epistemic_limit`. Return only when `_hedge_does_not_authorize` is empty. A cause connective, actor attribution, history assertion, or non-negated certainty marker in the same sentence keeps validation going.

3. **Unsupported narrator lead.** If `_unsupported_narrator_lead`, append an unauthorized `unsupported_narrator_lead` claim. Not terminal. `_UNKNOWN_SLOT_RE` no longer returns before the definite test. When `_marks_unresolved_status` is true, the definite test ignores epistemic-slot subjects (`explanation`, `cause`, and the existing boilerplate), status modifiers such as `still`, and `possibility`. Other ungrounded nouns, including `motive`, still fail.

4. **Authorized qualified inference.** If the decision has an `infer` act, `_QUALIFIED_INFERENCE_RE` matches, and neither lead regex matches, append `authorized_qualified_inference`. Not terminal. Cause, history, actor, certainty, and the consequential tail still run.

5. **Explicit non-assertion.** If `_NONASSERTION_FRAME_RE`, append an authorized non-assertion and return. Terminal. Unchanged. `cannot be established` does not match this pattern (`be` sits between the words) and falls through to the negation-aware residual.

6. **Interrogative.** Unchanged. Terminal when the sentence ends in `?` and the early slot list has no location fill.

7. **Unresolved status.** If `_marks_unresolved_status`, append an authorized `unknown_cause_actor_or_time` claim. Not terminal. The predicate is `_UNKNOWN_SLOT_RE` or `_UNRESOLVED_STATUS_EQUIVALENT_RE` (`remains uncertain`, `is uncertain`, `cannot be determined`, `cannot be established`, and the `unclear` forms already in the unknown-slot pattern).

8. **Relationship residuals.** `_relationship_residual_claims` no longer returns empty because an unknown-slot or epistemic-limit phrase matched. Causal, evidential, and certainty patterns run. A match governed by `not`, `cannot`, `nothing`, or `no` is ignored. When inference is licensed, `suggest`, `point to`, and `indicate` are removed before the evidential test. They remain evidential when inference is not licensed.

9. **Slot fill, answer-relation, departure, semantic rejection, negative evidence, consequential tail, legacy fallback.** Unchanged. Slot fill still returns nothing when `epistemic_frame` is `uncertain`. Cause connectives are caught by the relationship residual, so that slot-fill exemption does not hide `due to`.

`classify_narrated_fact` still rejects the sentence when any claim is unauthorized. An authorized inference claim can sit beside an unauthorized causal claim. The sentence fails. The inference operation remains visible in `claim_results`.

## Early returns

| Gate | After this repair |
| --- | --- |
| Attributed uncertain claim | Terminal. Unchanged. |
| Authorized epistemic limit | Terminal only when no cause, actor, history, or certainty residual remains. |
| Authorized qualified inference | Append only. The old terminal return is gone. |
| `_UNKNOWN_SLOT_RE` inside `_unsupported_narrator_lead` | Gone. Unresolved status filters the status subject and still tests other definites. |
| `_UNKNOWN_SLOT_RE` inside `_relationship_residual_claims` | Gone. Cause and certainty checks run. Negated establishment is ignored. |
| Explicit non-assertion | Terminal. Unchanged. |
| Interrogative | Terminal. Unchanged. |

## Uncertainty

`_marks_unresolved_status` is the shared predicate. `remains unclear` and `remains uncertain` both record `unknown_cause_actor_or_time` and both leave an ungrounded non-slot noun unauthorized. `cannot be established` is the same status operation. The stem `established` does not become a certainty upgrade when `cannot` or `not` governs it.

## Declaration parity

`_proposal_is_bounded_inference` calls `_hedge_does_not_authorize` before accepting a propose-mode claim.

`_asserted_causal_relation` strips `a possible cause` / `likely cause` / `probable cause`, then runs the causal pattern. `Excessive strain is a possible cause` stays a qualified possibility. `possibly from`, `due to`, `because`, and `caused by` still fail. Actor attribution and history assertions fail the same way on the declaration path.

## Grounding

`_decision_ground` still includes the authored corpus and authoritative proposed facts. It omits rows whose authority is `inference` or whose provenance is `gm_inference`, `speculation`, or `generated_proposal`. A speculative declaration cannot supply the token that grounds a neighboring definite span.

The production envelope rejects the P1 declaration, so that declaration is not merged. Narration is then audited on the pre-merge decision. Forcing the speculative row into `proposed_facts` still leaves `damage` / `might` ungrounded and still rejects the cause connective.

## P1 path

Declaration text: `might indicate ... possibly from heavy use`.

1. Inference is permitted.
2. `possibly from` matches the cause connective after `possible cause` phrasing is stripped. There is no `possible cause` phrase here. The proposal is rejected with `unauthorized_causal_relation`.
3. `audit_realization_envelope_against_decision` returns on the declaration violation. Narration is not audited against a merged ground.

Narration sentence on the saved decision:

1. Not an attributed claim. Not a pure epistemic limit.
2. `damage` is ungrounded, so `unsupported_narrator_lead` is appended.
3. `might` appends `authorized_qualified_inference` and validation continues.
4. `due to` appends `unauthorized_causal_relation`. `suggest` is not also `unauthorized_evidential_relation`.
5. `classify_narrated_fact` rejects. The violation reasons include `unauthorized_causal_relation`.

Before this repair, step 3 returned, and on the merged path step 2 was false because `might` had been copied into the ground from the accepted declaration.

## P3 path

Sentence with `could` and `the explanation remains uncertain`, on the perceive decision (no infer act, empty `unresolved_qualifiers`):

1. Not an attributed claim. Epistemic limit is not authorized for this decision.
2. Shared unresolved status matches `remains uncertain`. `explanation` is a status subject, so the lead check does not fire.
3. An authorized `unknown_cause_actor_or_time` claim is appended.
4. No cause connective and no positive certainty marker. The sentence is accepted.

The same sentence with `remains unclear`, `is uncertain`, `is unclear`, `cannot be determined`, or `cannot be established` takes that status path.

The live sentence with `that motive remains uncertain` or `remains unclear` still has ungrounded `motive`. The lead claim is unauthorized. Unresolved status does not clear it.

Before this repair, `remains unclear` returned from the lead function before `motive` was tested, and `remains uncertain` did not match the unknown-slot pattern, so the same conditional was rejected as `unsupported_narrator_lead`.
