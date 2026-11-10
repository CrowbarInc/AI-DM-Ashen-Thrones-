# 17 Latency and usage

Times are milliseconds from the live application requests.

| Action | HTTP total | Provider | Validation | Integrated total |
|---|---:|---:|---:|---:|
| Notice board | 3330.874 | 3071.704 | 27.224 | 3102.425 |
| Rain barrel | 2266.065 | 1972.176 | 16.549 | 1992.845 |
| Notice board again | 2239.977 | 1947.887 | 7.975 | 1958.829 |
| Look around | 2568.620 | 2187.420 | 17.023 | 2208.876 |

HTTP total: average 2601.384, median 2417.343, maximum 3330.874.

Provider latency is the largest contributor. It is about 87 to 92 percent of each HTTP total. Validation stays under 30 ms. The remaining time is deterministic resolution, ordinary narration setup, and response assembly. Those stages were not instrumented separately from the HTTP total.

Frontend rendering latency: not measured.

Provider requests: 4. Retries: 0. Fallbacks in the live sequence: 2. Tokens: 1663 input, 263 output, 1926 total.

The wait is understandable for a prototype turn and is too slow if every glance costs a full provider round trip. No latency optimization was attempted.
