# 03 — Test-data isolation

`tests/helpers/storage_isolation.py` still redirects `ASHEN_DATA_DIR` before gameplay imports and rejects writes under repository `data/` and unrelated `artifacts/`.

The first HTTP harness imported `game` before `install()`, so `new_campaign` tried to write `data/session.json.tmp`. The audit hook raised `PermissionError` and the write did not land. The harness was reordered so isolation is installed first. The rerun wrote only under `artifacts/pr_play_79/http_data`.

Protected-file check against `artifacts/pr_play_78/protected_before.json`:

- Expected: 150
- Preserved: 150
- Mismatches: none
- Missing: none

Recorded in `artifacts/pr_play_79/protected_hashes.json`.
