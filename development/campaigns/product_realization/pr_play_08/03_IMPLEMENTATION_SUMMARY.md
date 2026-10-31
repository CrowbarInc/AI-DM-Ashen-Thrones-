# Implementation Summary

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

New source: `tools/playtest/{runner,worker,analysis,browser,__init__}.py`, two scenario
JSON definitions, `scripts/run_live_playtest.ps1`, `tools/validate_pr_play_08.py`,
`tools/report_pr_play_08.py`, and `tests/test_automated_playtest.py`. Updated only
the coverage registry and canonical NEXT_SESSION; added the guide. Production
`game/`, `static/`, ordinary `data/`, and `experiments/` were not edited.

The transaction is New Campaign → capture baseline → Start once → capture after.
HTTP statuses/bodies, narration presence, API-visible state, session metadata,
turn/scene/log, complete selected persistent files, native provider journal,
budget snapshot, structural/semantic/outcome stages and correlations are retained.
The report checks acceptance, one diagnostic commit, turn delta one, log delta
one and state-integrity constraints; HTTP 200 is insufficient.

Failure/interruption closes only the owned worker. After an interruption, persistent
after-state is copied after shutdown when the final API projection cannot be read.
Port collisions block without attaching to or terminating other processes.
No task implementation changes were made in response to production failures.

Evidence: `artifacts/pr_play_08/source_diff.patch`, source snapshots, matrix_runs.json,
JUnit XML/logs, protected integrity, and the complete example run at
`artifacts/atgb/automated_playtests/20261030T011639Z-812744c9c860`. The initial development failures identified
PID redirection, request-bookkeeping comparison, missing-diagnostic verdict and
fixture-expectation mistakes in the harness; final checks cover their corrections.
