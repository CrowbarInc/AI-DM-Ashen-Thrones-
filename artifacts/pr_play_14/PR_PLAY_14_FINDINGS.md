# PR-PLAY-14 Findings

## Confirmed observations / harness blocker

**F1 — Application readiness timeout (high confidence; single execution).**

Observed: owned worker wrote ready.json with isolation and renderer attestation, but controller failed to obtain HTTP 200 from /api/state within the existing 30-second startup window. Result has failure.type=TimeoutError, stage=application_startup_failure; steps=[], elapsed_seconds=31.312. Journal contains initialized only. No application log output or budget snapshot exists. Worker terminated by existing cleanup.

Expected: server should serve a successful readiness response within the configured deadline, then initialize campaign and submit opening. Category: harness execution / application startup; no confirmed gameplay or provider defect. Evidence: harness/.../reports/result.json, diagnostics/{ready,execution_log}.json, provider_usage.jsonl, application.log; source_snapshots/tools/playtest/{runner,worker}.py. Root cause: **not established**. Scope: one observed controlled invocation; reproducibility not claimed. Consequence: no live gameplay evidence. No repair attempted.

## Suspected defects / hypotheses

No specific code defect confirmed. Worker reaches ready-file write before importing uvicorn and starting its server. A stall in the remaining bootstrap, server startup, lifespan or local HTTP readiness is possible (low confidence). Empty logs do not identify the responsible stage, and individual readiness errors were discarded by the polling loop. Do not infer provider outage, credential failure, semantic rejection or renderer defect.

## Non-defect limitations

- Credentials were present, not validated against provider because no request was dispatched.
- Worker flag activation verified; campaign renderer behavior never exercised.
- Raw native usage/live-call fields are absent/null; durable dispatch journal supports zero calls. Derived counters are separately labeled.
- Bootstrap files preserved and compared, but initial/final runtime snapshots and ordinary-turn raw responses do not exist.
- No UI, NPC dialogue, continuity, agency, meaningful progression or interactive provider performance evidence.
- Six-request ceiling might constrain a future scenario but did not cause this stop.
- Dirty pre-existing implementation is part of the tested context, recorded with source snapshots; no commits/pushes or changes to implementation/configuration.

## Single recommended next targeted investigation

Investigate the owned worker startup path between ready.json publication and the first successful /api/state response in a separate, offline-only pass. Determine whether the stall occurs during uvicorn import/startup, lifespan or readiness handling before requesting another live authorization. Preserve the existing budget/model/prompt/validator settings. PR-PLAY-15 was not started here.
