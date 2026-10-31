PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 06 — Integrated Regression and Performance

Final focused suite: **39 passed** (21 PR-PLAY-05 checks plus 18 retained PR-PLAY-04 checks). `integrated.xml/txt` retains results. Offline HTTP positive/journal tests pass individually; HTTP negative placeholder is in this suite. Raw transport is synthetic, no provider/network trial.

## Opening matrix

| Scenario | Endpoint / visible result | Progression / requests / diagnostics |
|---|---|---|
| valid | 200, exact valid narration | latch true; turn/time 1; faction agendas +1; one request; accepted_structured_opening |
| placeholder | 422, explicit error, no gm_output | latch false; no turn/time/faction/log progression; one request; JSON failure + rejected opening |
| missing envelope | 422 | same rollback; one request; missing envelope |
| malformed / empty / truncated | 422 | same rollback; one request each; precise distinct diagnostics |
| provider exception | 422 | same rollback; one request; provider_error and rejected outcome |
| budget exhausted | 409 blocked | no dispatch/admission, no progression; provider_budget_refused |
| failure, failure, success | 422,422,200 | three admissions; two rejected outcomes and one commit; turn/time/faction increment once |
| repeated successful Start | 200 then 409 already_started | one provider request total, no second progression; repeated-start diagnostic |
| concurrent Starts | one 200, one 409 | existing persistence lock serializes; one request/commit; no duplicate progression |

Retained PR-PLAY-04 controls also cover chat-start parity, pipeline/pre-dispatch/save exceptions, retry after exception, independent market vocabulary and ordinary information fallback. Focused payload checks materialize normal initialization defaults before measurement. Failed attempts preserve all gameplay JSON values; exceptions are explicitly limited to existing save timestamps, empty-log materialization and duplicated scene-addressability initialization trace rows. Those bookkeeping writes are not represented as byte-for-byte file identity. Normal user saves were never used as the test sandbox.

## Broader slice

| Group | Passing | Failing |
|---|---:|---:|
| HTTP opening/seam/scene canon | 23 | 3 preexisting rich cases |
| Provider controls/accounting | 88 | 1 preexisting attestation |
| Structured/narration-only/retry/immutable boundary | 60 | 1 preexisting conversation assertion |
| Retry, ordinary conversation, pending action, authority | 56 | 0 |
| Review exporter | 11 | 0 |
| Total broader | 238 | 5 |

Full repository suite was not run. Groups are individually capped at 90 seconds; required original cases at 55. No test is skipped to obtain these counts. Logs/command JSONs identify exact suite files. Initial sandbox HTTP timeouts and one sandbox atomic-replace permission error were environment limitations; clean outside-sandbox guarded reruns passed the scoped checks. An isolated baseline accounting collection first lacked tools/; supplied those dependencies, reran and retained the failed setup record.

All remaining broader failures are demonstrated on earlier source: rich cases on hash-matched pre04; `test_readiness_acceptance_is_not_live_execution` and `test_raw_chat_stub_preserves_valid_and_contains_invalid` on saved entry source (`entry_remaining.txt`). The attestation remains fail-closed because reviewed source fingerprints are stale, not because admission ceased to work. The conversation case expects a stew-price limitation but gets the authored runner line. Neither is repaired or silently claimed green. No unknown failure is called preexisting.

## Performance and accounting

Synthetic local medians: parser alone 0.0047 ms; parser plus structural diagnostic construction 0.0146 ms; durable ledger observation 0.8789 ms (p95 1.2156 ms), 100 fsync writes. See performance.json for scope/iterations; this is not provider/UI latency. Durable writes can cost more on another disk. Zero provider admissions in the measurement.

No interpretation/narration operation, retry, model, prompt, output cap, response schema, persistent gameplay structure or gameplay-state mutation was added. Existing request kwargs and 600 cap are asserted in synthetic dispatch tests. All gm top-level prompt/config literals compare equal to entry. 437 protected data/experiment hashes, including normal saves and frozen ATGB, remain unchanged. No PR-EG integration. Ledger lifecycle reconciliation still bounds admissions and avoids counting diagnostic copies of token usage. Frozen source-attestation readiness remains separately red; the manual procedure uses the existing budget owner and does not claim ATGB worker readiness.
