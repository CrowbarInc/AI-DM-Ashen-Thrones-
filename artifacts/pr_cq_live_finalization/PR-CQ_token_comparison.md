# PR-CQ Token Comparison

Measured usage from the Responses API. Cached input was 0 on every call. Prices confirmed before the calls from the GPT-4.1 mini model page: input $0.40 / 1M, cached input $0.10 / 1M, output $1.60 / 1M. Estimated spend for this probe: input $0.0434, output $0.0004, about **$0.0438**.

The ceiling checked before any call was 120,000 tokens at 95% input / 5% output, about $0.055, or $0.192 if the entire cap were output.

## This probe

| Call | Turn | Kind | Retry | Input | Output | Total | Latency (s) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | startup | preflight | 0 | 24 | 2 | 26 | 1.775 |
| 2 | T1 | generation | 0 | 30,877 | 66 | 30,943 | 1.994 |
| 3 | T2 | generation | 0 | 34,561 | 117 | 34,678 | 2.007 |
| 4 | T2 | generation | 1 | 42,960 | 83 | 43,043 | 2.312 |
| | | | | **108,422** | **268** | **108,690** | **8.088** |

Provider requests: 4, including preflight. Gameplay generations: 3. Retry tokens: 43,043 (39.6% of 108,690).

Turn wall time, including validation: T1 2.608 s, T2 5.358 s.

No interpretation request was made. PR-CO's preference turn and patrol turn also made none.

## Against the PR-CO probe totals

PR-CO: 295,037 tokens, 12 requests, 5 HTTP turns, retry tokens 161,822 (54.8%).

This probe is two gameplay turns plus a 26-token preflight. It is not a replay of those five turns. The lower total is mostly the shorter plan and the missing preference retry, not a measured context reduction.

## Against the two matching PR-CO turns

PR-CO turn 1 (preference) plus turn 3 (patrol question):

| | Input | Output | Total | Requests | Retry tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| PR-CO T1 + T3 | 147,966 | 358 | 148,324 | 4 generations | 81,804 (55.2%) |
| PR-CQ T1 + T2 | 108,398 | 266 | 108,664 | 3 generations | 43,043 (39.6%) |
| Difference | −39,568 | −92 | −39,660 | −1 | −38,761 |

### A. Fewer retries

PR-CO rejected the preference and spent a second generation (38,531 tokens). This probe sealed that turn on the first generation (retry tokens 0).

The patrol turn still retried. Its retry was 43,043 tokens, close to PR-CO turn 3's retry of 43,273. Both of those retries were also rejected. The token drop on this pair is almost entirely the preference retry that did not happen: 39,660 fewer tokens, of which 38,531 are that avoided call.

### B. First-request context size

Preference first input: 30,877 here, 30,970 in PR-CO. Difference: −93 tokens.

Patrol first input: 34,561 here, 35,302 on PR-CO turn 3. Difference: −741 tokens.

Turn 3 in PR-CO followed two earlier HTTP turns. Turn 2 here followed one short accepted preference. That history difference is a test condition. This probe does not claim a context-optimization change.

### C. Output length

Preference output fell from 128 tokens to 66. Patrol first output was 117 versus 120. The retry output was 83 versus 43. Output is a few hundred tokens either way and is not the source of the 39,660-token gap.

### D. Test conditions

- Two turns were planned, not eight. The request cap was 4, not 12.
- The preference sentence is the one specified for this cycle. PR-CO asked about "a dry watch inside the walls."
- Preflight is inside the 4-request count. It was 26 tokens.
- Storage was pointed at the disposable directory before the app started, so startup did not touch production saves.
- No parallel session and no second model.

Do not treat 108,690 versus 295,037 as a rate that will hold for a longer session.
