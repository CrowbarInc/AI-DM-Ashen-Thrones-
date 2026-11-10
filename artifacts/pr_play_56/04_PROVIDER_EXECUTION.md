# Provider execution

Recorded in `preflight.json` before the requests.

| Item | Value |
| --- | --- |
| Provider | OpenAI, through `game.expressive_dialogue.request_expression` |
| Configured model | `gpt-4.1-mini` |
| Model returned | `gpt-4.1-mini-2025-04-14` |
| Endpoint | `responses.create` |
| Temperature | 0.2, the literal in `request_expression` |
| Adapter output cap | 80 tokens |
| Cycle output ceiling | 700 tokens |
| Hook output ceiling | 1,000 tokens, not reached because the adapter cap is 80 |
| Timeout | 45 seconds |
| SDK retries | `max_retries` 0 |
| Host retries | disabled |
| Automatic retries used | 0 |
| Hook behavior on a second `generate` | raises `automatic_retry_forbidden` |
| Hook behavior on timeout, authentication, or connection failure | sets a stop flag. This script does not clear it. |
| Cycle request ceiling | 8 |
| Hook request ceiling actually applied | 6 |
| Cycle token ceiling | 12,000 |
| Hook token ceiling | 10,000 |
| Accounting ledger | `artifacts/pr_play_56/provider_usage.jsonl` |
| Gameplay provider calls | disabled for the chat turn |
| Quarantine gate | on only for a live or fault turn |
| Live narration flag | on only for a live turn |
| Credentials | present. The value was not written. |
| DNS | `api.openai.com:443` resolved |
| Estimated cost | not available. No price table is configured. |

The fault-injection turn used the existing timeout fault. It made no provider request. The six live turns each made one request. No request failed. No retry was spent.

Usage events in the ledger: 1 initialization, 6 admissions, 6 dispatches, 6 completions. Every completion has `purpose=expression`, `owner=expressive_dialogue.request_expression`, `sent=true`, `usage_consistent=true`, `sdk_retries=0`, and host retries disabled.
