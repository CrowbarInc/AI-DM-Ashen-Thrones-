# 15 — Performance Comparison


FRESH matrix: 130 successful Responses calls, 62,542 input tokens and 3,738 output tokens; median per-call elapsed time 805.735 ms. One separate access probe used 473 input / 25 output tokens and 2,410.8 ms. One failed sandbox attempt has no usage; it was not silently discarded. These counts exclude rejected, never-executed baseline requests and local scripted captures. Output cap 500; no SDK or semantic retries in the isolated matrix. One provider response per turn. The elapsed interval includes the provider request, JSON parsing and the initial lightweight local validator (and first-use imports). It excludes the later decision/preseal analysis, interpretation, full final gate and save costs; it is not pure network latency.

Matched six-case comparison, two repeats per case, unchanged system policy:

| Context | n | Input min | Input max | Input mean | Median ms | Mean output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| minimal | 12 | 355 | 382 | 368.8 | 764.0 | 30.2 |
| compact | 12 | 450 | 478 | 464.2 | 889.7 | 27.8 |
| rich | 12 | 585 | 613 | 599.2 | 773.3 | 28 |

The sizes were measured from actual provider usage, not imposed input ceilings. Minimal omitted redundant identity/provenance; compact retained these; rich added scene/authorization metadata. All can paraphrase; minimal/rich also invent gate security conditions. Rich B1 admitted uncertainty twice, but sample n=2 does not justify choosing rich as safer. The rich case still fails other boundaries. Smaller input is feasible, yet no safe minimum is established.

HISTORICAL PR-EG-R1 complete-turn measurements (include interpretation where present; these are NOT latency-matched calls):

| Sequence | Turn | Question | Total calls | Total input tokens | Whole-turn ms |
| --- | --- | --- | --- | --- | --- |
| primary | 2 | I ask Sergeant Mara what the street beyond the gate is called. | 2 | 26319 | 4783.5 |
| primary | 5 | Do you prefer the morning or the evening? | 1 | 24606 | 2534.6 |
| second | 2 | Sergeant Mara, is there a name for the road past the barred gate? | 1 | 25248 | 2102.8 |
| second | 4 | Do you like the quiet of morning better than evening? | 1 | 24279 | 2613.9 |

LOCAL captured strict-social content totals 24,104 and 23,611; system 893 each, remainder user payload. Provider message framing excluded. Ordinary follow-up reuse may use zero calls but deliver a quote or uncertainty rather than an explanation; exact_preference_trace.json shows that tradeoff. Future performance qualification must compare identical authorized tasks and final delivered quality, including interpretation, validation, retries and persistence. The roughly 98% content reduction suggested by isolated 450–610-token prompts is arithmetic potential, not a measured production saving or guaranteed latency reduction.

Fresh full-size baseline generation was blocked by review. No new full-prompt latency was measured. Per-section local counts and historical actual-provider usage are the available comparison, with their limits explicit.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
