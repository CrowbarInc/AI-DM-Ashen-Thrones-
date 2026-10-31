# 07 — Provider Accounting

| Trial | Admissions | Dispatches | Responses | Failures | Input tokens | Output tokens | Total tokens | End-to-end ms |
|---|---:|---:|---:|---:|---|---|---|---|
| L1 | 1 | 1 | 0 | 1 | unknown | unknown | unknown | 1326.207 |
| L2 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |
| L3 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |
| L4 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |

Budget compliance: 1/4 admissions used. One admission and dispatch marker are durably recorded before the failed SDK request; completion is failed. SDK max_retries=0 observed on the actual single client. Zero SDK retries, application retries, reruns, setup provider calls, exploratory calls, model switches or response-generation admissions. Unused allowance was not spent. No further trials after failure/unknown usage.

APIConnectionError is captured by request_interpretation and response resolution metadata. Ledger error is generic provider_error; stopped reason provider usage accounting unavailable. Tokens and estimated cost are UNKNOWN, never zero. No request ID or returned model version. Application admission is certain; remote receipt/processing/billing is unknown. Recorded dispatch latency 91.72 ms excludes local setup/client construction; end-to-end 1326.207 ms includes preflight/host. No performance improvement judgment.

Important telemetry discrepancy: response metadata provider_calls.interpretation_requests and performance.provider_call_count report 0 because failure returns no provider_requests. Durable provider_budget accounting and request_interpretation.sent=true prove ONE actual application admission/dispatch. This report uses the durable ledger, not the zero completion-path counter. The prior-turn log includes historical provider records; those are reconstructed context, not new admissions. Per-process measured ledger is the accounting authority. No production telemetry fix authorized or implemented.
