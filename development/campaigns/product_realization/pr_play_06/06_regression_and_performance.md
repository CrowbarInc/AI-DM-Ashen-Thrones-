# 06 — Regression and Performance

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

| Bounded group | Passed | Failed | Pytest seconds |
|---|---:|---:|---:|
| focused | 58 | 0 | 8.712 |
| provider | 88 | 1 | 30.495 |
| structured | 60 | 1 | 2.525 |
| ordinary | 56 | 0 | 4.044 |
| opening | 23 | 3 | 7.255 |
| world | 123 | 0 | 2.949 |
| export | 11 | 0 | 1.774 |

Broader total: 361 passed / 5 failed. Focused 58 passed is separate;
the 57-pass non-HTTP subset is overlapping evidence, not added to totals. Every
driver group is bounded at 90 seconds. Commands, run records, XML and text logs
are retained. Full repository suite and live benchmark not run.

Five failures are preexisting, reproduced individually with the saved entry
game.gm source using tests.helpers.pr_play_06_entry_source: stale accounting source
attestation; raw-chat stew-price assertion; three rich opening emission preservation
assertions. Identical failing IDs match the broader runs. Earlier PR-PLAY-05
reports independently retain the same families. No unrelated repair or updated
attestation. New regressions: none observed in completed scope. Unresolved new
failures: none. Those preexisting player-facing limitations justify verdict B.

Sandbox attempts stalled at the placeholder HTTP check and raw-chat check; capped
at 90 seconds. Bounded outside-sandbox reruns complete, including all 58 focused
tests. No provider access permitted. A prior unbounded-shell focused invocation
was interrupted after stall; it is not counted as a completed test result.
No claim that a sandbox timeout is a product pass or a product failure.

Regression scope includes initialization, opening/structured parsing and final
response preservation, provider dispatch/accounting/retries, rollback, world/faction
progression, ordinary narration/conversation/authority and R2 interpretation/participant
grounding. This is a relevant slice, not all ATGB scenarios or statistical reliability.

Prompt size change: zero for both recorded fixtures. Local new contract parse and
setting selection: median 0.3809 ms, maximum
0.6409 ms over 200 iterations. This measures only the added
local selection work on a ~103k-character user payload, not network/UI latency.
No latency or monetary cost-neutral claim. Protected integrity: all 257 baseline
data/experiment files and file inventory match. Frozen ATGB content unchanged;
its source attestation remains stale and fail-closed.
