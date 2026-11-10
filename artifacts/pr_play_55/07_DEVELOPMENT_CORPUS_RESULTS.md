# Development corpus results

Source: `tests/pr_play_55_development.py`. Rows: `evaluation.json` → `development_rows`.

This corpus was used while editing. It is not the holdout.

| Metric | Count |
| --- | --- |
| Total | 40 |
| Consequential fabrications | 21 |
| Fabrications decided FAIL | 21/21 |
| Fabrications decided REVIEW_REQUIRED | 0/21 |
| Fabrications decided PASS (critical false negatives) | 0/21 |
| Harmless narration | 15 |
| Harmless false FAIL | 0/15 |
| Harmless false REVIEW_REQUIRED | 0/15 |
| Authorized paraphrases | 3 |
| Paraphrases accepted | 3/3 |
| Ambiguous rows | 1 |
| Ambiguous rows decided REVIEW_REQUIRED | 1/1 |
| REVIEW_REQUIRED overall | 1/40 |
| VALIDATION_ERROR | 0/40 |
| Correct classification | 40/40 |
| Provider requests | 0 |

Single pass over the 40 lines: average 0.1976 ms, median 0.1711 ms, maximum 0.7443 ms.

Untraced repeat, 40 passes, 1600 validations: average 0.1662 ms, median 0.1636 ms, maximum 4.7721 ms, about 6007 validations per second. See `performance.json`.

## Previous scored corpus, same build

| Metric | Count |
| --- | --- |
| Total | 83 |
| Fabrications FAIL | 49/49 |
| Critical false negatives | 0 |
| Positive and paraphrase rows that were not PASS | 0 |
| Paraphrases accepted | 7/7 |
| REVIEW_REQUIRED | 2 (`R1`, `R2`) |

Single pass: average 0.1961 ms, median 0.1582 ms, maximum 0.6976 ms.

Untraced repeat, 40 passes, 3320 validations: average 0.1833 ms, median 0.1587 ms, maximum 2.5002 ms.

PR-PLAY-54's published average on its scored pass was about 0.169 ms. The untraced median here is in that neighborhood. The maximum moves when a single call pays an allocation spike. Correctness was not traded away to protect the 0.169 ms figure.

Confusion for the development set: `FAIL→FAIL` 21, `PASS→PASS` 18, `REVIEW_REQUIRED→REVIEW_REQUIRED` 1. There is no false-negative row and no false-positive row.
