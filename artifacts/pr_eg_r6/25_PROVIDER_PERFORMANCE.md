# 25 — Provider Performance

Engine calls only. Player-generation and judge calls are outside this budget and are stored on the turn rows.

Calls: 142. Per turn mean: 1.1932773109243697.
Input tokens per call mean / p95: 1795.6971830985915 / 2220.
Input tokens per turn mean / p95: 2256.5398230088495 / 2220.
Output tokens per call mean: 143.71830985915494.
Turn latency mean / median / p95 / max ms: 2716.20425210084 / 2465.359 / 4898.392 / 12271.412.
Provider-call latency p95 ms: 2811.008.
Retry-purpose calls: 1.
Models: ['gpt-4.1-mini-2025-04-14'].

Targets were mean turn input <= 3500, p95 turn input <= 5000, p95 turn latency <= 5000 ms, and no strict-social retry loop. Gate 12 records whether this run met them. Safety was not relaxed to meet them.
