# PR-PLAY-33 — Harness process ownership investigation and repair

**Verdict: B — PARTIAL. Root cause classification: A — Windows virtual-environment process indirection.**

Toolhelp32 process snapshots establish that the same .venv Python used by PR-PLAY-32 spawns an interpreter child. Popen owns the redirector, while os.getpid() reports the child. The direct base interpreter has no intermediate worker process. The controller and worker PID APIs were correct; the strict guard correctly refused the launch topology.

Repair: extract the existing shared controller's base-interpreter launch policy into runner.start_worker; route both the shared runner and PR-PLAY-32 observer controller through it. Preserve package visibility, environment safety settings, strict PID/path/isolation attestation, deadlines and existing handle-based cleanup. Fail before spawning when the expected interpreter is unavailable. No gameplay, campaign initialization or provider routing code changed.

24 focused offline tests passed, no failures, errors, skips or retries. Four stdlib-only process reproductions passed. The first actual harness readiness attempt reached HTTP 200 with matching PID and isolation, then the controller caught an AssertionError in the diagnostic wait wrapper and cleaned up with zero provider usage. The wrapper did not persist its native snapshot, so its exact failed assertion is unresolved. The outer diagnostic then failed because it incorrectly required session.json to be absent; GET /api/state leaves a bootstrap session at turn zero with campaign_started false. Per mission instructions the harness was stopped without a readiness retry. Observer-worker readiness and occupied-port cleanup controls were not executed. Full readiness is therefore NOT certified.

Provider requests: 0. Input/output/total provider tokens: 0/0/0. Live gameplay turns: 0. Campaign initialization/start/chat POSTs: 0. Bootstrap state loading did occur in the isolated readiness store. No live experiment, credentials-required launch or next PR initiated. Await review.
