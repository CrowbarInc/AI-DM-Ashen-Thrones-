# Provider Accounting

Admission was not bypassed. The provider host was not restarted to reset a ledger.

## This cycle’s live use

| Item | Value |
| --- | --- |
| Requests | 1 |
| Input tokens | 22,777 |
| Output tokens | 600 |
| Total tokens | 23,377 |
| Retries | 0 |
| Openings | 0 |
| Model | `gpt-4.1-mini-2025-04-14` |
| Attempt | `12e9b94b02cb49cf984cf975b5e58d5e` |
| Ledger | `http_data/provider_usage.jsonl` |

The request was sent because the HTTP acceptance continuation, “I step back from the notice board.”, still invoked primary narration while interpretation was disabled. `sent` is true. This exceeds the cycle cap of 3,000 tokens. No further live call was made.

## Browser host

`browser_provider_usage.jsonl` has one `initialized` event and no completed request. The controlled refusal used request limit 0 and did not dispatch. Token ceilings on that host were 50 input, 50 output, and 80 total.

## Deterministic accounting

Request, input, output, and total ceilings refuse before dispatch and add 0 requests and 0 tokens. Accounting unavailable refuses before dispatch. A provider exception and a model mismatch record one sent request and still write no gameplay publication. No case enables an automatic retry.
