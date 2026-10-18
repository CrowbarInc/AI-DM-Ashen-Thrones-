# PR-BU qualified-inference control flow after complement authorization

Deterministic narration and declaration validation. No model call. No prompt edit.

A licensed hedge answers only: is this a qualified-inference operation?

The complement check answers the second question: is the proposition being inferred inside this decision's permitted space?

`might point to X` does not mean `X` is authorized.

## Operator recognition

`_QUALIFIED_INFERENCE_RE` still matches `might`, `may`, `could`, `perhaps`, `suggest`, `point to`, and the other existing hedge forms.

`_decision_allows_inference` is still true only when the decision has an `infer` act.

When that act's scope is `qualified_possibilities_only`, `_qualified_infer_acts` marks the explanatory ceiling as closed. Cause, actor, time, and history are not established. The hedge may still be recorded as `authorized_qualified_inference`.

`suggest`, `point to`, and `indicate` are still removed before the evidential-establishment test when inference is licensed. They are the operator. They are not scored again as `unauthorized_evidential_relation`.

## Complement identification

The complement is not a new parse tree. After the hedge matches, the validator looks for the concrete explanatory phrases the qualified-possibilities scope already refuses:

- `neglect`
- `harsh conditions`
- `safety status`
- `unseen damage`

Those phrases are the non-abstract entries of the existing `_QUALIFIED_FORBIDDEN` list. Abstract slot names (`cause`, `actor`, `time`, `history`) stay with the connective, actor, time, and history recognizers. They are not banned as bare words.

A match governed by `not`, `cannot`, `nothing`, or `no` is not a complement assertion. `might not point to neglect` does not raise the complement reason.

## Complement authorization

A matched phrase is authorized, and the reason is not raised, when any of these already on the decision or in the authored corpus carries that phrase:

- an authoritative proposed fact (`_fact_can_ground_definite`)
- the authored corpus
- a `player_hypothesis` proposed fact or realization claim
- a decision-owned `MAY_INFER` realization claim, including its semantic-identity strings

A `gm_inference` or `generated_proposal` proposed fact does not authorize the phrase. The model cannot propose `neglect` and then narrate it as licensed.

`significant stress`, `force`, and `the wood gave under a load` are not in the closed phrase list. They stay qualified possibilities.

## Residual validation

The inference branch still appends `authorized_qualified_inference` and continues.

Cause connectives, actor attribution, history-event patterns, and certainty markers still run. An unresolved-status sentence returns early only when `_hedge_does_not_authorize` is empty. That helper now includes `unauthorized_inference_complement`, so `remains uncertain` does not cover a closed complement.

The complement claim is appended with the other residuals, after the non-assertion and interrogative early returns. Its reason is `unauthorized_inference_complement`. The claim identity records `unsupported_complement`.

## Declaration equivalent

`_proposal_is_bounded_inference` calls `_hedge_does_not_authorize` before it accepts a propose-mode claim.

Hedge detection is not proposition authorization. `The split wooden yoke might point to neglect` fails the declaration. `The split wooden yoke might point to significant stress` passes it.

## Grounding interaction

`_decision_with_accepted_declarations` still copies only accepted declarations into `proposed_facts`.

The neglect declaration is rejected, so the envelope returns before narration validation. A speculative `gm_inference` fact inserted by hand still does not license the complement, and `_fact_can_ground_definite` still excludes it from definite-span ground.

## Early returns

| Gate | Complement effect |
| --- | --- |
| Epistemic-limit early return | Does not fire when the complement is unauthorized. Validation continues. |
| Qualified-inference append | Still not terminal. |
| `cannot establish` without `be` | Still returns before the complement claim is appended. Deferred. |
| Interrogative | Still returns as a non-assertion before the complement claim. |

## C04 before

`The split wooden yoke might point to neglect.`

1. The subject is grounded. The lead check does not fire.
2. `might` and `point to` append `authorized_qualified_inference`.
3. No `due to`, `because`, or `possibly from`.
4. The inference claim is authorized, so the sentence was accepted.

## C04 after

1. Steps 1–3 are unchanged. The hedge claim is still recorded.
2. `neglect` is a closed explanatory complement.
3. The P1 decision's observations, realization claims, and corpus do not carry `neglect`. There is no player hypothesis and no `MAY_INFER` permission for it.
4. The validator appends `unauthorized_inference_complement` with `unsupported_complement: neglect`.
5. Classification rejects the sentence. The hedge claim remains visible beside the unauthorized complement.

## Valid Control A

`The split yoke might suggest the wood gave under a load.`

1. `might` and `suggest` append `authorized_qualified_inference`.
2. `suggest` is not rescored as evidential establishment.
3. The complement has no closed explanatory phrase and no cause connective.
4. The sentence stays accepted.

`The split wooden yoke might point to significant stress` uses the same `might point to` frame as C04. `significant stress` is not a closed phrase, so that sentence stays accepted too.
