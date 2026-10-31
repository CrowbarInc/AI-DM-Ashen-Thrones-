# 07 — Regression and Performance

Completed suites (JUnit/raw commands and logs under artifacts/pr_play_02):

| Slice | Result |
|---|---|
| New production-control tests | 30 passed; 3.428s |
| Existing non-HTTP accounting/preflight/reset/correction/pending/grounding/evidence/authority/diagnostics/efficiency | 301 passed, 1 preexisting failed, 302 executed; 33.047s |
| Existing routing configuration/runtime/escalation and interpretation compatibility | 23 passed, 1 preexisting failed, 24 executed |
| Completed total | 354 passed, 2 preexisting failures |
| Explicit HTTP lifespan test | Environment-blocked at 15s, killed; not passed |

Preexisting failure 1: test_readiness_acceptance_is_not_live_execution rejects the
ATGB reviewed source fingerprint manifest. Reconstructing the effective entry game/
surface reproduces rejection before this pass (reviewed_application_surface_changed).
Current intended implementation changes also invalidate its older owner/core hashes.
readiness_comparison.json records both. Manifest remains unchanged under the frozen
ATGB restriction. This prohibits claiming a freshly attested ATGB worker run; the
manual application does not use that offline worker readiness gate. Static inventory
and all seven production-boundary tests establish the scoped manual safeguards.

Preexisting failure 2: test_call_gpt_attaches_route_metadata_and_merges_existing_metadata
expects exact metadata without the preexisting provider_call field. The identical
failure reproduces with saved entry source (entry_compatibility.xml/txt). Baseline
overlay setup initially lacked static/; that setup error was corrected only in the
disposable overlay, and the actual baseline assertion then reproduced. No test
expectation or unrelated implementation was altered to force green.

Initial mixed regression attempt timed out at 90s after reaching the HTTP ten-turn
test; incomplete output is retained in regression.txt. It has no completed JUnit
result and is not added to pass counts. Completed nonhttp.xml excludes that HTTP
test and lifespan test. One separate lifespan test was bounded to 15s (http_result.json)
and stalled at the known TestClient boundary. No infrastructure debugging followed.
No new unexpected regression in the executed slices. Full suite not run.

Authority checks cover evidence authorization, pending revisions/confirmations,
nonmutating conversation, reset isolation, state integrity, provider exceptions,
admission failure and existing diagnostics. Focused cap tests block state/resolver
access before exhausted submissions. Protected file and inventory checks cover
normal data, frozen ATGB inputs and experiments; see integrity.json.

Performance: no new provider requests, interpretation stages or narration stages.
The admission lock/reservation/fsync are existing behavior. A local five-repeat,
50,000-call microbenchmark measured the added supplementary submission gate:
default 1.290 microseconds; enabled 6.207 microseconds; delta 4.918 microseconds.
This measures the local gate only, not provider latency or the existing durable
ledger/fsync. Additional telemetry fields/rejection writes are local diagnostic work.
No latency optimization or measured gameplay improvement is claimed.

Remaining limitations: HTTP/UI transport unverified, provider reachability untested,
live semantics/timing/cost unmeasured, ATGB source re-attestation deferred. Those do
not weaken the verified one-process admission ceiling under the documented launch.
