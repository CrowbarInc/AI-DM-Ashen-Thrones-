# Test-Data Isolation

Protected repository data is `data/`. `tests/conftest.py` installs `tests/helpers/storage_isolation.py` before game imports. Campaign, session, save, provider-log, and pytest storage stay outside `data/`.

Protected hashes were recorded in `artifacts/pr_play_76/protected_before.json` before edits and checked again after the campaigns.

- Protected files: 150
- Matching after the cycle: 150
- Missing: 0
- Differing: 0

No protected file was restored silently because none changed. HTTP traces wrote under `artifacts/pr_play_76/http/` through the evidence-directory exception. The browser host used `artifacts/pr_play_76/browser_data`, created by the same isolation helper.
