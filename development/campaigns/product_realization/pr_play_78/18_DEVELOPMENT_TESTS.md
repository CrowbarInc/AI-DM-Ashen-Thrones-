# Development tests

Closure command:

```
python -m pytest tests/test_pr_play_78_integrated.py tests/test_pr_play_78_holdout.py tests/test_pr_play_78_http.py tests/test_pr_play_77_multistep.py -q --tb=line -p no:cacheprovider --basetemp development/tmp/pr78_dev
```

Result: 259 passed, exit 0, about 13.4 seconds.

`tests/test_pr_play_78_integrated.py` collects 136 tests. That file is the focused matrix: parametrized mixed intents plus read-only stone checks, stone persistence, conversation memory, accepted and rejected speech, narration accept/reject, hidden-phrase exclusion, ordering, duplicates, lane release, independent campaigns, scene-scoped NPCs, cross-campaign facts, and provider accounting. Deferred behavior is not marked passing. Climbing and carrying remain refusals.

`tests/test_pr_play_77_multistep.py` passed in the same run. Pure physical sequences still belong to PR-PLAY-77.

The matrix items that are policy checks rather than new product behavior (no invented DC, no invented roll, no invented treasure) are asserted by the refusal text and the absent-fragment cases, not by a claim that those actions now succeed.
