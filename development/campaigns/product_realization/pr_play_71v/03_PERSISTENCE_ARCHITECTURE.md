# 03 — Persistence architecture

Persistence remains the existing file store in `game/storage.py`. This cycle did not add a database, replace the store, or redesign Save Slots.

`_atomic_write_bytes` writes a same-directory temporary file, fsyncs it, and replaces the target. On Windows `PermissionError` with `winerror == 5`, it retries only that replace. The delay schedule is 0.01, 0.03, and 0.09 seconds, then one final attempt with no further sleep. Any other `PermissionError` or `OSError` is raised immediately. The temporary file is removed if the replace does not complete. The previous target bytes stay in place when every attempt fails.

`runtime_commit_scope` records the pre-turn bytes of the session, world, combat, character, and session log. `api_action`, `start_campaign`, and `api_chat` use that scope. If the turn raises, the scope writes those prior bytes back. A failed restore falls back to a direct write. An error inside the restore is swallowed so the original exception still propagates. The scope does not call the provider or the resolver again.

Save Slots remain labelled snapshots. Loading one replaces the live runtime. An unsaved continuation exists only in the live session until a new snapshot is created.
