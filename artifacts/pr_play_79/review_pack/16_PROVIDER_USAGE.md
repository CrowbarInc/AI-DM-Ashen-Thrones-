# 16 — Provider usage

Source: `artifacts/pr_play_79/live_data/provider_usage.jsonl`, completed events only. Admission and dispatch rows are not extra requests.

| Purpose | Completed |
| --- | --- |
| primary_turn | 3 |
| interpretation | 4 |
| contract_interpretation | 2 |
| expression | 2 |
| retry_escalation | 2 |
| Total completed | 13 |

- Model: `gpt-4.1-mini-2025-04-14`
- Input plus output tokens on completed events: 144,968
- Retries: 2 (`retry_escalation`)
- Narration proposals accepted / published: 0 / 0
- Dialogue proposals accepted / published: 0 / 0
- The two later `speak()` continuations added 0 completed requests

The suggested ceiling was 40 requests and 80,000 tokens. Requests stayed under 40. Tokens did not. The opening turn was 26,676 tokens. No further live session was started, so the cycle would not pay for a second opening.

Estimated cost is not computed here. The usage file has token counts and no price table was applied.
