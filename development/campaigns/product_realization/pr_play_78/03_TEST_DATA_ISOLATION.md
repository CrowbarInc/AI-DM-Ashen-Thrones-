# Test-data isolation

`game.storage.DATA_DIR` is bound at import. Tests set `ASHEN_DATA_DIR` before import. `tests/helpers/storage_isolation.py` refuses writes under `data/` and under `artifacts/` unless `ASHEN_TEST_EVIDENCE_DIR` is a specific run directory. Pytest therefore does not write campaign traces into `artifacts/pr_play_78/`.

Play scripts used their own directories:

- `artifacts/pr_play_78/extended_data/`
- `artifacts/pr_play_78/live_data/`
- `artifacts/pr_play_78/browser_data/`

Canonical scene files were copied into those directories after storage import. The repository `data/` tree was not the runtime store.

Protected hashes were recorded in `artifacts/pr_play_78/protected_before.json` before product edits (150 files, 0 missing). The closure recount compared those hashes to the current files.

Result: **150/150 unchanged. 0 missing. 0 changed.**

No protected file was restored, because none changed.
