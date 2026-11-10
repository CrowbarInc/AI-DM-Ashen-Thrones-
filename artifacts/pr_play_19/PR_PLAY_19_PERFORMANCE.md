# PR-PLAY-19 Performance
All token counts below are actual provider usage, not character estimates. Request count 1; cached input tokens 0; reasoning output tokens 0.

| Metric | PR-PLAY-17 | PR-PLAY-19 | Observed reduction |
| --- | ---: | ---: | ---: |
| Input tokens | 26,986 | 1,378 | 94.89% |
| Output tokens | 2,050 | 120 | 94.15% |
| Total tokens | 29,036 | 1,498 | 94.84% |
| Provider latency | 14.19 s | 2.261 s | 84.07% |

Provider latency uses dispatch-to-completion accounting, comparable to prior provider measurement. Direct SDK invocation measured 2.251 s. /api/start_campaign HTTP duration 4.133 s; engine reported 3912 ms. Entire harness including configuration/startup/snapshots/shutdown was 8.281 s. Initialization HTTP timing includes response transfer/processing; startup is separately documented in http_ready.json.

Captured live input has 3,220 message characters and 2,496 compact-schema characters (5,716 combined), eleven catalog entries/six required. PR-PLAY-18's ~902-token estimate was reconstructed from a smaller six-entry payload, whereas this actual initialization exposes five additional optional public entries. Tokenization of identifiers, schema and protocol overhead also differs from characters/4. This explains why the observed 1,378 input tokens exceed that estimate while remaining 94.89% below the earlier 26,986-token request. No unexpectedly large legacy context is present.

Material token/latency improvement observed in this one sample; caching contributes zero. Output is now a compact selection plan rather than narration. These are different historical requests with network/runtime variability; one sample does not establish population latency or isolate every causal factor. Current pricing was not independently verified, so cost estimate unavailable. No provider optimization or second measurement was attempted. Source: performance_measurements.json and live diagnostics/provider_response.json/provider_usage.jsonl.
