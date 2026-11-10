# Latency analysis

Milliseconds. None means absent/not applicable, not an inferred zero.

| Turn | Resolution seam | Projection | Context+fallback | Provider adapter | Validation | Publication assembly | Server | HTTP client |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 247.321 | 0.834 | 0.239 | 10846.592 | 169.373 | 1.065 | 13275.452 | 13506.554 |
| 2 | 156.592 | 0.438 | 0.215 | 2428.251 | 25.011 | 0.081 | 3968.554 | 4243.976 |
| 3 | 198.325 | 0.416 | 0.281 | None | None | 0.139 | 1246.813 | 1532.956 |
| 4 | 230.19 | 0.339 | 0.19 | 2542.266 | 103.846 | 0.046 | 4325.639 | 4703.698 |
| 5 | 195.883 | 0.383 | 0.196 | None | None | 0.036 | 1350.661 | 1721.253 |

HTTP mean 5141.687, max 13506.554. Frontend render
time NOT TESTED. Client-minus-server includes transport and JSON decoding,
not isolated network latency. Resolver timing covers the noncombat seam; normal
orchestration/persistence and uninstrumented work remain in the total.

First adapter interval: 10,846.592ms; admission/completion ledger: 3,453.994ms.
Different scopes: adapter includes setup before admission. Neither is claimed
as isolated network latency. Later adapter intervals: 2,428.251/2,542.266ms.
Concurrent regression makes PR61 comparison uncontrolled; mean/max worsened
despite shorter candidates. Fast paths remove two requests but still take
1.533s/1.721s. No broad optimization or causal speedup claim.

Live context_build_ms includes fallback assembly. Final instrumentation splits
assembly_ms for future runs; no more live calls were made after that telemetry
change or the offline-preview scope fix. With publication=1, final fallback
wording is the same as the captured live run, covered by offline tests.
