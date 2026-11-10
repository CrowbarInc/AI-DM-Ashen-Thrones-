# 11 LIVE PROVIDER RESULTS

Provider: OpenAI. Model: `gpt-4.1-mini-2025-04-14`. Existing configured adapter; two requests, zero retries. 895 input + 44 output = 939 total tokens. Provider latencies: 3937.757 ms and 1369.010 ms. No regeneration to chase PASS.

Discovery candidate:

> You study the notice board carefully and discover that the missing patrol was last seen taking the northwest mud track past the crates.

Result: FAIL in `_route_assertion` because this finite prefix adds “carefully” and uses “discover that”. Mandatory coverage PASS; deterministic fallback published. Follow-up barrel response: PASS and published. Live validated AI responses: 1; AI publications: 1. Raw outputs, model metadata, usage and publication decisions are in `gameplay_actions.json`, `provider_usage.jsonl`, and `provider_snapshot.json`.

The broad API provider switch remains disabled to isolate this existing experimental narration adapter. Upstream preflight was skipped as in the established harness; recorded adapter metadata and usage establish these two actual requests only.
