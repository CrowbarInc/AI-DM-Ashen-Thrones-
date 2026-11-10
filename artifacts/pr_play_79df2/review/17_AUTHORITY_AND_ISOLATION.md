# Authority and isolation

Protected files versus the PR-PLAY-79D baseline: 150/150 unchanged. Changed: none. Missing: none.

Browser storage is the copy under `artifacts/pr_play_79df2/browser_data`. Tests use `tests/helpers/storage_isolation.py`, which refuses writes to repository `data/` and to artifact paths outside the configured evidence directory.

Cross-session test: noting a publication on campaign alpha does not change campaign beta's pointer. Cross-campaign physical plan test does not mutate the other session.

No hidden-information exposure was observed. Player projection tests require an empty resolution object and no `hidden_facts` string in the projected body. The rejected northwest-track candidate was not published.

The notice-board lead remains the pre-existing scene-anchored redirect. No new authoritative fact was created from the accepted greeting or from the rejected patrol question.
