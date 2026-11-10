# Historical regression

Final source, lanes from `artifacts/pr_play_79df2/run_regression.py`, compared with PR-PLAY-78A:

| Lane | Passed | Failed | New identities |
| --- | ---: | ---: | --- |
| Focused | 1065 | 20 | none |
| Boundary | 101 | 6 | none |
| Broader | 0 | 9 | none |

The 20, 6, and 9 failures are the historical identities. They are not new. Cleared identities versus PR-PLAY-78A: none.

Failed revision, before the `campaign_run_id` rename: focused 1048/37, with 17 new identities, all quarantined investigation or readiness comparisons of `last_publication.campaign_id`. Boundary and broader had no new identities on that revision either. Those 17 are repaired and are not in the final result. The failed-revision list is `machine/regression_results_failed_revision.json`.
