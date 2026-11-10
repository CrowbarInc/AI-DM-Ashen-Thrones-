# Provider accounting

HTTP, including the single opening:

- Requests: 20
- Input tokens: 34,003
- Output tokens: 2,279
- Total tokens: 36,282
- Retries: 0

Browser, new calls only. The copied opening row was not a new generation:

- Requests: 5
- Input tokens: 1,522
- Output tokens: 129
- Total tokens: 1,651
- Retries: 0

Combined live calls: 25 requests, 35,525 input, 2,408 output, 37,933 total.

The first browser process refused expression with "provider admission accounting unavailable" because the copied ledger already existed and a new process will not adopt it. That attempt was not counted. The ledger was removed and the host was restarted.
