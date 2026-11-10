# PERFORMANCE

300 local projection/serialization samples: mean projection 0.393 ms (max 8.655 ms); projected JSON encoding mean 0.220 ms. Primary 70 TCP requests: mean 292.698 ms, max 1661.043 ms. Ten replay gameplay actions average 347.191 ms. Supplemental/holdout/control requests are separate datasets and are not silently mixed into these latency statistics.

Matched first-action wire sizes, disabled/enabled: before [122980, 123027] bytes; after [5426, 5426] bytes. Actual measurements include local safe response reencoding in the route adapter. These data show payload reduction, not a controlled throughput/latency improvement. No provider calls, extra resolution or database round trips were introduced.
