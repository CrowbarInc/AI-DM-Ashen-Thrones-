# 11 Live provider results

Provider: OpenAI through `game.expressive_dialogue.request_expression`. Model: gpt-4.1-mini-2025-04-14.

The key was already configured. It is not recorded here.

| Action | Requests | Input | Output | Total | Retries | Decision |
|---|---:|---:|---:|---:|---:|---|
| Notice board | 1 | 395 | 59 | 454 | 0 | PASS |
| Rain barrel | 1 | 410 | 69 | 479 | 0 | FAIL |
| Notice board again | 1 | 448 | 57 | 505 | 0 | PASS |
| Look around the gate | 1 | 410 | 78 | 488 | 0 | REVIEW_REQUIRED |
| Total | 4 | 1663 | 263 | 1926 | 0 | |

The ledger has four admissions, four dispatches, and four completions. SDK retries are 0. Host retries are disabled. The run did not stop for budget. The ceiling was 8 requests and 15000 tokens. The integrated hook's own ceiling remained 8 requests and 12000 tokens.

No call was repeated to seek a passing sentence. Fault injection did not call the provider. The replay used the saved sentences and made 0 provider requests.
