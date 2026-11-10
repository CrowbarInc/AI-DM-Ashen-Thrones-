# PR-PLAY-72V — REGRESSION RESULTS

Raw results (do not merge combined and isolated):

```json
{
  "focused": {
    "passed": 1063,
    "failed": 22
  },
  "boundary": {
    "passed": 101,
    "failed": 6
  },
  "broader": {
    "passed": 0,
    "failed": 9
  },
  "lifecycle_isolated": {
    "passed": 38,
    "failed": 1
  }
}
```

Exact identity comparison with PR72 is in regression_comparison.json. The focused run is 1063/22; 20 failure identities overlap the prior run, one prior timing failure is absent, and two extra test-isolation failures were repaired and passed 2/2 in a clean process. The running focused process predates final auxiliary grammar changes; those gated changes have dedicated final safety/HTTP/browser coverage. The isolated lifecycle lane is 38/39: the no-injected-fault atomic test observed a second rename, after the correct bytes had already been verified. A fresh four-case rename-budget rerun passed 4/4 without changing storage. This is retained as a nonreproduced test failure, not called historical. See atomic_replace_observation.json. No full-suite or official benchmark claim. No new product regression is confirmed in these executed lanes.
