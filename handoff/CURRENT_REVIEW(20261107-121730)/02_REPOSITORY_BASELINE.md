# Repository Baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD message: fix: restore clarification recency and resolve planner audit false positive
- No commit and no push were made.

The working tree already contained unrelated uncommitted files before this cycle. Those files were left in place. This cycle owns:

- `game/physical_adjudication.py` (new)
- physical planning and commit hooks in `game/bounded_improvisation.py`
- the routine-turn extension in `game/api.py` so physical routines do not advance the world clock
- `tests/test_pr_play_76_physical.py`
- `tests/test_pr_play_76_matrix.py`
- `tests/test_pr_play_76_holdout.py`
- `tests/test_pr_play_76_http_trace.py`
- evidence under `artifacts/pr_play_76/`

The pathway is the existing one: player initiative calls `controlled_request`, which calls `plan_physical` when `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION=1` and the controlled-improvisation gates are on. `resolve_controlled_fact` calls `commit_physical` only for an interact plan. Flag off leaves the previous seat path and general-purpose actions unchanged.
