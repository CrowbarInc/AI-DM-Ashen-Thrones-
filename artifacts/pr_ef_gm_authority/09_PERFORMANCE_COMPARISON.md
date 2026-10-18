# 09 — Performance Comparison

Same PR-ED disposable ten-turn profiler before/after; provider disabled. Values are local measurements, not a latency improvement claim.

| Sample | Median ms | Narration function entries | External requests |
|---|---:|---:|---:|
| baseline_disabled | 87.0 | 7 | 0 |
| final_disabled | 82.0 | 6 | 0 |

Provider-disabled input/output tokens are unavailable. Function entries count attempted narration boundaries, including disabled or discarded output; they are not external requests. Persistence and prompt estimates are retained per turn in both profile JSON files. The two samples are single runs and were collected under different surrounding machine load.

| Live sample | Calls | Input tokens | Output tokens | Total tokens | Median turn ms | Retries |
|---|---:|---:|---:|---:|---:|---:|
| live_before_local_repairs | 9 | 83930 | 1312 | 85242 | 1919.461 | 1 |
| live_before_final_recall_fix | 9 | 86437 | 1302 | 87739 | 2367.9570000000003 | 1 |
| live_holdouts | 12 | 14827 | 2509 | 17336 | 2314.245 | 0 |

30 external calls were completed after explicit user approval: 9 + 9 + 12. Before approval, an aborted harness-mode attempt sent additional narration requests; its usage file is retained separately and excluded from the approved 30-call comparison. It imported an experiment that disabled interpretation; that sample is invalid for conversational acceptance. Automatic approval review initially denied the repeat; explicit payload/destination approval was then obtained. No rejection was bypassed.

Production retains the 320-token interpretation cap, existing timeout helper (45 seconds by default), narration budget and PR-ED retry/movement skips. The live harness used a bounded 25-second timeout and 1600-token narration cap; these are validation settings, not new production defaults. The old profiler's `openai_sdk_default` timeout label is stale; current source is authoritative. The new NPC recall skip uses a resolver-owned already disclosed answer and still reaches final emission.

Performance summaries now include interpretation tokens when available and do not label decline/clarify as conversational success. Aggregate tokens remain unavailable when multiple narration attempts cannot be reconstructed from a single final stamp; raw budget usage is the source for complete live totals. No before/after live speedup is claimed: the samples differ in code and behavior.
