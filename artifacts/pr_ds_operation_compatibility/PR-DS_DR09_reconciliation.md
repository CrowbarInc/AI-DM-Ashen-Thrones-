# PR-DS DR09 Reconciliation

DR09 was sent to the provider. The sentence in the PR-DR experiment report that says it was not sent is stale.

## Stored request

`artifacts/pr_dr_live_vertical_slice/raw_results.json` contains a completed DR09 call:

- request id `resp_088bea2734f3a049006acadaf47b5c87d28e307705ad4b2fb4`
- model `gpt-4.1-mini-2025-04-14`
- status `completed`
- input tokens 667
- output tokens 205
- total tokens 872
- latency 2489.364 ms

The stored prompt's visible scene is Waystation street, and the permitted entity is `notice_board`. That is the scene after DR08. The provider text parses to the stored `parsed` object: communication mode `IN_WORLD_ACTION`, one MOVE component, and no target id.

`PR-DR_provider_usage.csv` has the same DR09 token row. The budget object records 10 requests and 6,835 / 1,934 / 8,769 tokens. Those totals equal the sum of the ten usage rows, including DR09. Omitting DR09 would leave 6,168 input tokens, 1,729 output tokens, and 7,897 total tokens.

## Stale statement

`state.json`, `raw_results.json`, and `PR-DR_experiment_report.md` contain this harness note:

> DR09 was not sent. A visibility guard treated the notice board as illegal after the gate had already moved the disposable scene to the street. The guard now applies only while the courtyard is active. No provider request was retried.

`experiments/pr_dr/reports.py` prints `harness_note` when the field is present. The current `experiments/pr_dr/runner.py` does not assign that field. Its visibility check refuses `notice_board` only when the active scene is not the street. The stored DR09 prompt is the street prompt, so that check would allow the request that was actually stored.

The note contradicts the call record, the usage CSV, and the token sum. It was left unchanged. PR-DS does not rewrite PR-DR artifacts.

## Replay use of the same output

The replay sent no new request. It applied the stored DR09 object with the original OOC override. The envelope mode was OOC via `USER_OVERRIDE`. The row did not call a resolver, did not execute, and left the street scene and `time_pressure` 1 in place.
