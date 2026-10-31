# 07 — Deterministic Replay and Regression

PR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.

Original reproduction: replay.json executes the exact captured parsed response through the
production parser, semantic validation, acceptance and normal persistence with synthetic SDK
transport. No direct runtime-state injection. Only isolated authored scene fixture content is
prepared before the operation. Historical/replayed before overlays and after overlays compare
equal. Whole documents are not claimed byte-identical: fresh run IDs, clocks and diagnostic
timestamps differ. Instrumentation observes rather than replaces decisions. One SDK stub call.

Runtime HTTP reproduction: http_evidence/ preserves the full owned isolated FiveTurnGameplay
run. Opening integrity true, T1 executed, 4 turns attempted /
4 completed; stop=provider_budget_exhaustion, six synthetic dispatches, zero live.
T5 is safely skipped at the original request ceiling. This is progression beyond opening,
not proof of all five turns fitting six requests or of narrative quality. The first sandboxed
HTTP attempt was environment-blocked; localhost-enabled rerun traversed normal production HTTP.
The sandboxed broad run was interrupted while blocked; final lane records supersede it.

Final completed regression: 752 passed / 6 failures across selected lanes.
Counts are test executions, including intentional overlap, not a unique-test claim.

| Lane | Passed | Failed | Errors |
| --- | --- | --- | --- |
| conversation | 35 | 0 | 0 |
| diagnostics | 81 | 0 | 0 |
| export_atgb | 55 | 1 | 0 |
| gameplay | 33 | 0 | 0 |
| harness | 35 | 0 | 0 |
| hidden_faction | 78 | 0 | 0 |
| opening | 23 | 3 | 0 |
| overlay | 88 | 0 | 0 |
| provider | 88 | 1 | 0 |
| rules_persistence | 53 | 0 | 0 |
| structured | 60 | 1 | 0 |
| world | 123 | 0 | 0 |

Commands, time bounds and exits: regression_runs.json. JUnit and text output accompany every
lane. PR-PLAY-04/06/07 cover valid/invalid/nonresolution openings, retry eligibility, one-time
progression, repeat/concurrency, validation/budget/capture. Harness covers state classification,
stop behavior, accounting, continuation, scenarios and hashed evidence export. Overlay suites
cover gateway effects, save/load, hidden layering and runtime state. World/rules lanes cover
deterministic and faction progression. Frozen ATGB infrastructure is tested without running
a live benchmark or changing baseline attestations.

Known failures are compared by exact test ID against the preserved PR-PLAY-09 JUnit baseline
in failure_classification.json. No unrelated repairs. No full-suite, live quality, human review,
held-out generalization, rendered browser or ATGB score claim. Protected hashes cover ordinary
data, game/static and experiments: entry_to_exit_integrity.json.
