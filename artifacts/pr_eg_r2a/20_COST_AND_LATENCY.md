# 20 — Cost and Latency

FRESH token and wall-time measurements, including the initial paid format failure:

| Strategy | Provider requests | Successful candidate evaluations | Input tokens | Output tokens | Amortized ms/candidate |
| --- | --- | --- | --- | --- | --- |
| B | 22 | 116 | 10688 | 11002 | 722.9 |
| C | 10 | 60 | 7564 | 5301 | 654.4 |

A: zero provider calls/tokens; median hot local check 0.002050 ms. B host exact-support check median 0.005062 ms, plus annotation provider cost. B one-candidate annotation requests: [1315, 1290] ms. These single-call measurements do not establish C interactive latency. Most C requests are six-candidate batches; amortized per-candidate time is throughput, not response time for a player. D is replay, with hypothetical 4.9% call avoidance; no integrated savings were measured.

Per successful annotation/evaluation including failed-format overhead: B 92.1 input / 94.8 output tokens; C 126.1 / 88.3. Batch median and observed p95, raw all-request costs, repeat counts and exact usage are in `cost_measurements.json` and `provider.jsonl`. Provider cache usage is retained; simple summed tokens are not an invoice.

Dollar cost per candidate is `(input_tokens * applicable_input_price_per_million + output_tokens * applicable_output_price_per_million)/1e6`, adjusted for actual cached-token rates. Account-specific billing/rates are not measured and no guessed price is supplied. No fresh dialogue generation baseline exists in this cycle; B measures annotation overhead rather than a free structured generator's combined turn price.

Expected sequential production-turn model (INFERENCE): generation G + validation V + host H; with at most one allowed regeneration probability p, expectation is `G+V+H + p*(G_retry+V_retry+H_retry)`. Calls are typically 2, or 4 with regeneration/revalidation, excluding interpretation and existing route calls. Structured generation might fold metadata into G but has unknown token overhead here. Hybrid expectation is `G+H+(1-q)*V` before retries, where observed finite-corpus fast-path q≈0.049; it does not fix C safety.

Observed handler probes used retries in 3/7 scenarios; among candidate-requested cases, 3/5. This tiny artificial repeated-candidate setup is not a production retry probability. Initial B format failure was 1/22 annotation attempts across evolving transport handling, not a stable failure-rate estimate. Recovery/timeout policy should abstain and retain diagnostics; blindly retrying a failed safety classifier is not justified. Responsiveness under realistic sequential calls, smaller/local models and cold start remain unqualified.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
