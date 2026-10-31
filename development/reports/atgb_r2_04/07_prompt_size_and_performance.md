# 07 — Prompt Size and Performance

| Surface | Before characters | After characters | Absolute delta | Percentage delta |
|---|---:|---:|---:|---:|
| Existing appended production instruction | 4660 | 5102 | +442 | +9.485% |
| Effective system message | 4726 | 5168 | +442 | +9.353% |
| Full compact request + schema S02.2 | 11148 | 11590 | +442 | +3.965% |
| Full compact request + schema S02.3 | 11425 | 11867 | +442 | +3.869% |
| Full compact request + schema S02.4 | 11574 | 12016 | +442 | +3.819% |
| Full compact request + schema S05.3 | 11511 | 11953 | +442 | +3.840% |

Appended instruction chars/4 estimate: **1165 → 1276 tokens**, +111 (+9.528%). Full effective request estimates and deltas are in prompt_sizes.json. These are explicitly rough character-based estimates, not measured model tokens or reliable language-specific tokenizer output. tiktoken is unavailable in the local test environment (ModuleNotFoundError); no encoding download, package install or provider call was used. Production's existing conservative UTF-8-bytes/3 + 64 preflight estimate also remains unchanged and is captured per effective request, not mislabeled as measured tokens.

The replacement adds 442 characters / roughly 111 tokens, about 4% of the reconstructed full requests, while replacing existing guidance rather than appending another section. This modest absolute increase preserves the required distinctions and does not add a provider call, response stage, context store or payload field. The existing single interpretation request and host response architecture remain unchanged. No further wording optimization was undertaken after the bounded checks passed.

Actual provider admissions/calls, live inference, retries and connectivity diagnostics in this pass: **zero**. Local request stubs are not provider calls. Expected performance impact is limited to the modest additional input length within the same request; latency/cost/quality impacts are unmeasured and no numerical latency improvement is claimed. No future live-call authority is implied.
