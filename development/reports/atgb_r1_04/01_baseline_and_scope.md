# 01 — Baseline and Scope

ATGB-R1-04, 2026-10-19. Structural-only validation recovery. Primary development
failure class: evaluation — an invalid execution environment defeated the control.
HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; extensive dirty/untracked state
predates this pass. repository_status_before.txt records it. No commit or push.

Read the Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
product realization validation, review standard, R1-01 causal report and R1-02/03
eight-report packages. support/docs/NEXT_SESSION.md does not exist in the checkout;
it is a review-bundle spelling, as R1-03 also documented. Canonical docs was used.
Current R1-02 orchestration remains present and matches the R1-03 entry digest;
baseline_comparison.json finds zero predecessor discrepancies. Final integrity.json
verifies all 3,996 entry files, including production, player data, frozen ATGB and
experiments. No material baseline discrepancy beyond the recorded dirty worktree.

R1-03: L1 connection error, L2 server error, L3 inadequate paraphrase, L4 invalid
disabled-interpretation fallback with isolated mutation. These outcomes remain
historical; no transcript or assessment is rewritten.

Authored implementation: tools/atgb/readiness.py and
tests/test_atgb_r1_04_readiness.py only. Supporting changes: eight reports/index,
campaign evidence/export script, review configuration, docs/NEXT_SESSION.md and
generated handoff. No production or experimental implementation edits. The old
execute_trial.py remains preserved evidence; its replacement gate/control is the
supported foundation for a separately reviewed future runner. Do not rerun it.
No semantic repair, prompts, models, binding, or world-authority change.
