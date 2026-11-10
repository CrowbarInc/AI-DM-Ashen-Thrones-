# Test-data isolation

- Campaign, session, save, and provider logs for the live run are under `artifacts/pr_play_79c/live_data`.
- The browser host used a copy of the initialized seed at `artifacts/pr_play_79c/browser_data`.
- The seed hash is `92415f74c31800dcfe8b36fa3ac7b35aa237df5c59a265ac9aacb9c348b4033f`.
- Provenance: one fresh opening, then a restored initialized campaign for the browser. The browser did not generate a second opening.
- Protected `data/` files compared with `artifacts/pr_play_79b/protected_before.json`: **150 preserved, 0 mismatches, 0 missing**.
- Import-time isolation remains `tests/conftest.py` plus `tests/helpers/storage_isolation.py`. Pytest still disables live expression unless a test patches it.
