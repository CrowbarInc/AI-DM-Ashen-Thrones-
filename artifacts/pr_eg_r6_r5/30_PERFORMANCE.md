# 30 — Performance

Costs are separated. Gold-arm tokens are not production cost. No dollar price is claimed. Cost in currency is `(input_tokens * input_price + output_tokens * output_price) / 1_000_000` once a price is chosen.

## Production baseline (`baseline.jsonl`)

| Measure | Value |
|---|---:|
| Turns | 164 |
| Provider calls | 205 |
| Calls per turn | 1.25 |
| Input tokens | 464239 |
| Output tokens | 37057 |
| Retries | 0 |
| Turn latency ms | mean 2729, median 2517, p95 4226, max 8195 |
| Call latency ms | mean 1859, median 1861, p95 2790, max 4193 |

Purpose mix: semantic_plan 158, expression 27, interpretation 6, contract_interpretation 13, strict_social 1.

The semantic plan is the standing cost. Expression runs on a minority of turns. Most failures return a host line without a second call.

## Diagnostic interventions (`interventions.jsonl`)

Calls 146, input tokens 33129, output tokens 3267. These replay a cached plan. They are not a forecast of production cost after a repair.

The discarded schema-rejected run made 26 additional sent calls. Those calls are not in the totals above.

## Expression control (`expression_control.jsonl`)

Calls 54, input 4761, output 802, turn latency ms mean 1276, median 1225, p95 1524, max 2150. Isolated experiment.
