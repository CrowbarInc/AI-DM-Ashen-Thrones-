# 14 — Corpus Evaluation

R2A corpus.json is copied byte-for-byte; freeze.json verifies SHA256 and preserves the original 72 development / 30 holdout split. Labels are investigator-authored and previously exposed during R2A. No relabeling, strategy selection on holdout, or tuning occurred here. This is historical split reuse, not independent blind qualification. Supplemental ten cases have separate freeze, labels and denominators. Generation reviews are a third, post-output dataset and never merged into corpus rates.

Development:

| Strategy | n | Safe accepted / safe | Unsafe accepted / unsafe | High-risk unsafe | False rejection | Safe abstention | All abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 72 | 15/30 | 28/39 | 27 | 15 | 0 | 0 |
| B | 72 | 15/30 | 28/39 | 27 | 15 | 0 | 0 |
| C | 72 | 4/30 | 0/39 | 0 | 0 | 26 | 68 |
| D | 72 | 24/30 | 2/39 | 1 | 6 | 0 | 0 |
| E | 72 | 24/30 | 2/39 | 1 | 6 | 0 | 0 |

Historical holdout:

| Strategy | n | Safe accepted / safe | Unsafe accepted / unsafe | High-risk unsafe | False rejection | Safe abstention | All abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 30 | 7/12 | 10/16 | 10 | 5 | 0 | 0 |
| B | 30 | 7/12 | 10/16 | 10 | 5 | 0 | 0 |
| C | 30 | 0/12 | 0/16 | 0 | 0 | 12 | 30 |
| D | 30 | 11/12 | 0/16 | 0 | 1 | 0 | 0 |
| E | 30 | 11/12 | 0/16 | 0 | 1 | 0 | 0 |

Supplement:

| Strategy | n | Safe accepted / safe | Unsafe accepted / unsafe | High-risk unsafe | False rejection | Safe abstention | All abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 10 | 3/6 | 2/4 | 2 | 3 | 0 | 0 |
| B | 10 | 3/6 | 2/4 | 2 | 3 | 0 | 0 |
| C | 10 | 2/6 | 0/4 | 0 | 0 | 4 | 8 |
| D | 10 | 6/6 | 0/4 | 0 | 0 | 0 | 0 |
| E | 10 | 6/6 | 0/4 | 0 | 0 | 0 | 0 |

A/B ACCEPT denotes hard-valid only; C ABSTAIN prohibits delivery. E is policy replay. Full confusion matrices include expected ABSTAIN, unresolved acceptance, safe abstention, false rejection and mixed failure ids. Per-category tables are retained in category_metrics.json, including low-count historical source categories. There are no missing provider cases imputed as successes. Two diagnostic repeats and the interactive pair are excluded from these frozen-case denominators.

Evidence classes: STATIC = current source inspection; LOCAL = executed current production functions with disposable fixtures and external wire doubles; FRESH = new provider request; HISTORICAL = retained predecessor evidence; REPLAY = recombination of measured results; INFERENCE = proposed design; UNVERIFIED = not exercised. No fresh full-production API test was performed.
