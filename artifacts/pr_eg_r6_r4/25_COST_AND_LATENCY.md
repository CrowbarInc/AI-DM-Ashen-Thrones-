# 25 — Cost and Latency

| Architecture | Calls | Mean input | P95 input | Mean output | Mean latency ms | P95 latency ms |
|---|---:|---:|---:|---:|---:|---:|
| A | 176 | 1634.07 | 1700 | 213.72 | 2423.56 | 3059.366 |
| B | 0 | 0 | 0 | 0 | 0.06 | 0.096 |
| C | 176 | 599.07 | 665 | 111.38 | 1839.92 | 2705.773 |


| Sources | Architecture | Input tokens | Output tokens | Latency ms | Result |
|---:|---|---:|---:|---:|---|
| 1 | A | 1625 | 227 | 2230.812 | DIRECT |
| 1 | C | 590 | 135 | 1854.619 | DIRECT |
| 4 | A | 1724 | 227 | 2633.28 | DIRECT |
| 4 | C | 689 | 136 | 1986.069 | UNKNOWN |
| 12 | A | 1988 | 227 | 2226.786 | DIRECT |
| 12 | C | 953 | 135 | 1780.457 | DIRECT |
| 32 | A | 2648 | 132 | 1801.327 | UNKNOWN |
| 32 | C | 1613 | 135 | 2059.674 | DIRECT |

Official primary counts include all 176 diagnostic cases. B's zero provider tokens exclude manual fact authoring and any upstream production interpretation call. C adds one matching call on top of interpretation in a production design; the primary gold control masks that upstream cost. Latencies are wall time per task under concurrent load, with model/network variability. No current price estimate is claimed; dollar cost is input_tokens × input_price + output_tokens × output_price. The invalid initial run has incomplete billing evidence.

Authoring estimate, not timed measurement: if annotating/reviewing each source takes 2–10 minutes, 1,000 sources cost 33–167 hours initially, plus updates and predicate/role governance. Both B and this C require that work. Source lists grow roughly linearly in tokens with serialized source text; 1/4/12/32-source probes provide concrete usage in supplemental results. No latency or token reduction is claimed for full /api/chat.
