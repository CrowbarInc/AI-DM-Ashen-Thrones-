# 34 — Remaining Unknowns

- Human review is pending. F18 covers 20 of 105 baseline failures. Some of those may be rubric misses.
- c06t06 is PARTIAL with an empty eligible-source list. Gold cannot say the allowed name without inventing a source. The label and the harness disagree about what a partial answer may cite.
- Two validation turns never entered the planner. Their gold rows are copies. The live-interpretation path is outside this causal map.
- I6 cannot attach `proposed_coverage` to a compact payload. The measured I6 effect is the `coverage()` adapter only. Turns with no source proposition never call it.
- I9's gold referent delta is still rejected by bind. The experiment shows the gate is causal. It does not show which predicate in `bind()` is the smallest safe change.
- Holdout was baselined (21/55) and not used to choose repairs. A later patch can still fail holdout.
- Temperature 0 did not make the two c01 pilot phrasings identical to the full rerun. Provider nondeterminism remains.
- Public clue creation on a direct selection was observed and not fully inventoried beyond the log lines.
- Dollar cost is not computed. Token totals are in artifact 30.
- The full automated suite was not run. This cycle's offline test is `tests/test_pr_eg_r6_r5_diagnostic.py` (4 passed).
