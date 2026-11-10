# Final historical regression

Final source and final assertion set: machine/final_audit. Same suites as the 79C regression runner, compared against archived PR78A exact failure identities.

```json
{
  "focused": {
    "passed": 1065,
    "failed_count": 20,
    "skipped": 0,
    "new_vs_pr_play_78a": [],
    "cleared_vs_pr_play_78a": []
  },
  "boundary": {
    "passed": 101,
    "failed_count": 6,
    "skipped": 0,
    "new_vs_pr_play_78a": [],
    "cleared_vs_pr_play_78a": []
  },
  "broader": {
    "passed": 0,
    "failed_count": 9,
    "skipped": 0,
    "new_vs_pr_play_78a": [],
    "cleared_vs_pr_play_78a": []
  }
}
```

All historical failure identities remain listed in regression_results.json and individual XML. New identities: []. Earlier intermediate full runs showed the two obsolete PR69 no-recall expectations; their literal assertions were replaced by stricter source-recall assertions and both were rerun before the final complete lane. Repeated runs occurred only after new source or assertion changes; they are retained as intermediate evidence, not substituted for the final lane.
