# PR-DY failure recovery

Providers were not left enabled for these checks. The live server had already spent its planned interpretation calls. Further live retries were not used.

| Case | Where shown | Result |
| --- | --- | --- |
| Malformed interpretation | `test_pr_dy_malformed_interpretation_does_not_execute` | No execution |
| Rejected / unsupported interpretation | `test_pr_dy_rejected_interpretation_does_not_fall_through` | No narration call, turn not advanced |
| Unavailable or wrong-kind target | `test_pr_dy_bridge_rejection_does_not_execute` (ASK aimed at the lantern) | Bridge rejects, no execution |
| Provider path unavailable | `test_pr_dy_disabled_interpretation_does_not_call_provider` and the disabled HTTP preflight | Interpreter not called; explicit OOC stays non-mutating; explicit IC still uses the parser |
| Narration failure | Live ledger rows 1, 3, and 5, refusal `input-token ceiling`, `sent` false | Resolver text already committed is what the player sees. Opening has no resolver sentence, so the player sees the budget sentence. No second commit |
| Repeated submission | `test_pr_dy_repeated_submission_commits_a_second_turn` | A second identical inspect commits another turn. Not collapsed |

Clarification is the same pre-commit shape as rejection: `test_pr_dy_clarification_does_not_mutate`.

A live provider exception after a request has already been sent is recorded with null token counts and poisons later budgeted calls. That exception path was not injected against the live server in this cycle. The budget refusal path was.

No duplicate committed gameplay action occurred on the live browser sequence.
