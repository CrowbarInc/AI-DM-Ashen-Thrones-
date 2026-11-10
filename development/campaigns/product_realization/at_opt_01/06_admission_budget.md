# Admission and Budget Enforcement

The 3,000-token figure was a verification-cycle instruction. It was not the ceiling the process enforced.

## Where 3,000 was stated

The PR-PLAY-79D-F3 task told the agent that live provider use was optional and capped at 3 requests and 3,000 tokens, with 0 openings and 0 retries. That instruction is in the F3 session transcript summary (`agent-transcripts/5bab8166-a3b5-4fe4-9965-8b13093bace3`, compaction segment). The F3 reports then call 23,377 tokens a breach of “this cycle’s 3,000-token cap.”

`http_acceptance.py` set different numbers:

- `ASHEN_PROVIDER_REQUEST_LIMIT=4` at start and again before the continuation
- `ASHEN_PROVIDER_INPUT_TOKEN_LIMIT=100000`
- `ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT=100000`
- `ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT=200000`
- request limit `0` only for the Gate Guard refusal

The 3,000-token cap was documented in the task and in the cycle report. The harness did not enforce it. Runtime admission enforced the harness ceilings.

## What runtime admission actually checks

`provider_budget.limits` reads the four environment variables. Input, output, and total default to 8,000 / 2,000 / 10,000 only when a request limit is set and those variables are absent. The script set all four, so the defaults did not apply.

`admit_request` runs before dispatch. It refuses when any of these projected sums exceed the ceiling:

- request count
- recorded input plus reserved input plus this attempt’s `estimated_input`
- recorded output plus reserved output plus `max_output`
- recorded total plus both reservations plus `estimated_input + max_output`

`gm.call_gpt` estimates input as `(len(json.dumps(messages)) // 3) + 64` when accounting is active, and reserves `max_output` of 600 for ordinary narration. The check uses that estimate, not the provider’s later token count. The provider count is applied in `finish`, after the call returns. If the recorded total then exceeds the ceiling, `_stop` blocks later admissions. It cannot unsend the call that just completed.

F3’s ceilings were 100,000 and 200,000. An estimate near 28,000 plus a 600-token output reservation is inside those ceilings. Admission admitted the attempt. Recorded consumption of 23,377 was stored after dispatch and did not trip a 200,000 ceiling.

The refusal path itself works. The same process, with request limit 0, refused “Good day, Gate Guard.” before dispatch: 0 requests, 0 tokens, operational refusal, pointer unchanged. Deterministic ceiling tests in the F3 report cover request, input, output, total, and missing-estimate refusals. Those tests were not the HTTP continuation’s ceilings.

## Earliest point that should have stopped the call

The continuation was still local when `http_acceptance.py` set the ceilings back to 4 / 100,000 / 100,000 / 200,000. That is the earliest controlled point. A total ceiling of 3,000, or an input ceiling of 3,000, would have been visible to `admit_request` before `responses.create`.

The reconstructed no-resolution prompt estimates 28,031 tokens. That estimate exceeds 3,000 by a wide margin. The formula overshoots the recorded 22,777, so the direction of the error on this prompt is toward refusal, which is the fail-closed direction. This is still a reconstruction. The captured message bytes were not retained, so the exact estimate the process computed is UNKNOWN. Given recorded input of 22,777 and an estimator that uses bytes/3, an estimate under 3,000 is not plausible for this prompt.

A production primary-turn ceiling of 3,000 would also refuse the recorded openings at 25,294 input tokens. The 3,000 figure is a verification budget. It is not a viable production cap for `gm.call_gpt`.

## Fail-closed mechanism to add later

Do not implement it in this audit.

1. Verification scripts copy the cycle’s stated request and token caps into `ASHEN_PROVIDER_REQUEST_LIMIT`, `ASHEN_PROVIDER_INPUT_TOKEN_LIMIT`, `ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT`, and `ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT` before any live continuation.
2. Keep the existing pre-dispatch check. Refuse when `estimated_input + max_output` exceeds the remaining total. Return the existing budget-refusal sentence. Do not dispatch.
3. Apply recorded usage only as the post-completion stop that already exists.
4. Log the estimate, the ceiling, and the refusal reason on the ledger row. Do not log the prompt.
5. A provider-free test builds a primary-sized message list, sets the total ceiling to 3,000, and asserts `sent` is false and the provider client is not called.

The harness budget and the production admission controller are different layers. Production already refuses when its own ceilings are crossed. F3 crossed the written cycle budget and stayed inside the ceilings the process was given.
