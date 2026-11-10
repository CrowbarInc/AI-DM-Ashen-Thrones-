# PR-PLAY-14 Performance

| Metric | Result |
|---|---|
| Live harness invocations | 1 |
| Provider dispatched/successful/failed requests | 0 / 0 / 0 (journal-derived) |
| Input/output/total tokens | 0 / 0 / 0 attributable provider usage; native counters unavailable |
| Total provider latency | 0 dispatched-provider time; native sum unavailable |
| Average/longest provider latency | N/A: zero requests |
| Runner measured elapsed | 31.312 s (excludes final evidence export) |
| Startup deadline | 30 s |
| Completed player turns | 0 |
| Requests per completed turn | Undefined (0/0) |
| SDK/host retries; judge calls | 0 / 0; 0 |
| Estimated dollar cost | No dollar estimate: no requests and no pricing metadata used |

Principal observed bottleneck: application HTTP readiness never established before startup timeout. It was not provider latency or request-budget exhaustion. Ledger initialization occurred at 15:04:22.365378Z, 3.610480 seconds after runner timestamp; this interval includes setup/imports and is not a pure application startup measurement. The remaining startup time cannot be split reliably between application initialization, controller polling and environment effects.

Application processing, validation overhead and harness overhead have no separate native timing breakdown. End-to-end tool/process duration and export duration were not independently instrumented; 31.312 seconds is the captured runner measurement, not a precise full launcher wall clock. Retry overhead was zero. No response latency exists from which to assess ordinary interactive tolerability. The observed startup did not deliver a usable session; interactive gameplay performance remains INCONCLUSIVE.

Budget limits unchanged: 6 requests; aggregate 200000 input, 20000 output, 220000 total tokens. Per-response opening/ordinary/interpretation caps 3000/600/320. Six-request scope can prevent five-turn completion in a functioning run; it did not cause this interruption.
