# PR-BU qualified-inference complement authorization

Deterministic validator repair. Model and gameplay API calls: zero. No live play. Prompts, retry, and authority generation were not modified. Nothing was committed or pushed.

## A. Executive result

C04 is fixed, and useful qualified inference still passes.

`The split wooden yoke might point to neglect` now rejects. `might point to significant stress`, Control A (`might suggest the wood gave under a load`), and `could be consistent with significant stress or force` still accept. The original 41-case matrix matches 41 / 41 expected outcomes.

## B. Exact C04 root cause

The claim-composition repair stopped treating the hedge as a terminal accept. It still treated a licensed operator as if it licensed the proposition.

`might` and `point to` match `_QUALIFIED_INFERENCE_RE`. The subject `split wooden yoke` is grounded, so the lead check does not fire. There is no `due to`, `because`, or `possibly from`, so the causal residual does not fire. `point to` is in the same licensed-hedge class as Control A's `suggest`, so it is removed before the evidential test. Nothing then asked what the inference points to.

The composition repair therefore left one false accept: a valid hedge with an unauthorized complement.

## C. Implementation

`_unauthorized_inference_complements` runs only when the decision has an infer act scoped to `qualified_possibilities_only` and the sentence matches the existing hedge recognizer.

It searches the concrete explanatory phrases that scope already refuses, taken from the non-abstract entries of `_QUALIFIED_FORBIDDEN`: `neglect`, `harsh conditions`, `safety status`, `unseen damage`. A negated match is ignored.

Narration appends `unauthorized_inference_complement` and records the phrase on `unsupported_complement`. The hedge claim `authorized_qualified_inference` is still recorded. Declaration proposals reach the same helper through `_hedge_does_not_authorize`.

No new authority object, no model call, and no general parser were added.

## D. Contextual authorization

The phrase is permitted when it is already carried by:

- an authoritative proposed fact
- the authored corpus
- a player-hypothesis fact or realization claim
- a decision-owned `MAY_INFER` realization claim, including semantic-identity text

A speculative `gm_inference` proposed fact does not count. The same word is not inspected in ordinary narration that has no hedge, and it is not inspected when the decision has no qualified-possibilities infer act.

`significant stress` is not one of those closed phrases, so the P1 infer act still permits it as a qualified possibility.

## E. Positive control

`The split wooden yoke might point to significant stress` accepts on the P1 decision. The claim list contains `authorized_qualified_inference` and does not contain `unauthorized_inference_complement`. The same text passes `_proposal_is_bounded_inference`.

Control A and the useful A1 sentence (`could be consistent with significant stress or force`) also stay accepted. Matrix cases A03 and A04 stay accepts.

## F. Negative control

`The split wooden yoke might point to neglect` rejects. Audit claims contain both `authorized_qualified_inference` and `unauthorized_inference_complement`. The unauthorized claim's identity is `unsupported_complement: neglect`.

## G. Authority-swap control

The same C04 sentence, on a copy of the P1 decision that adds a `MAY_INFER` realization claim whose text and semantic identity carry `neglect`, accepts.

The classified fact is authorized and its authority is not `world_truth`. The permission is the decision claim, not the word list.

## H. Player-hypothesis control

With proposed fact `Maybe this was neglect?` at provenance `player_hypothesis`, the same sentence accepts. The classified fact's authority is not `world_truth` and its provenance is not `authored_world_fact`. The GM can discuss the player's hypothesis. The hypothesis is not promoted.

## I. Direct-authority control

With an authoritative fact `The wooden yoke shows long neglect`, ordinary narration `Long neglect marks the wooden yoke` accepts and does not receive `unauthorized_inference_complement`. The hedged C04 sentence also accepts, because the authoritative fact covers the complement.

## J. Declaration parity

`might point to neglect` fails narration and `_proposal_is_bounded_inference`, both with `unauthorized_inference_complement`.

`might point to significant stress` passes both.

`Excessive strain is a possible cause` still passes the declaration path on the P1 decision. That sentence has no hedge operator, so the complement check does not see it. The named-possibility strip in `_asserted_causal_relation` is unchanged.

## K. Mixed-claim composition

`The split wooden yoke might point to significant stress or neglect` rejects. The stress complement does not immunize `neglect`.

`The split wooden yoke is split` style observations were already unable to cover a second proposition under `_empty_identity_covers`. That rule is unchanged.

## L. Order invariance

`Neglect is what the split wooden yoke might point to, along with significant stress` rejects with the same complement reason. The phrase search is not limited to text after the verb.

The earlier cause-connective order pair still rejects with `unauthorized_causal_relation` and still keeps `authorized_qualified_inference`.

## M. Grounding

A hand-inserted `gm_inference` proposed fact whose text is the C04 sentence does not authorize the complement. Narration still rejects.

The envelope path rejects the C04 declaration and returns with `narration_validation` unset, so the declaration is not merged into the narration ground.

## N. P1 regression

The live P1 narration sentence still rejects with `unauthorized_causal_relation`, and the audit list still includes `authorized_qualified_inference`. The P1 declaration `possibly from heavy use or an external force` still fails before it can be merged.

## O. P3 regression

`the explanation remains uncertain` and `remains unclear` still accept the conditional fit on the perceive decision. `that motive remains uncertain` and `remains unclear` still reject with `unsupported_narrator_lead`, in either order. The perceive decision has no infer act, so the complement check does not run there.

## P. C04 regression

`tests/test_pr_bu_narration_claim_composition.py` no longer xfails C04. The promoted 41-case matrix expects reject, and the run rejects it. A direct test also requires `unauthorized_inference_complement` and `unsupported_complement == neglect`.

## Q. 41-case matrix

| Stage | False accepts | False rejects | Expected outcomes matched |
| --- | ---: | ---: | ---: |
| PR-BU discovery | 9 | 5 | 27 |
| Claim-composition repair | 1 | 0 | 40 |
| Complement authorization | 0 | 0 | 41 |

Correct accepts after this repair: 18. Correct rejects: 23. Ambiguous: 0.

Discovery false accepts were C01, C02, C04, B04, F02, F04, G01, G02, H01. The composition repair left C04. C04 is now a correct reject.

`accept_by_omission` still counts as an acceptance.

Artifact: `PR-BU_validator_semantic_matrix_complement_after.json`.

## R. Broader regressions

Composition file: **62 passed**, 0 xfailed.

Composition plus PR-BS answer recipe: **71 passed**.

Broader command in `artifacts/pr_bu_validator_semantic_robustness/regression_evidence.txt`: **313 passed, 1 failed**.

The failure is `test_pr_bt_provider_requests_remove_at_least_12000_chars_each`. Savings are `121438 - 110405 = 11033`, the same figure as the composition cycle. The test measures provider prompt size. This repair did not edit prompts.

Covered by that run: narration and declaration authority, qualified inference, possible-cause declarations, player hypothesis, uncertainty, certainty, premise links, causal and history restrictions, grounding, incidental improvisation, structured realization, the decision-facing answer recipe, PR-BT provider behavior, PR-BS, PR-BR authority regressions, and C18.

## S. C18

`tests/test_pr_br_structured_chat_path.py` passed, including `accepted == sealed == emitted`.

`tests/test_pr_br_continuation18_immutable_boundary.py` passed.

No C18 regression.

## T. Prompt

UNCHANGED.

This cycle did not edit the system prompt, response policy, answer recipe, provider projection, turn packet, or selective epistemic protocol.

## U. Retry

UNCHANGED. Retry remains deferred.

## V. Authority

UNCHANGED.

`GMResolutionDecision` construction, realization-claim ownership, epistemic ceilings, provenance rules, incidental improvisation, and C18 were not modified. The validator reads the infer scope, realization claims, proposed facts, and corpus that already exist.

## W. PR-BR

PR-BR remains closed.

The decision already distinguishes a qualified-possibilities infer act from an explicit `MAY_INFER` claim, a player hypothesis, and an authoritative fact. The defect was that the validator never compared the complement to those inputs. That is not Chapter I reopening evidence.

## X. PR-BT

PAUSED. Not closed. Not rolled back. Optimization not resumed. Provider context was not modified.

## Y. Remaining validator debt

1. **Explicit non-assertion still returns early.** `cannot establish` without `be` matches `_NONASSERTION_FRAME_RE` and returns before the complement claim is appended. `We cannot establish the cause` still accepts as `explicit_nonassertion`. This did not affect the 41-case matrix and was not the C04 blocker. Deferred.

2. **`definitely`, `certainly`, and `obviously`** remain outside `_CERTAINTY_UPGRADE_RE`. The matrix sentences that use them already reject through other residuals.

3. **Named-possibility narration on P1.** `Excessive strain is a possible cause` still passes as a declaration. Narration of that same sentence on the saved P1 decision can still match the causal residual, because `_relationship_residual_claims` does not strip `a possible cause` the way `_asserted_causal_relation` does. The complement check does not add a reason on that sentence. This split predates this repair. The structured-chat inference that persists `Excessive strain is a possible cause` still passes.

## Z. Live-readiness recommendation

The validator is ready for the tiny P1/P2/P3 live gate.

C04, the last known false accept, is closed. P1 and P3 remain fixed. Useful inference and possible-cause declarations remain available. Do not run that live gate in this cycle.

## Decision

**A — PR-BU deterministic repair complete; ready for micro live.**
