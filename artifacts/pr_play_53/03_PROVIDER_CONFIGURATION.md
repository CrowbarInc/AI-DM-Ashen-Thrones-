# Provider configuration

Recorded in `preflight.json` before any request.

| Item | Value |
| --- | --- |
| Provider | OpenAI, through `game.expressive_dialogue.request_expression` |
| Purpose recorded by accounting | `expression` |
| Configured model | `gpt-4.1-mini` |
| Model returned | `gpt-4.1-mini-2025-04-14` |
| Timeout | 45 seconds (`provider_timeout_seconds`) |
| SDK retries | `max_retries` 0, because `ASHEN_PLAYTEST_DISABLE_SDK_RETRIES=1` |
| Host retries | disabled |
| Automatic retries used | 0. The experiment ceiling was 1. The generator raises if called a second time. |
| Adapter output cap | 80 tokens. This was not raised. |
| Experiment output ceiling | 1,000 tokens per request |
| Experiment request ceiling | 6 |
| Experiment total-token ceiling | 10,000 |
| Accounting ledger | `artifacts/pr_play_53/provider_usage.jsonl` |
| Request limit env | `ASHEN_PROVIDER_REQUEST_LIMIT=6` |
| Input / output / total ceilings | 8,000 / 1,000 / 10,000 |
| Gameplay provider calls | disabled for the chat turn |
| Credentials | present in the existing environment. The value was not printed or written. |
| DNS | `api.openai.com:443` resolved |
| Estimated cost | not supported. No price table exists in the current configuration. |

The live hook refuses before dispatch if the configured output cap is above 1,000, if six live requests have already been sent, if recorded tokens have reached 10,000, or if a prior live call stopped the experiment for an authentication, connection, or unknown-usage failure.

A process-wide request limit of 0 also stops the chat turn itself through the existing playtest gate, before the hook runs. The adapter refusal was therefore tested by calling the generator directly, with the OpenAI client still unconstructed.
