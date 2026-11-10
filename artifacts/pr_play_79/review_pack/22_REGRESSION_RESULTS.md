# 22 — Regression results

Comparison target: PR-PLAY-78A identities. Focused 1,065 passed / 20 failed. Boundary 101 / 6. Broader 0 / 9.

First attempt was invalid. Pytest `--basetemp` pointed at a directory that did not exist, so the failures were `FileNotFoundError`, not product failures. Those counts are discarded. The runner now creates the directory.

The valid comparison, including the greeting repair:

- Focused: 1,065 passed / 20 failed / new identities 0 / cleared 0
- Boundary: 101 passed / 6 failed / new identities 0 / cleared 0
- Broader: 0 passed / 9 failed / new identities 0 / cleared 0

The failed names match the PR-PLAY-78A lists. None were reclassified as new. Record: `artifacts/pr_play_79/regression_results.json`.
