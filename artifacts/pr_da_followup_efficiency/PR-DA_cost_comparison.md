# PR-DA Cost Comparison

## Historical PR-CY follow-up

These figures are the recorded PR-CY provider usage. They were not remeasured.

| Request | Input | Output | Total | Result |
|---|---:|---:|---:|---|
| Follow-up attempt 1 | 31,242 | 1,230 | 32,472 | Rejected |
| Follow-up retry | 39,262 | 331 | 39,593 | Rejected |
| Follow-up combined | 70,504 | 1,561 | 72,065 | Fallback refusal |

Historical retry overhead: 39,593 tokens.

## Actual PR-DA follow-up

These figures are the live Responses API usage for this run.

| Request | Input | Output | Total | Result |
|---|---:|---:|---:|---|
| Follow-up attempt 1 | 30,166 | 116 | 30,282 | Accepted |
| Retry | 0 | 0 | 0 | No retry |

- Successful first attempt: yes
- Useful final answer: yes
- Reduced-context projection selected: no

## Differences

- Combined total: 30,282 − 72,065 = −41,783 tokens.
- Retry overhead: 0 − 39,593 = −39,593 tokens.
- First-request input: 30,166 − 31,242 = −1,076 tokens.
- First-request total: 30,282 − 32,472 = −2,190 tokens.

Most of the combined difference is the retry that PR-CY spent and this run did not. The first-request input is also 1,076 tokens lower, but the live payload did not select reduced context, so that gap is not a projection saving.

The eligibility report's byte/4 figures are reconstructed estimates. They are not provider usage.

This is one live sample on the dirty worktree. It does not isolate PR-CZ from every other uncommitted change, so the whole 41,783-token difference is not attributed to PR-CZ alone.
