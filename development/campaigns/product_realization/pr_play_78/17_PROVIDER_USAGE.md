# Provider usage

Source: `artifacts/pr_play_78/extended_data/provider_usage.jsonl`, `artifacts/pr_play_78/live_data/provider_usage.jsonl`, and `artifacts/pr_play_78/provider_usage.json`.

| | Extended | Live gate | Total |
|---|---|---|---|
| Completed | 6 | 8 | 14 |
| Admitted | 6 | 8 | 14 |
| Dispatch attempted | 6 | 8 | 14 |
| Retries | 0 | 0 | 0 |
| Input tokens | 1,550 | 1,115 | 2,665 |
| Output tokens | 116 | 219 | 335 |
| Total tokens | 1,666 | 1,334 | 3,000 |

Model configured: `gpt-4.1-mini`. Model returned: `gpt-4.1-mini-2025-04-14`. Purpose: `expression`. Budget used: 14 of 24 requests, 3,000 of 48,000 tokens.

Accepted and published after the scene fix: 3 dialogue lines, 4 narration restyles. Rejected narration: 1 (`not_a_variation`). Extended session published 4 additional dialogue lines before that fix, one of which added an uncommitted track condition, and 1 live request fell back to deterministic thanks.

Opening scenes use the existing stubbed opening response, not a live call. The browser host set provider calls disabled. No browser turn is in this table.

Cost was not estimated. No price table was applied. The provider never wrote campaign state.
