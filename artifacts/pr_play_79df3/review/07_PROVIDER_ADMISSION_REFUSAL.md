# Provider-Admission Refusal

Deterministic cases in `tests/test_pr_play_79df3_classification.py` and holdout H01–H08. Accounting was not bypassed. Ceilings use the production admission path.

| Case | Dispatch | Requests | Tokens | Gameplay event | Pointer |
| --- | --- | --- | --- | --- | --- |
| Request ceiling | Not sent | 0 | 0 | None | Unchanged |
| Input-token ceiling | Not sent | 0 | 0 | None | Unchanged |
| Output-token ceiling | Not sent | 0 | 0 | None | Unchanged |
| Total-token ceiling | Not sent | 0 | 0 | None | Unchanged |
| Accounting path is a directory | Not sent | 0 | 0 | None | Unchanged |
| Playtest stop at request ceiling | Not sent | 0 | 0 | None | Unchanged |
| Token estimate unavailable | Not sent | 0 | 0 | None | Unchanged |

Visible text for the ceilings and the accounting failure is “I couldn't interpret that just now, so no gameplay action was taken.” The token-estimate case uses “I can't send that for interpretation because the token estimate is unavailable.” The playtest gate uses the existing playtest stop message.

The resolver does not run. Turn and world stay put. The preceding publication remains. A later valid examination adds one gameplay event and advances the pointer. Retries stay 0.

HTTP acceptance repeated the request-ceiling case on the normal HTTP route: events stayed at 1, turn stayed at 5, requests stayed at 0, and the log class was `operational_refusal`.
