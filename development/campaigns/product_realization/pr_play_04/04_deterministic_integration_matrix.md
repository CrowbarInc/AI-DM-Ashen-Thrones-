# 04 — Deterministic Integration Matrix

Command:

`python -m pytest tests/test_pr_play_04_opening_integrity.py -q --tb=line`

Result: 18 passed, exit 0, about 4.7 seconds.

These checks use a deterministic OpenAI stub and the production `call_gpt`. They describe host behavior under controlled responses. They do not show that a live model will emit a valid opening.

The valid narration restates authorized Cinderwatch seed sentences. An earlier paraphrase was rejected by the existing `undeclared_consequential_claim` audit even though the prose looked like an opening. The test was corrected to the narration the standalone script already accepted. The audit was not weakened.

## Matrix A — Response acceptance

| Provider result | Outcome |
| --- | --- |
| Valid structured opening | HTTP 200, provenance `initial_generation`, exact text |
| Missing envelope (plain prose) | HTTP 422 `opening_failed`, no `gm_output`, state unchanged, 1 SDK call |
| Malformed JSON | HTTP 422, state unchanged |
| Incomplete envelope | HTTP 422, state unchanged |
| Truncated JSON | HTTP 422, state unchanged |
| Empty response | HTTP 422, state unchanged |
| Provider exception | HTTP 422, reason `provider_opening_not_delivered`, state unchanged, 1 call |
| Budget exhaustion before dispatch | HTTP 409 `blocked`, 0 SDK calls |

Player failure text contains “could not be generated” and does not claim that anyone answered.

## Matrix B — State integrity

For every failure above, the snapshot matches the pre-attempt baseline: `campaign_started` false, turn 0, `time_pressure` 0, faction pressure 2/2/1, agendas 0, no faction events, log length 0.

Also covered: exception before `call_gpt` (0 SDK calls), exception inside the pipeline, and `OSError` on the success `save_world`. Each restores the baseline.

Post-change standalone confirmation is in `artifacts/pr_play_04/post_change/`. `missing_envelope` is HTTP 422 with null player text and unchanged state. `pipeline_exception` still raises and no longer leaves pressure or faction ticks. `valid_structured` remains HTTP 200 with one progression.

## Matrix C — Retry and repetition

| Scenario | Result |
| --- | --- |
| Success, then Start again | Second HTTP 409 `already_started`, no second opening, turn stays 1 |
| Failure, failure, then success | Three SDK calls, progression once (turn 1, pressure 1, agendas 1) |
| Provider exception, then success | Two calls, turn 1 |
| Budget limit 0 | 409 before dispatch |
| Budget limit 1, then another Start | First invalid opening consumes the admission (1 call, HTTP 422). Second is 409 with no further call |
| Two concurrent Starts | Statuses 200 and 409, one SDK call, turn 1 |

Token ceilings in the budget tests are raised so the request count is the binding limit. The default output ceiling equals the narration cap and a large prompt estimate can refuse the first call for tokens. That is accounting behavior, not an opening-acceptance defect.

## Matrix D — Second fixture

`market_quarter` is an existing scene. Its opening uses the existing seed sentences: “A moneylender's house flies noble colors. Canvases snap in the wind over the market stalls.” Invalid text leaves turn 0. The valid envelope then commits turn 1 and `campaign_started`. No new lore was added.

## Matrix E — Ordinary compatibility

`safe_nonresolution` for a non-opening observe/answer is not classified as an opening rejection. Seam and ordinary start tests that use a contract-valid stub still complete. See report 06 for the HTTP slice that still fails.
