# PR-BU narration claim-composition repair

Deterministic validator repair. Model and gameplay API calls: zero. No commit. No push.

## A. Executive result

Compositional semantic enforcement is repaired for the live P1 and P3 failures and for mixed-order cause and uncertainty cases.

One matrix case remains a false accept: `C04`. It is a separate complement gap, recorded below, and it is the reason the decision is **B**.

## B. Root cause

`audit_narrated_claims` treated one recognized epistemic operation as success or exemption for the whole sentence.

The qualified-inference branch appended `authorized_qualified_inference` and returned. Cause, history, and certainty checks below that line did not run. `_UNKNOWN_SLOT_RE` at the top of `_unsupported_narrator_lead` returned before any other definite noun was tested, so `remains unclear` exempted `motive`. `remains uncertain` did not match that pattern, so the same conditional was rejected. `_proposal_is_bounded_inference` accepted a hedged proposal without running those residuals, and the accepted text was copied into the narration ground.

## C. P1 repair

The inference branch now records the hedge and continues. `due to` and `possibly from` still match the cause patterns. The P1 narration sentence therefore carries both `authorized_qualified_inference` and `unauthorized_causal_relation`, and classification rejects it.

The P1 declaration `possibly from heavy use or an external force` fails `_proposal_is_bounded_inference` with `unauthorized_causal_relation`. The envelope returns before that declaration can be merged into `proposed_facts`.

## D. P3 repair

`_marks_unresolved_status` treats `unclear`, `uncertain`, `cannot be determined`, and `cannot be established` as one status operation. A conditional fit whose coda is `the explanation remains uncertain` is accepted as `unknown_cause_actor_or_time`.

`motive` is not an epistemic-slot subject. `that motive remains unclear` and `that motive remains uncertain` both append `unsupported_narrator_lead`. The status wording does not clear the noun. Order does not change that result.

## E. Composition model

The unit of audit is still the sentence. The unit of authorization inside it is one epistemic operation.

A licensed `might` / `could` / `may` authorizes the inference claim. An unresolved-status phrase authorizes the status claim and the slot noun that phrase is about (`explanation`, `cause`, and the boilerplate already used by the status patterns). Cause connectives, positive certainty markers, actor attributions, and other ungrounded definite nouns are separate operations in the same sentence.

No parser and no model call were added.

## F. Qualified-inference behavior

Inference remains available when the decision has an `infer` act and the sentence matches `_QUALIFIED_INFERENCE_RE` without a lead pattern. Control A, `The split yoke might suggest the wood gave under a load`, stays accepted. `suggest`, `point to`, and `indicate` are not scored again as `unauthorized_evidential_relation` when they are the verb that licensed that inference.

`due to`, `because`, `caused by`, `as a result of`, and `possibly` / `perhaps` / `maybe from` still produce `unauthorized_causal_relation` in either clause order. `clearly` beside `could` still produces `unauthorized_certainty_upgrade`.

`A possible cause` remains the qualified-possibility shape already accepted for declarations such as `Excessive strain is a possible cause`. The connective check strips that phrase and still rejects a real connective.

## G. Uncertainty behavior

Shared predicate: `_marks_unresolved_status`.

Covered forms used by the matrix: `remains unclear`, `is unclear`, `remains uncertain`, `is uncertain`, `cannot be determined`, `cannot be established`, plus the existing unknown-slot and epistemic-limit patterns.

Matching the predicate appends `unknown_cause_actor_or_time` and filters the status subject out of the definite-lead test. It does not skip cause, actor, history, or other definite nouns.

## H. Negation and scope

A certainty or establishment match is ignored when `not`, `cannot`, `nothing`, or `no` governs it within a short window. `It is not clearly neglect` and `Deliberate cutting cannot be established` are accepted. `It clearly could be neglect` and `The cause is clear` are rejected. `The cause is not clear` does not match the positive `is clear` pattern.

Deferred: full negation parsing, and the explicit-non-assertion return, which is still terminal for `cannot establish` without `be`.

## I. Declaration parity

`_proposal_is_bounded_inference` now rejects the same cause connectives, actor attributions, history assertions, and non-negated certainty markers that narration rejects. A hedge is not sufficient.

`The split wooden yoke might suggest significant stress, perhaps due to prolonged neglect` fails in both lanes with `unauthorized_causal_relation`. The useful sentence `could be consistent with significant stress or force` passes in both lanes.

`Excessive strain is a possible cause` stays an accepted bounded inference. That phrase is the possibility name, not `due to`.

## J. Grounding corpus

Self-grounding was real and it contributed to P1. The accepted declaration put `might` into `_decision_ground`. One in-ground token grounded the six-word definite span, so the lead check did not see `damage`.

Two changes:

1. The declaration is rejected, so the envelope does not merge it.
2. `_fact_can_ground_definite` excludes `authority: inference` and provenance `gm_inference`, `speculation`, and `generated_proposal`. Authoritative proposed facts still ground definites.

Forcing the speculative declaration into `proposed_facts` still leaves the P1 span ungrounded and still rejects `due to`.

## K. 41-case matrix

| | Before | After |
| --- | --- | --- |
| Cases | 41 | 41 |
| Correct accepts | 13 | 18 |
| Correct rejects | 14 | 22 |
| False accepts | 9 | 1 |
| False rejects | 5 | 0 |
| Ambiguous | 0 | 0 |

`accept_by_omission` still counts as an acceptance, matching the discovery scoring.

## L. False accepts

Before: `C01`, `C02`, `C04`, `B04`, `F02`, `F04`, `G01`, `G02`, `H01`.

After: `C04` only.

`C04` is `The split wooden yoke might point to neglect.` The subject is grounded. There is no cause connective and no positive certainty marker. `point to` is the same licensed hedge class as Control A's `suggest`. Treating it as evidential establishment would reject Control A. The word `neglect` was not banned.

## M. False rejects

Before: `D02`, `D05`, `D07`, `F03`, `F06`.

After: none.

## N. Order invariance

Cause connective before the hedge, and hedge before the cause connective, both reject with `unauthorized_causal_relation` and both keep `authorized_qualified_inference` in the claim list.

`that motive remains unclear/uncertain` before or after the conditional fit rejects with `unsupported_narrator_lead`.

`the explanation remains uncertain/unclear` before or after the conditional fit accepts.

## O. Permanent regression coverage

`tests/test_pr_bu_narration_claim_composition.py` loads `PR-BU_validator_semantic_matrix.json` and checks every case id, including `C01b`. `C04` is an expected failure until the complement gap is closed.

Explicit tests cover the P1 narration sentence, the P1 declaration, the envelope short-circuit, speculative grounding, P3 status parity, motive in both uncertainty wordings and both orders, cause order, declaration/narration parity, negation, `the cause is clear`, and `Someone cracked`.

## P. Broader regression suite

Command and totals are in `artifacts/pr_bu_validator_semantic_robustness/regression_evidence.txt`.

Validator-relevant result: **304 passed, 1 xfailed** (`C04`).

One additional failure is outside this repair:

`tests/test_pr_bt_policy_instruction_deduplication.py::test_pr_bt_provider_requests_remove_at_least_12000_chars_each`

`121438 - 110405 = 11033`, which is under 12000. The test measures provider prompt size. It does not call the narration validator. This repair did not edit prompts. The working tree already contained prompt-module edits.

## Q. C18

`tests/test_pr_br_structured_chat_path.py` passed, including `accepted == sealed == emitted`.

`tests/test_pr_br_continuation18_immutable_boundary.py` passed.

No C18 regression.

## R. Prompt status

UNCHANGED.

## S. Retry status

UNCHANGED.

## T. Authority status

UNCHANGED. Resolution Contract ownership, `GMResolutionDecision`, realization claims, epistemic ceilings, player-hypothesis status, provenance rules, incidental improvisation, and C18 were not modified.

## U. Architecture status

PR-BR remains closed.

The decision already represents an infer act, a player hypothesis, and unresolved qualifier slots. The defect was validator control flow. `C04` needs a complement check in the validator. It does not require a new authority kind.

## V. PR-BT status

PAUSED. Not closed. Not rolled back. Optimization not resumed.

## W. Remaining validator debt

1. **`C04` — history/cause complement with no connective.** `The split wooden yoke might point to neglect` is still accepted. One later repair: authorize the complement of a licensed hedge separately from the hedge verb. A grounded observation reading such as `might suggest the wood gave under a load` must stay accepted. Do not ban `neglect`. Do not score `suggest` / `point to` as evidential establishment when they licensed the inference.

2. **Explicit non-assertion is still a terminal return** for `cannot establish` without `be`. Not hit by the 41-case matrix.

3. **Slot fill still skips uncertain frames.** Cause connectives are covered by the relationship residual. A cause stated without `because` / `due to` / `possibly from` can still miss slot fill when the frame is uncertain. That is the same complement gap as `C04`.

4. **`definitely`, `certainly`, and `obviously`** are still outside `_CERTAINTY_UPGRADE_RE`. The matrix sentences that use them already reject through stateful or history residuals.

## X. Live-readiness recommendation

A tiny live P1/P2/P3 gate is not justified yet.

P1's `due to` / `possibly from` shape and P3's `remains uncertain` versus `motive` shape are fixed. A grounded hedge with an unsupported history noun and no connective (`C04`) would still pass. That is the same product failure with the connective removed. Do the one complement repair, then consider the micro-live. Do not run it in this cycle.

## Decision

**B — one bounded validator defect remains.**

Core composition repair succeeded. Repair `C04` before live testing, by the complement check in section W. Do not weaken Control A to force the matrix to 41/41.
