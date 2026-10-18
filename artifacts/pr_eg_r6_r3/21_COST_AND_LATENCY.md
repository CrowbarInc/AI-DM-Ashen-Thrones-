# 21 — Cost and Latency

Interpretation only.

| Architecture | Calls | Mean input tokens | Mean output tokens | Mean latency ms | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| A | 132 | 1900.8 | 160.0 | 2015.4 | 2514.901 |
| B | 132 | 850.1 | 109.7 | 1696.4 | 2112.453 |
| C | 132 | 703.8 | 66.7 | 1484.8 | 1872.269 |

C is the cheapest of the three. Production narration cost is not included. A's previous live path sometimes added expression and strict-social calls; those are unchanged and outside this comparison.
