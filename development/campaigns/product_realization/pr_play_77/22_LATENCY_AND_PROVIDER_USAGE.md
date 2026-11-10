# Latency and Provider Usage

Deterministic HTTP, ten campaign turns:

- Mean 364.25 ms
- Median 175.2 ms
- Maximum 908.1 ms

Selected HTTP steps:

- Two-step push and look: 306.8 ms
- Three-step partial success: 792.0 ms
- Conditional skip: 42.9 ms
- Independent stand and approach: 839.7 ms
- Read-only compound: 43.6 ms
- Resumed state question: 40.7 ms
- Conditional after resume: 908.1 ms

Browser server time, 19 chat posts: mean 551.42 ms, median 424.55 ms, maximum 1683.87 ms. The maximum is the stand-and-approach request. Paint time was not captured.

Provider, measured separately:

- 4 requests
- 1,037 tokens
- 0 retries
- 1 plan accepted and executed by the host
- 3 plans rejected
- Latencies 2253 ms, 1479 ms, 835 ms, and 1255 ms

Provider time is not folded into the deterministic HTTP mean.
