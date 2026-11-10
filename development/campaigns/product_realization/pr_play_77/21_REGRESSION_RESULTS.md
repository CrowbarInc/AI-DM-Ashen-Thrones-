# Regression Results

Runner: `artifacts/pr_play_77/run_regression.py`.

Baselines: `development/tmp/pr77_regression`. Provider calls disabled. Evidence-dir variable cleared.

| Lane | Passed | Failed | Identity delta vs PR-PLAY-75 |
| --- | --- | --- | --- |
| Focused | 1065 | 20 | none |
| Boundary | 101 | 6 | none |
| Broader | 0 | 9 | none |
| Isolated lifecycle | 39 | 0 | none |

The 20 focused, 6 boundary, and 9 broader failures are the same identities as PR-PLAY-75 and PR-PLAY-76. They are historical. New regression count: 0.

Isolated lifecycle remains 39/39, including persistence recovery and the PR-PLAY-71V verification file.
