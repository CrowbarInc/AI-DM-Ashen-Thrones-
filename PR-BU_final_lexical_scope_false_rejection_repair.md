# PR-BU final lexical-scope false-rejection repair

Deterministic validator repair. Model and gameplay API calls: zero. No live play. No prompt, retry, or authority-model edits. Nothing was committed or pushed.

## A. Executive result

PR-BU can close.

Both demonstrated false rejections are repaired. The exact preserved P1 retry now passes the production envelope validator. Genuine route/geography matches still reject. Genuine unauthorized cause attributions still reject. The original 41-case matrix remains 41 / 41. The new lexical-scope controls pass. C18 holds. PR-BR stays closed. PR-BT stays paused at BT-C.

Decision: **A — PR-BU CLOSED.**

## B. Exact P1 retry reconstruction

Preserved narration, attempt 2, response `resp_0926127abab144d7006ac41d68881487d28db895396ca8107c`, from `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P1/validation.json`:

> The bell's wooden yoke is split, its surface showing clear evidence of damage. The leather hanger appears torn, frayed at the edges. These details point to significant deterioration, though without further context it remains uncertain what exactly caused this wear or when it occurred.

`declared_claims` is empty. The validator result was `hard_valid: false`, reason `unauthorized_resolution_decision_fact`.

Two narration rows failed:

- `The bell's wooden yoke is split, its surface showing clear evidence of damage.` → `patrol_route_or_geography`
- `These details point to significant deterioration, though without further context it remains uncertain what exactly caused this wear or when it occurred.` → `unauthorized_cause_attribution`

The third sentence also carried authorized rows `authorized_qualified_inference` and `unknown_cause_actor_or_time`. The unauthorized cause row is what failed it. The fraying sentence was not a violation.

Semantic class of that retry: valid. Validator result before this repair: reject. Classification: false reject.

## C. Geography false positive

Exact input span on the yoke sentence: characters `[26, 67]`, text `split, its surface showing clear evidence`.

Lexical trigger: `split`, then `evidence`.

Regex: the second alternative of `patrol_route_or_geography` in `_CONSEQUENTIAL_PATTERNS`. The left class was `route|road|path|fork|marker|watchtower|milestone|split`. The right class was `patrol|tracks?|trail|broken twigs?|bootprints?|evidence`. The window is 90 characters and does not cross `.`, `!`, or `?`.

Contextual words that fired: `split` and `evidence`. The sentence has no patrol, route, road, path, trail, fork, marker, or watchtower.

It matched because `split` sat in the route-head class, so any later `evidence` inside the window was read as route evidence.

That reading is wrong because `is split` is the condition of the wooden yoke, and `evidence of damage` is the condition of that object. The smallest scope-aware distinction is at the head class: `split` is a route token only when a route noun is already in the match.

## D. Geography repair

`split` was removed from the left-hand head class. The second alternative now starts at `route|road|path|fork|marker|watchtower|milestone` and still looks ahead for patrol, tracks, trail, broken twigs, bootprints, or evidence.

The first alternative still requires a route noun on the left. Its right-hand branch list now uses `splits?` and `forks?`, so `the road splits` and `the trail forks` are route branches of that noun. Copular `is split` without a route noun does not enter the pattern. There is no global allow for `split`, and no special case for yokes, bells, damage, or the P1 sentence.

## E. Geography controls

11 / 11 passed. They are in `tests/test_pr_bu_lexical_scope.py` and are not part of the 41-case denominator.

| Control | Text shape | Result |
| --- | --- | --- |
| A1 | `The beam is split.` / `The leather is split.` | no geography, accepted |
| A2 | physical split plus `evidence`, including the preserved yoke sentence | no geography, accepted |
| A3 | `The road splits ahead.` / `The trail split north.` / `The trail forks toward the river.` | geography fires, rejected |
| A4 | `The patrol route splits near the gate.` and the bootprints / old-route / fork / marker chain | geography fires, rejected |
| A5 | driver says the patrol took the old route and split at the fork | pattern still matches; narration accepted as `npc_claim` |
| A5 | `You walk through the gate arch and reach the road beyond.` under a permitted scene transition | accepted, no geography code |

## F. Causal false positive

Exact input span on the uncertainty sentence: characters `[115, 126]`, text `caused this`.

Lexical causal trigger: `_EVENT_CAUSE_ATTRIBUTION_RE`, alternative `caused` plus `it|this|that|the|damage`.

Uncertainty language in the same clause: `it remains uncertain what exactly`.

Recognizer order: `_marks_unresolved_status` is true because `_UNRESOLVED_STATUS_EQUIVALENT_RE` matches `remains uncertain`, so the audit records `unknown_cause_actor_or_time`. `_ordinary_residual_reasons` then searches the cause regex. Its early return looks at `_UNKNOWN_SLOT_RE`. That pattern matches `remains unclear` and does not match `remains uncertain`. The cause verb was therefore still an attribution.

Negation scope was not inspected. `_establishment_match_is_negated` does not cover this construction, and the status marker was not applied to the verb span.

The sentence was classified as attribution because `caused this` is a positive match and the governing `remains uncertain what` was only allowed to add a second, authorized status row.

The smallest safe repair is at the cause-attribution check: a causal verb governed by the shared unresolved-status marker, in the same clause, linked by `what` / `which` / `who` / `why`, is not an attribution. `and` or `but` between the verb and the marker leaves the verb in force. The whole sentence does not return early.

## G. Causal-scope repair

`_asserted_event_cause` walks `_EVENT_CAUSE_ATTRIBUTION_RE`. A match that `_causal_match_is_unresolved_cause` accepts is skipped. Any other match still produces `unauthorized_cause_attribution` unless the decision authorizes cause.

The status spans come from `_UNRESOLVED_STATUS_EQUIVALENT_RE`, the same pattern `_marks_unresolved_status` already uses. Clause boundaries come from the existing comma / semicolon / `but` / `yet` splitter.

`cannot` / `can't determine` was added beside the existing passive `cannot be determined`. `We cannot determine what caused this wear` is the same governed-verb case. `cannot establish` was left on its existing early-return path. See section I.

`might have caused this` is unchanged. It is a qualified-inference hedge, not an unresolved-cause construction.

`because`, `caused by`, `due to`, and `possibly from` still reject through `_CAUSAL_RELATION_RE` when unauthorized. The P1 initial `possibly from years of use or a recent forceful event` still fails that way.

## H. Causal controls

13 / 13 passed, separate from the 41-case matrix.

| Control | Result |
| --- | --- |
| `Neglect caused this damage.` | reject, `unauthorized_cause_attribution` |
| `The damage was caused by neglect.` | reject, `unauthorized_causal_relation` |
| `This happened because of neglect.` | reject, `unauthorized_causal_relation` |
| `A sudden pull might have caused this.` on the P1 decision | accept, `authorized_qualified_inference` |
| `It remains uncertain what exactly caused this wear.` | accept, no cause-attribution code |
| `What exactly caused this wear remains uncertain.` | accept, no cause-attribution code |
| `It remains unclear what caused this.` | accept |
| `The cause cannot be determined from the visible evidence.` | accept |
| `We cannot determine what caused this wear.` | accept, `unknown_cause_actor_or_time` |
| `It cannot be determined what caused this wear.` | accept |
| `We cannot establish the cause.` | accept, `explicit_nonassertion` |
| `Neglect caused this damage, though it remains uncertain what exactly caused this wear.` | reject, `unauthorized_cause_attribution` |
| Same direct sentence with an authorized causal fact on the decision | accept |

## I. `cannot establish`

Deferred.

`We cannot establish the cause` and `We cannot establish that neglect caused this damage` still return from `_NONASSERTION_FRAME_RE` as `explicit_nonassertion` before complement and cause residuals run. The second sentence therefore still accepts even though it names neglect as the cause.

That is a different defect from the P1 retry. The retry recorded the unresolved status and then also recorded a cause attribution. `cannot establish` never reaches the attribution check, so the failure mode is a false accept of neighboring content, not a false reject of a governed verb. Extending the unresolved-cause helper does not change that early return. Removing the early return would be a new negation pass. It stays deferred.

`cannot determine` was fixed, because it is the active form of `cannot be determined`, which the shared status pattern already contained, and it false-rejected `caused this` the same way `remains uncertain` did.

## J. Exact P1 retry

Before: `hard_valid false`. Codes on the two sentences: `patrol_route_or_geography`, `unauthorized_cause_attribution`.

After: `hard_valid true` through `audit_realization_envelope_against_decision` on the preserved raw envelope, P1 decision, and chapel corpus. Remaining codes: `authorized_qualified_inference`, `unknown_cause_actor_or_time`. No other rejection appeared.

## K. P1 initial

Still rejected.

Preserved narration includes `possibly from years of use or a recent forceful event`. After repair the envelope is `hard_valid false`, with `unauthorized_causal_relation` and `unsupported_narrator_lead`. The declaration row `accepted_bounded_declared_inference` is still present and does not license the narration complement. `authorized_qualified_inference` is still recorded on the narration and does not clear the causal residual.

## L. P2 initial

Still rejected.

The preserved declaration is mode `realize`, provenance requested `authored_world_fact`, epistemic status `established`, source claim id empty, text `The baker declines to reveal which loaf they keep for themselves.` The envelope is `hard_valid false` with `unauthorized_declared_claim`. `narration_validation` stays unset, so the declaration fails before narration can authorize it.

## M. P3 initial

Still accepted.

Preserved narration: `The bronze bell's wooden yoke is visibly split, and its leather hanger is torn. While these damages are clear, whether they were caused deliberately by someone cannot be confirmed just from the current evidence.`

Envelope `hard_valid true`. Declaration code `accepted_declared_realization`. No `unauthorized_cause_attribution`. No `patrol_route_or_geography`.

## N. Original 41-case matrix

41 / 41.

False accepts: 0. False rejects: 0. Correct accepts: 18. Correct rejects: 23.

`tests/test_pr_bu_narration_claim_composition.py`: 62 passed, including the parametrized matrix. Result file: `PR-BU_validator_semantic_matrix_lexical_scope_after.json`. The new scope cases are not in this denominator.

C04, the valid hedge with an authorized complement, the invalid hedge/complement pair, authority swap, player hypothesis, and declaration parity stay on their previous expected outcomes.

## O. New lexical-scope tests

24 / 24, in `tests/test_pr_bu_lexical_scope.py`.

- Geography: 11 / 11
- Causal scope: 13 / 13

The same module also replays the four preserved gate envelopes. Module total: 28 / 28.

## P. Broader regression

341 passed, 1 failed, in 20.41s.

The failure is `test_pr_bt_provider_requests_remove_at_least_12000_chars_each`. Measured savings are `121438 - 110405 = 11033`. The complement-authorization cycle recorded the same figure and the same failure, at 313 passed and 1 failed. The extra 28 passes are this module. Prompts were not edited. The assertion measures provider prompt size.

Covered and passing inside that run: the 41-case matrix, the new geography and causal controls, the exact P1 retry, P1 initial rejection, P2 initial rejection, P3 initial acceptance, narration authority, declaration authority, qualified inference, complement authorization, player hypothesis, uncertainty, certainty, premise links, grounding, causal and history restrictions, incidental improvisation, structured realization, PR-BT provider tests other than that size assertion, PR-BS, PR-BR, and C18.

## Q. C18

`tests/test_pr_br_structured_chat_path.py` and `tests/test_pr_br_continuation18_immutable_boundary.py`: 32 passed.

`test_raw_chat_accepts_authorized_fact_and_seals_it` still requires `accepted == sealed == emitted`.

No C18 regression.

## R. Prompt

UNCHANGED.

## S. Retry

UNCHANGED.

## T. Authority

UNCHANGED.

`GMResolutionDecision` construction, realization-claim ownership, epistemic ceilings, and provenance rules were not edited. The validator reads the decision it already receives. `cannot determine` was added to the existing unresolved-status recognizer. That is a classification scope, not a new authority object.

## U. PR-BR

CLOSED.

The decision can already represent a route claim, a causal fact, an unresolved status, and an NPC claim. The defect was that two lexical matches ignored the construction around them. That is not Chapter I reopening evidence.

## V. PR-BU

**A — PR-BU CLOSED.**

## W. PR-BT

PAUSED / BT-C.

The compact provider stays in place. The PR-BS prompt was not restored. This cycle did not reopen prompt optimization.

## X. Remaining validator debt

These do not block closure.

1. `definitely`, `certainly`, and `obviously` remain outside `_CERTAINTY_UPGRADE_RE`. Matrix sentences that use them already reject through other residuals.
2. Narration and declaration still differ on bare `a possible cause`. `_asserted_causal_relation` strips that named possibility. `_relationship_residual_claims` does not.
3. Qualified-inference complements still use the closed phrase list, not general proposition parsing.
4. `cannot establish` without `be` still returns as `explicit_nonassertion` before a neighboring cause or complement is checked. Inspected. Not the same root cause as the P1 retry. Deferred.

## Y. Next recommended slice

First-pass realization competence. Do not start it in this cycle. Do not run another P1/P2/P3 live gate for this validator repair.

The preserved failure corpus for that slice:

- P1. A bounded interpretation request produced unsupported `years of use` and a `recent forceful event`. The validator correctly rejected them.
- P2. Ordinary incidental NPC social behavior was emitted as `realize` / `authored_world_fact` / `established` instead of narration or incidental improvisation. The validator correctly rejected it.

Diagnose the responsible layer before changing prompts.
