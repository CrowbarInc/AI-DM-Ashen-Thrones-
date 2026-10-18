# PR-DG Regression Results

No live provider calls. Unrelated failures were not repaired. Production save hashes were compared before and after the suite. None of the watched save files changed.

## Focused experiment tests

`tests/test_pr_dg_architecture_preflight.py`: 2 passed, 0 failed, 0 skipped.

## Relevant existing suites

| Suite | Passed | Failed | Skipped |
|---|---:|---:|---:|
| PR-CK resolver (`test_pr_ck_ordinary_resolver_selection.py`) | 30 | 0 | 0 |
| State authority (`test_state_authority.py`) | 26 | 0 | 0 |
| PR-CX authority (`test_pr_cx_authority_assurance.py`) | 9 | 0 | 0 |
| PR-CP finalization (`test_pr_cp_authorized_finalization.py`) | 9 | 0 | 0 |
| Combat (`test_combat_resolution.py`) | 8 | 0 | 0 |
| Improvisation (`test_bounded_improvisation_authority.py`) | 5 | 0 | 0 |
| PR-DE (`test_pr_de_exact_contract_deduplication.py`) | 6 | 0 | 0 |
| Noncombat (`test_noncombat_resolution.py`) | 11 | 0 | 0 |
| World state (`test_world_state.py`) | 11 | 0 | 0 |
| World clock (`test_world_progression_tick_integration.py`) | 6 | 0 | 0 |
| Shared turn pipeline (`test_turn_pipeline_shared.py`) | 41 | 24 | 0 |

Those existing files, excluding the shared pipeline, are 121 passed, 0 failed, 0 skipped.

## Inherited baseline

PR-DE recorded the required suite as 353 tests, 326 passed, 27 failed, 0 skipped. This cycle did not re-run that full list. The overlapping rows that PR-DE published match this run: PR-CK 30 passed, PR-CX 9 passed, PR-CP 9 passed, PR-DE focused 6 passed.

PR-DE shared-pipeline baseline: 41 passed, 24 failed, 0 skipped.

This run: 41 passed, 24 failed, 0 skipped.

The 24 names are the inherited dialogue-lock, retry, notice-board mixed-turn, and strict-social failures. They were not repaired.

## Command

Each file was run as `python -m pytest <file> -o addopts=--basetemp=development/tmp/pytest --tb=no -q` with `PYTHONPATH` set to the repo root and `ASHEN_DISABLE_LIVE_INTERPRETATION=1`. The repo `pytest.ini` already adds `-q`, so the override keeps a single quiet level and a visible summary line.
