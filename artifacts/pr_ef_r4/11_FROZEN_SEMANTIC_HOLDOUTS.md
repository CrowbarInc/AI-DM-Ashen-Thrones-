# 11 — Frozen Semantic Holdouts

Frozen before the implementation was allowed to pass: `tests/fixtures/pr_ef_r4_holdouts.json` (25 cases, frozen 2026-10-16). The expressions were not rewritten after results. Scripted adversarial provider fields in that file are used by `tests/test_pr_ef_r4_authorization.py` only. The live run did not inject them.

## Scripted module

28 tests passed, 0 failed, as part of the post-implementation family. That includes the 25 frozen cases plus the narration-eligibility predicate, the historical provider-id override, and the third-person continuation guard.

Scripted coverage: explicit name, role, unique pronoun, two-NPC and one-NPC non-unique phrases, either/someone, height fact present and absent, GM question, conflicting GM recipient, follow-up, GM clarification, correction in three states, confirmation in three states, withdrawal, mixed ask-then-leave, conditional gate, incidental glance, missing provider target, and save/load of a two-choice pending ask.

## Live metrics, reported separately

Fresh interpretation, same expressions, disposable scene per case. 25 cases.

| Metric | Result |
| --- | --- |
| A. Interpretation-label agreement | 5 / 15 scored. 10 cases have no single expected recipient/purpose (ambiguous, mixed, conditional, save/load). Failures are mostly the model not emitting CORRECTION, CONFIRMATION, WITHDRAWAL, or NPC when the behavior was still right. |
| B. Authorization / end-to-end behavior | 23 / 25 |
| C. Resolver handoff | 24 / 25 |
| D. End-to-end behavior | same as B, 23 / 25 |
| E. State integrity | 24 / 25 |
| F. Final-response consistency | 23 / 25 |

The two behavior misses:

- `ambiguous_one_of_them_one_npc`: clarification, no mutation. The line was the provider clarification, so the phrase check failed. State passed.
- `npc_followup`: `malformed_communication` blocked the cold follow-up. State and handoff failed. The continuous conversation’s turn 3 is the passing instance of this sentence.

`explicit_role_ask` and `direct_ask_conflicting_owner` executed Mara even though the model’s recipient was GM. Label agreement failed. Behavior, handoff, state, and response passed. That is the ownership contract working against the model’s label.
