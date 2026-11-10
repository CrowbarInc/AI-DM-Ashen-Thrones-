# Frozen holdout

Developer-authored. Not independent external validation.

Fixture: `tests/fixtures/pr_play_79df2_holdout.json`
SHA-256: `42887ffb1d8abf2044deddcdc8ef69a664209b9dd58b075e5cb8c5fe9bb75083`
Cases: 28 (H01–H28).
Result: 28/28. Individual rows: `machine/holdout_results.jsonl`.

The fixture was amended once before the final regression, and before this recorded run. H26 originally expected a field named `campaign_id`. That name broke paired historical comparisons. The expectation now uses `campaign_run_id` for the same campaign stamp. Visible text, validation, and provenance expectations were not retuned after a holdout failure.

A later attempt to write results into the review directory failed closed because the test audit blocks artifact writes outside the configured evidence directory. That run is not a behavioral failure. The recorded 28/28 run used the evidence directory and wrote the result rows.
