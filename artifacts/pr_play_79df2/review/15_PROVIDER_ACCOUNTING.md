# Provider accounting

Sent requests: 4. Input tokens: 1853. Output tokens: 205. Total tokens: 2058. Retries: 0. Openings: 0. Budget: 6 requests and 6,000 tokens.

Superseded process ledger `browser_provider_usage.jsonl`:

| Attempt | Purpose | In | Out | Total | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 33c6af4ea39a4e819f21e8c3a8e0184d | interpretation | 1160 | 122 | 1282 | completed |
| eda3484f02d3444996d3a930e6e003bd | expression | 161 | 15 | 176 | rejected, not published |
| ecd7f0725cd24e5c8da06d44cdee5fe1 | expression | 259 | 34 | 293 | accepted |

Final process ledger `browser_provider_usage_final.jsonl`:

| Attempt | Purpose | In | Out | Total | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 831112184d3147059da48e9e7151d946 | expression | 273 | 34 | 307 | accepted |

Model: `gpt-4.1-mini` / `gpt-4.1-mini-2025-04-14`. Retries disabled. The final process cap was the remaining cycle budget (3 requests, 3,420 input, 829 output, 4,249 total) because a new process cannot adopt an existing ledger. The accepted expression fit inside that cap. No request was sent beyond the cycle budget.
