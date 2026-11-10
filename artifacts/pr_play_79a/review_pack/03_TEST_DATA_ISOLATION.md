# Test-data isolation

`tests/conftest.py` installs `tests/helpers/storage_isolation.py` before game imports during pytest. That sets `ASHEN_DATA_DIR` outside `data/` and audits writes to repository `data/` and unrelated `artifacts/`.

The live HTTP script called `install(artifacts/pr_play_79a/live_data)` before importing the game. Campaign, session, save, and provider-log writes for that run stayed under that directory.

Protected-file comparison against `artifacts/pr_play_78/protected_before.json`: **150/150** preserved, 0 mismatches, 0 missing. Recorded in `artifacts/pr_play_79a/protected_hashes.json`.
