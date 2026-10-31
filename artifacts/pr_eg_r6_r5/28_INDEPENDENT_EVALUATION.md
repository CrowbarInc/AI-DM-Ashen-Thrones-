# 28 — Independent Evaluation

Ground truth was frozen before provider execution. Hash `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221`.

The scorer does not receive the engine operation, referent, selected source, or response class as the answer. It receives the delivered string and the frozen phrase lists.

Disagreements are preserved. A turn can be `authorized_direct` in the plan and still fail the rubric if the spoken line drops the allowed phrase or adds a forbidden one. A turn can be engine-unknown and still pass UNKNOWN. Those pairs stay in the jsonl.

No human adjudicated the packet. Where the phrase list is narrow, F18 (20 of 105 baseline failures) may be a rubric gap rather than a player-facing miss. The report does not convert F18 into a stage blame.

Holdout labels were not placed in provider prompts. Interventions did not run on holdout, so holdout success (21/55) is a second baseline measurement, not a tuned score.

The schema-rejected intervention file is excluded from every rate above.
