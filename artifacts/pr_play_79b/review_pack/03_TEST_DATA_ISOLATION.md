# Test-data isolation

Pytest uses tests/helpers/storage_isolation.py before game imports. The live HTTP run used artifacts/pr_play_79b/live_data. Provider usage for that run is in that directory. Protected repository data was not written. 150/150 hashes still match artifacts/pr_play_78/protected_before.json. Entry hashes are in artifacts/pr_play_79b/protected_before.json.
