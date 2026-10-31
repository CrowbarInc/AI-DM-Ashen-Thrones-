# 10 — Frozen Partitions

Hash `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221` was written to `artifacts/pr_eg_r6_r5/freeze.json` before intervention tuning. The runner exits if `corpus_hash()` differs.

Whole families stay in one partition so a conversation is not split across development, validation, and holdout.

| Partition | Families | Turns | Role |
|---|---|---:|---|
| Development | c01–c04 | 55 | Baseline measurement. Not used to choose a repair after seeing interventions. |
| Validation | c05–c08 | 54 | Baseline plus every gold arm and the expression control. Repair ranking uses this paired set. |
| Holdout | c09–c12 | 55 | Baseline only. Labels are not sent to the provider. No arm is tuned on these turns. |

Interventions replay the cached baseline proposal for the same validation turn and restore that turn's pre-turn snapshot. Holdout proposals are not patched.

No threshold, prompt, or label was edited after the freeze. The corpus file must not be edited for the rest of this cycle.
