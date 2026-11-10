# Provider efficiency

PR-PLAY-79B baseline was 23 requests and 39,611 tokens, of which the opening was about 26,956.

This cycle used one opening of 26,657 tokens. Gameplay HTTP tokens were 9,625. Browser gameplay added 1,651. Combined gameplay tokens were 11,276 across 17 published live responses (7 HTTP dialogue, 5 HTTP narration, 5 browser dialogue), about 663 tokens per published live response.

HTTP gameplay latency over 17 turns: mean 1,773.1 ms, p95 3,592.0 ms, max 4,068.9 ms. Opening 12,718.1 ms.

Browser-visible chat latency for the five lines: 2,615, 1,578, 1,583, 1,508, and 1,578 ms. Mean 1,772 ms. Maximum 2,615 ms.

The request count is exactly the suggested ceiling of 25. The token total is under 50,000. No second opening was generated.
