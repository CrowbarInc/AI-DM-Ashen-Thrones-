# Test-data isolation

- Pytest uses `tests/helpers/storage_isolation.py`, which sets `ASHEN_DATA_DIR` before game import and refuses writes under repository `data/` and unrelated `artifacts/` trees.
- This cycle's runners called the same installer with directories under `artifacts/pr_play_78a/` (`holdout_data`, `http_data`, `adaptive_data`, `provider_data`, `browser_data`).
- Provider usage for those runs went to the isolated directory's `provider_usage.jsonl`.
- Protected hash check against `artifacts/pr_play_78/protected_before.json`: preserved 150 of 150. Mismatches: []. Missing: [].
- No protected file was restored or rewritten.
