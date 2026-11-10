# 15 — Publication HTTP 500

`tests/test_pr_play_66_publication.py::test_publication_http[rejected]` was run 8 times. Every attempt exited 0. No traceback and no HTTP 500 appeared in those logs. Rejected narration in the lifecycle tests still returned a player-safe body and kept the committed discovery text.

The historical intermittent 500 from PR-PLAY-70 was not reproduced. A passing repeat does not identify its cause and does not prove it cannot happen again. No unexpected HTTP 500 appeared in the 31 HTTP lifecycle requests or the 75 browser lifecycle responses.

The investigation stopped at that bounded budget. It was not expanded into older unrelated failures.
