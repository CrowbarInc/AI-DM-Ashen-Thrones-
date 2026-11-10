# 17 — Provider and latency

This cycle made **0 live provider requests** and used **0 provider tokens**. The discretionary budget of 4 requests and 8,000 tokens was not used. PR-PLAY-71's 15 requests and 189,036 tokens were not repeated. Stubbed and deterministic text must not be described as live narration.

| Measure | Value |
| --- | --- |
| HTTP lifecycle mean server time | 159.1 ms |
| HTTP lifecycle maximum server time | 545.1 ms |
| Browser host mean middleware time | 90.9 ms |
| Browser host maximum middleware time | 397.7 ms |
| Atomic retry overhead when three sleeps run | 130 ms of scheduled delay, plus replace work |
| Browser-visible paint time | Not instrumented |

HTTP status time and middleware time are not browser-visible latency. Each browser step was observed to finish in the page before the next action was sent.
