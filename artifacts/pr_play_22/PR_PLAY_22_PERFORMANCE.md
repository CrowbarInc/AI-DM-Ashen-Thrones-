# PR-PLAY-22 performance

| Request | Purpose | Model | Input | Output | Total | Cached | Provider seconds | API seconds | Status | Retries |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| 1 (opening) | primary_turn | gpt-4.1-mini-2025-04-14 | 1378 | 120 | 1498 | 0 | 2.756 | 3.812 | completed | 0 |
| 2 (T1) | interpretation | gpt-4.1-mini-2025-04-14 | 2306 | 203 | 2509 | 0 | 2.041 | 2.625 | completed | 0 |
| 3 (T2) | interpretation | gpt-4.1-mini-2025-04-14 | 2456 | 233 | 2689 | 0 | 2.461 | 3.359 | completed | 0 |
| 4 (T3) | interpretation | gpt-4.1-mini-2025-04-14 | 2615 | 184 | 2799 | 0 | 2.630 | 3.672 | completed | 0 |

T4: zero provider requests/tokens; API latency 0.250s. All four provider responses completed. No transport retries, judge calls or alternate model dispatches.

Totals: 8755 input + 740 output = 9495 tokens; 4 live requests. Opening: 1498 tokens. Ordinary: 7997 tokens over 3 provider requests / 4 API turns. Mean ordinary tokens: 1999.25 per attempted turn; 2665.67 per ordinary provider request.

Ordinary API latency mean 2.476s, maximum 3.672s. Live experiment duration 20.562s from worker spawn through shutdown. Offline readiness duration 2.453s separately; report-writing time excluded. Provider times measured around real SDK invocation; durable-accounting latency is separately retained in performance_measurements.json. API latency excludes subsequent snapshot requests.

PR-PLAY-19 reference: opening 1378 input / 120 output / 1498 total, ~2.26s. This opening has identical usage, 2.756s provider time. Ordinary requests: 2509 / 2689 / 2799 tokens (1.67–1.87x opening), despite producing no NPC dialogue.

Context contributors (exact assembled request content characters, not token estimates): ordinary system interpretation instructions 5168 characters each; ordinary user JSON 3113, 3784, 4508 characters. Opening system 1381 / user 1839. The interpreter system instructions are the largest single content segment. User context grows with the quoted refusal and recent exchanges. Response JSON schema adds serialization overhead. Requests preserve full schemas and content for independent token analysis; no unsupported per-section token counts are inferred. No narration-generation context was exercised.
