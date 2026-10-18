# PR-DP Cost Analysis

Actual live interpretation usage: 3 requests, 1804 input tokens, 695 output tokens, 2499 total tokens.

Ceilings were 8 requests, 8,000 input tokens, 3,000 output tokens, and 11,000 total tokens. Provider-reported usage was required. No price is stated.

Additional cost was not measured in PR-DP:

- Authoritative resolution: not run. Token cost is unknown. The existing resolvers are local code and do not themselves call a provider.
- Narration: not run. No narration token count was measured in this cycle.
- Validation retries: not run. The live procedure forbids automatic retries, so retry cost is zero for this cycle and unknown for a future slice.
- Recovery: not run.

PR-DN previously measured interpretation-only usage at 12 requests and 11,157 total tokens. That figure is a prior measurement, not a price, and it is not a complete-turn cost.

Complete-turn affordability is not claimed.
