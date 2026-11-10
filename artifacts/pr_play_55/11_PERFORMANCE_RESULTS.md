# Performance

No provider request. No additional tokens. No new provider dependency.

Comparable figures are untraced. A loop that also ran `tracemalloc` averaged 0.5431 ms and is reported only as an overhead measurement. Peak traced allocation during that loop was 3,160,442 bytes. That is the tracer's view of the loop, not a new retained cache in the validator.

| Corpus | How measured | Average | Median | Maximum |
| --- | --- | --- | --- | --- |
| Development, 40 lines, one pass | `evaluation.json` | 0.1976 ms | 0.1711 ms | 0.7443 ms |
| Development, 1600 calls | untraced repeat | 0.1662 ms | 0.1636 ms | 4.7721 ms |
| PR-PLAY-54 corpus, 83 lines, one pass | `evaluation.json` | 0.1961 ms | 0.1582 ms | 0.6976 ms |
| PR-PLAY-54 corpus, 3320 calls | untraced repeat | 0.1833 ms | 0.1587 ms | 2.5002 ms |
| Holdout, 70 lines, the one official pass | `evaluation.json` | 0.2129 ms | 0.1103 ms | 6.8801 ms |

The holdout maximum is the first call of that process. The median of the same pass is 0.1103 ms.

PR-PLAY-54's reference average was about 0.169 ms per scored statement. The untraced development average here is 0.1662 ms. Throughput on that repeat was about 6007 validations per second.

The extra work is a few more frame tests and a geography alias fold. It did not require a second model call.
