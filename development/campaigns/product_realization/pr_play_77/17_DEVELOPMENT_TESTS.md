# Development Tests

File: `tests/test_pr_play_77_multistep.py`.

Re-run after the provider alias map and the admission error change:

`py -3 -m pytest tests/test_pr_play_77_multistep.py --tb=line -q --basetemp=development/tmp/pr77_multistep`

Result: 120 passed, exit code 0, elapsed about 3.5 seconds.

The matrix covers single-action preservation, two- and three-step decomposition, the more-than-three clarification, conditionals, shared targets, dependency kinds, partial success, blocked and skipped and unsupported steps, read-only compounds, H93 missing targets, save and resume without automatic continuation, provider accept and reject paths, and isolation. Deferred features were not marked passing. Climb stays unsupported in the tests that exercise it.
