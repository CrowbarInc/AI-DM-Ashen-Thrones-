# PR-PLAY-30 performance
Offline application run: 1.982s; opening 0.176s. Actions: {"T1": 0.16686519999348093, "T2": 0.4025636000005761, "T3": 0.13752499999827705} seconds. These are local mocked timings, not live-provider pacing estimates.

Actual live-provider requests 0; input/output/total billed tokens 0/0/0; per-request live usage not applicable; retries 0; fallback models 0; AI judges 0. Budget 0/7, compliant. Mocked opening requests 1, interpretation requests 2, expression requests 1. Turn 3 has zero of each. Mock helpers contain synthetic token values; they are not actual provider usage.

Offline scenario test passed (meaning expected boundary behavior observed); 29 security controls passed. Initial harness setup error occurred before gameplay; subsequent offline run is not a provider retry. No repeated scenario after decisive semantic stop. performance.json holds machine-readable measurements.
