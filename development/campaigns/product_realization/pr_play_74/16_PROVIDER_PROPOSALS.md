# PR-PLAY-74 — 16 PROVIDER PROPOSALS

Two actual gpt-4.1-mini requests used the existing configuration, OpenAI client patterns and provider_budget admission/dispatch ledger. Total 360 tokens, no retries. Both proposals validated, neither committed nor published (shadow evaluation only). provider_results.json and provider_data/provider_usage.jsonl retain proposal, verdict, request usage and latency. Malformed responses/timeouts have deterministic rejection tests. Normal gameplay uses deterministic constrained proposals; automatic live-provider proposal commitment remains deferred.
