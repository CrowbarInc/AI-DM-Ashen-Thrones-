# Change manifest

Existing files modified:

- tools/playtest/runner.py: extract existing direct-base-interpreter Popen construction into start_worker with optional observer script, preserve child environment without mutating caller settings, add fail-closed interpreter availability check, use the helper in the ordinary runner.
- artifacts/pr_play_32/execute.py: replace its single direct sys.executable Popen call with runner.start_worker using the same worker_capture.py target. This controller was NOT executed. Its original bytes are preserved under evidence_before/execute_pr_play_32.py; the original PR-PLAY-32 archive is retained.

New regression file: tests/test_pr_play_33_process_ownership.py (14 tests). Covers both module/script launch configuration, retained package and provider restrictions, missing base interpreter, controller adoption without importing live code, real direct-worker parent/PID ownership, cooperative normal exit, nonzero startup failure, timeout, termination/reaping, PID/path/isolation rejection before HTTP, and terminate-to-kill fallback through the owned handle. Existing test_playtest_startup_readiness.py contributes ten tests including stale attestation, deadline, startup exit and HTTP readiness behavior.

New artifacts/pr_play_33/: stdlib reproduction, readiness diagnostic, package builder, unchanged pre-repair source copies, hash baseline, raw process/pytest/readiness evidence, review reports, source snapshots, patches, manifests and archive verification. The readiness diagnostic is preserved exactly as executed, including its unpersisted post-readiness snapshot and failed session-absence assertion; it has not been silently corrected or retried.

New artifacts/atgb/pr_play_33/readiness/: exactly one isolated startup attempt and its normal controller evidence. No unrelated existing files changed, as checked against baseline_hashes.json across game/tools/tests and prior PR-PLAY-29/31/32 evidence. Temporary pytest files under development/tmp/pr_play_33_process are disposable test outputs and excluded from the review archive. Existing dirty worktree changes predated this task and were left intact.
