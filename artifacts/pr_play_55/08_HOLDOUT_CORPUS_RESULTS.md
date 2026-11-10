# Holdout corpus results

File: `tests/pr_play_55_holdout.json`.

Manifest: `tests/pr_play_55_holdout_manifest.json`.

SHA-256: `24ff35e8f4096e865dcf3ffd6f98a92d18a208e1329c445c33525e5e5fed1495`

Bytes: 14876. The hash was checked again after the run and still matches. The file was not edited after the hash was recorded, and it was not edited after the classification.

The official classification is the single pass stored in `evaluation.json`. The validator was not changed afterward.

| Metric | Count |
| --- | --- |
| Total | 70 |
| Fabrications | 30 |
| Fabrications decided FAIL | 30/30 |
| Fabrications decided REVIEW_REQUIRED | 0/30 |
| Fabrications decided PASS (critical false negatives) | 0/30 |
| Harmless narration | 20 |
| Harmless false FAIL | 0/20 |
| Harmless false REVIEW_REQUIRED | 0/20 |
| Authorized paraphrases | 10 |
| Paraphrases accepted | 10/10 |
| Ambiguous rows | 10 |
| Ambiguous rows decided REVIEW_REQUIRED | 10/10 |
| REVIEW_REQUIRED overall | 10/70 |
| VALIDATION_ERROR | 0/70 |
| Correct classification | 70/70 |
| Provider requests | 0 |

One-shot latency: average 0.2129 ms, median 0.1103 ms, maximum 6.8801 ms. The maximum is the first call in that process (`F01`). Later calls in the same pass sit near the median.

Confusion: `FAIL→FAIL` 30, `PASS→PASS` 30, `REVIEW_REQUIRED→REVIEW_REQUIRED` 10.

False-negative examples: none.

False-positive examples: none.

The 30 passing rows are the 20 harmless lines plus the 10 paraphrases.

## What the holdout is, and what it is not

The sentences use a customs shed, a hawser, a bone whistle, a tariff slip, a night barge, and an oilskin pouch. They are not rewordings of the silver-key and salt-fortress rows.

Labels were written from the decision rules in the mission, then hashed, then the validator was edited. Individual holdout outcomes were not used to change the code. The run matched every label.

The same session wrote the rules, the labels, and the code. The repository does not have a second author or a sealed review environment. The hash shows the file was stable. It does not make the corpus externally blind. That limit is stated again in `13_LIMITATIONS_AND_OPEN_RISKS.md`.
