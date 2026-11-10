# Validation metrics

Scored corpus: 83 lines. Negative fabrications: 49. Positive controls: 24. Paraphrases: 7. Ambiguous: 3. Denominators are line counts, not a hidden sample.

| Metric | New check | Previous `validate_generated_response` |
| --- | --- | --- |
| Consequential fabrication detection | 49 / 49 | 15 / 49 |
| False negatives | 0 / 49 | 34 / 49 |
| False positives | 0 / 31 | not the same control definition; the combined gate still rejects P1 and S21 |
| `REVIEW_REQUIRED` | 2 / 83 (R1, R2) | the previous checker has no such decision |
| `VALIDATION_ERROR` | 0 / 83 | not applicable |
| Paraphrase acceptance | 7 / 7 | P1 is rejected by the geography rule |

Latency, `validate_consequential_narration` only, one call per scored line:

- Sum 14.003 ms
- Mean 0.169 ms
- Max 5.8 ms

The metrics function wall time, including authority construction and the previous checker, was 97.62 ms. No figure here is a percentage detached from these counts.

Provider use: 0 requests, 0 tokens. No live narration call was made. Deterministic replay of the known sentences is the right test. PR-PLAY-53 already showed that the provider can write prose.

Outside the 83, `residual_probe.json` records one false negative: "You find a ribbon beneath the board." passes. That line is not in the 49 and is not folded into the detection rate.
