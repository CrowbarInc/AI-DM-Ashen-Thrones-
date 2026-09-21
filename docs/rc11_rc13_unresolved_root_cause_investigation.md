# RC-11 & RC-13 Unresolved Root-Cause Investigation

## Decision Summary

Both investigated failures are `STALE_EXPECTATION` with `HIGH` confidence. Neither demonstrates a product regression. No repair, threshold change, fixture change, evaluator change, replay change, or test expectation change was made.

## Baseline and Reproduction

The pre-investigation suite collected 6,448 tests: 6,342 passed, seven failed, and 99 skipped. Six failures are the established baseline; the additional governance-document assertion is unrelated to RC-11/RC-13 and reflects pre-existing worktree state.

RC-11 and RC-13 each failed identically in 10 of 10 isolated runs. Bounded checks also remained local:

| Check | Tests | Failures | Result |
|---|---:|---:|---|
| RC-11 module | 6 | 1 | RC-11 only |
| RC-11 plus opening-fallback family | 72 | 1 | RC-11 only |
| Long-session replay module | 3 | 1 | RC-13 only |
| Long-session plus projection engine | 7 | 1 | RC-13 only |

## RC-11

The current helper and preserved inline comparator select and emit the same accepted scene-opening candidate. Their candidate preview and emitted preview also match. The sole difference is that the current helper records a governed `diagnostic_only` semantic-mutation write-site row after restoring the accepted text. The historical whole-dictionary equality predates that attribution contract.

Classification: `STALE_EXPECTATION`, `HIGH`. Recommended future action: compare protected behavior fields and assert the attribution row independently.

## RC-13

The supporting direct-intrusion diagnostic profile caps mutation events at 14, exactly the sum of its four modeled subtype maxima. Current runtime lineage reports those 14 events plus four sealed-replacement events and one referential-clarity replacement event. The first unprofiled category appears at `act_02`; the cumulative cap is first exceeded at `act_19`.

The replay itself remains healthy: 25 turns, expected fallback behavior, stable ownership, session score 100, clean classification, overall pass, and no degradation. The cap is a historical snapshot that predates the expanded mutation attribution vocabulary.

Classification: `STALE_EXPECTATION`, `HIGH`. Recommended future action: recalibrate the supporting diagnostic profile from governed subtype categories and reconcile its aggregate cap.

## Scope Boundary

RC-10 and RC-21 remain undecided. This campaign ends with investigation evidence and recommendations only.

## Evidence

- `artifacts/unresolved_root_cause_investigation/investigation_registry.json`
- `artifacts/unresolved_root_cause_investigation/rc11_trace.json`
- `artifacts/unresolved_root_cause_investigation/rc11_trace.md`
- `artifacts/unresolved_root_cause_investigation/rc13_root_cause.md`
- `artifacts/unresolved_root_cause_investigation/rc13_turn_trace.json`
- `artifacts/unresolved_root_cause_investigation/rc13_turn_trace.md`
- `artifacts/unresolved_root_cause_investigation/recommended_actions.json`
- `artifacts/unresolved_root_cause_investigation/recommended_actions.md`
