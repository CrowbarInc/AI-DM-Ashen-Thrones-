# 16 — Provider Experiment Inventory

`provider.jsonl` retains every exact system/user message, raw output, returned model, status, usage, time and parse failure. Only synthetic fictional context/candidates were sent. Model route gpt-4.1-mini; returned gpt-4.1-mini-2025-04-14. Sampling defaults, SDK retries zero, 45s timeout, cap 5,000 output tokens. B and C prompts appear verbatim in strategy locks and every relevant raw request. Gold fields are never exported.

| Kind | Requests | Successful | Candidate evaluations | Input tokens | Output tokens | Median request ms |
| --- | --- | --- | --- | --- | --- | --- |
| B | 22 | 21 | 116 | 10688 | 11002 | 3768 |
| C | 10 | 10 | 60 | 7564 | 5301 | 3707 |

Initial B strict-format failure is retained separately from the successful rerun; it contributes cost but no classification. No transport outage was encountered. C stopped for safety, not provider access. C safety results are based on 60 actual candidates; no failed or unfavorable output was discarded.

B development-only repeat plan and two one-candidate requests are in `supplement_plan.json`; `repeatability.json` retains claim annotations across repeats. Exact-annotation differences measure surface/decomposition variation, not truth disagreement. C repetition/nondeterminism and local/smaller classifier evaluation were not performed after its stop. B is posthoc annotation of fixed speech, not free generation. Historical two provider corpus entries are recorded-provider evidence and are not counted as fresh R2A generation trials.

| Repeated dev id | Trials | Distinct exact annotations |
| --- | --- | --- |
| borderline01 | 2 | 2 |
| borderline04 | 2 | 2 |
| borderline10 | 2 | 2 |
| commitment01 | 2 | 2 |
| commitment04 | 2 | 2 |
| commitment08 | 2 | 2 |

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
