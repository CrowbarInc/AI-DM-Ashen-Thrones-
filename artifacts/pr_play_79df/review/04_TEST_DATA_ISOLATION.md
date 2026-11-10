# Test-data isolation

Pytest loads `tests/helpers/storage_isolation.py` before game imports. `ASHEN_DATA_DIR` points outside `data/`. An audit hook blocks writes to `data/` and `artifacts/` except the junit evidence root. Development runs also set `ASHEN_DISABLE_LIVE_INTERPRETATION=1` and `ASHEN_DISABLE_EXPRESSION_GENERATION=1`. `tests/helpers/live_model_guard.py` replaces live expression with `LiveModelCallForbidden` unless a test installs its own transport.

The first verification run failed in the harness: the live-model guard intercepted the controlled transport, a fresh dialogue session had no interlocutor, and provider admission tried to exclusive-create an existing ledger. Those failures were corrected in the test harness. Application source was not edited. The frozen holdout expectations were not edited. The second run is the reported development result: 187 passed.

Browser storage is a copy at `artifacts/pr_play_79df/browser_data`, taken from the initialized PR-PLAY-79D browser campaign. Provider rows for this cycle are in `artifacts/pr_play_79df/browser_provider_usage.jsonl`. Publication rows are in `artifacts/pr_play_79df/browser_publication.jsonl`. The copy skipped the prior provider and publication logs. No new campaign opening was generated.

Protected-file hashes were recorded at entry against the PR-PLAY-79D close inventory: 150/150 unchanged. The exit comparison is in `19_AUTHORITY_AND_ISOLATION.md`.
