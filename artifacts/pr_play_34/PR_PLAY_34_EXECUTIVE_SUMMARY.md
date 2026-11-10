# PR-PLAY-34 — Offline harness readiness

**Verdict: A — PASS.** The harness is ready for a separately authorized live experiment. PR-PLAY-35 was not started.

PR-PLAY-33 repaired Windows launcher indirection and reached HTTP 200, then stopped. Two diagnostic assertions remained unresolved: an unlabeled `AssertionError` inside the readiness wrapper, and an outer requirement that `session.json` be absent.

This task inspected that run without changing the process-launch repair. The unlabeled failure is the wrapper's zero-child assert. Re-measurement shows the worker's only child is `conhost.exe`. Controller pid, Popen pid, and worker-reported pid agree, and the worker image is the base interpreter. The session-file assert was an incorrect expectation: `GET /api/state` creates a bootstrap session with `campaign_started` false and `turn_counter` 0.

The diagnostic now records each condition separately, writes that record before cleanup, and accepts a bootstrap session while still failing a started campaign, a nonzero turn, gameplay activity, or a provider dispatch. Controls A through G passed on isolated stores. Provider requests and gameplay turns are 0. No gameplay or provider implementation file changed.
