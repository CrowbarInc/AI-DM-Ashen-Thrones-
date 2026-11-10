# Development tests

`tests/test_pr_play_79a_continuity.py`: 40 tests.
`tests/test_pr_play_79a_matrix.py`: 72 tests.
Total focused tests for this cycle: 112.

The last run of those files together with `tests/test_pr_play_78_integrated.py`, `tests/test_pr_play_79_agency.py`, and `tests/test_pr_play_78_holdout.py` passed.

The full PR-PLAY-79 regression lanes (focused 1065/20, boundary 101/6, broader 0/9) were not re-executed. Three existing directed-social chat tests still fail with `resolution.kind` None. They failed the same way before the observation and menu repairs. They are not claimed as new, and they are not claimed as fixed.

`game/authored_action_language.py`, `game/general_purpose_actions.py`, `game/integrated_play.py`, and `game/physical_adjudication.py` are untracked. Diff stats on tracked files mix this cycle with earlier uncommitted work.
