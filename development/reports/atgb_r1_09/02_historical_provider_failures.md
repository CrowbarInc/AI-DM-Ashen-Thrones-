# 02 — Historical Provider Failures

| Historical attempt | Exception | Defensible category | Cause / connection phase | HTTP status / request ID | Model output / usage | Admission / retries | Dispatch latency |
|---|---|---|---|---|---|---|---|
| R1-03 L1 | APIConnectionError | INDETERMINATE; connection failure reported | not retained / unknown | unavailable / unavailable | none / unavailable | 1 / 0 | 625.517 ms |
| R1-03 L2 | InternalServerError | Provider response failure (SDK category) | not retained / unknown | exact status unavailable / unavailable | none / unavailable | 1 / 0 | 6519.199 ms |
| R1-08 L1 | APIConnectionError | INDETERMINATE; connection failure reported | not retained / unknown | unavailable / unavailable | none / unavailable | 1 / 0 | 91.72 ms |

InternalServerError supports the SDK server-response category but does not recover an exact status, body, headers or request ID. A server error response is distinct from a successful model response. APIConnectionError alone cannot distinguish DNS, TCP, proxy, TLS or another underlying cause. No credential rejection is established by these artifacts. No timeout exception is recorded; short elapsed time alone does not prove the connection phase or configured timeout. Current 45-second timeout is not retrospectively asserted as measured historical configuration.

Historical provider_budget completion records normalize error to provider_error, while trace return records retain the exception class. Underlying __cause__, wire-level response and HTTP metadata were not captured. Failed dispatches count as admissions despite missing usage; historical ordinary response completion counters can report zero. Never replace durable admission counts with those counters. All three failures retained one admission and zero SDK retries, with no returned model version. The model field in failed ledger records is the configured fallback, not an observed provider model.

Current evidence establishes a local DNS prerequisite failure before any provider dispatch. It makes a DNS explanation for older connection failures plausible but does not demonstrate the same cause across sessions. There are no current provider failures, current provider status codes or current latency samples to compare. Detailed extracted fields and original source paths are in historical_provider_failures.json; original trace/accounting files are packaged under their original paths.
