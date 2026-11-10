# Browser-visible latency

Measured on the physical-action turn only. Later turns do not have a `performance.now` capture. Their browser intervals are unavailable.

Browser clock is `performance.now` on one document. Values are milliseconds from navigation.

| Mark | Value |
| --- | --- |
| T0 submit | 31804.40 |
| T1 fetch start | 31809.30 |
| T6 fetch end | 35947.40 |
| T7 first player-facing paint | 35948.20 |
| Later log refresh | 36257.10 |

| Interval | Result |
| --- | --- |
| Browser submission overhead (T1 − T0) | 4.90 ms |
| Fetch duration (T6 − T1) | 4138.10 ms |
| Browser render overhead (T7 − T6) | 0.80 ms |
| End-to-end player-visible (T7 − T0) | 4143.80 ms |
| Server request, `perf_counter` | 4115.47 ms |
| Provider call duration | 1936.353 ms |
| Other server work inside that request | 2179.12 ms |
| Server pre-provider overhead | unavailable |
| Server post-provider overhead | unavailable |
| Calibrated network overhead | unavailable |

Other server work subtracts the provider-client duration from the middleware duration. Both durations are inside the server process, and the provider call sits inside the request. The remainder is not split into time before the provider and time after it, because the middleware did not stamp the provider start.

T0 wall `1794143911358` and server receive `1794143911.3666606` are different clock APIs. They were not calibrated, so their difference is not reported as network overhead.

The paint at 36257.10 ms repeats the same GM sentence after a log refresh. It is not a second publication. Snapshot create took 568.51 ms on the server and snapshot load took 453.04 ms, both with zero provider rows. Dialogue, first examination, and repeat examination server durations were 4054.42 ms, 2613.36 ms, and 3301.16 ms.
