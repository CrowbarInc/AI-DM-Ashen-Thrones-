# 29 — Performance

Fresh provider log, 220 calls: 145 `semantic_candidate`, 73 `expression`, 2 `interpretation`. Candidate-call input tokens: mean 4,788, p95 6,418, max 6,719. Expression calls are small (mean about 160 input tokens). Candidate-call latency mean is inside the mixed-call mean of 2.1 seconds; mixed p95 latency was 3.3 seconds and the maximum was 16.8 seconds. The interpretation target was mean input at or below 3,500 and p95 at or below 5,000. Candidate calls missed both. There was no retry storm: 145 candidate calls across 150 turns.
