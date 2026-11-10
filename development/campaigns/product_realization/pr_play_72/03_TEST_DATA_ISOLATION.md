# PR-PLAY-72 — 03 TEST DATA ISOLATION

```json
{
  "storage_root": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_72\\isolation_probe_final",
  "session_log": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_72\\isolation_probe_final\\session_log.jsonl",
  "write_present": true,
  "protected_write_blocked": true,
  "blocked_paths": [
    "data\\session_log.jsonl",
    "artifacts\\pr_play_49\\evidence_pr72_forbidden.json"
  ],
  "protected_changed": [],
  "historical_report_output_policy": "Collected test module OUT paths are redirected to disposable test_artifacts directories; historical artifact writes are rejected except an explicit run evidence subtree selected by ASHEN_TEST_EVIDENCE_DIR, an explicit storage root, or --junitxml.",
  "early_run_limitation": "Initial combined regression regenerated legacy analysis outputs at module OUT paths. Entry hashes for those reports were not recorded, so their preservation is not claimed. All 150 production-like data entry hashes remained unchanged.",
  "dynamic_guard_smoke": "11 passed; evidence subtree selected from a nested JUnit output path."
}
```

Storage is configured before game import through tests/helpers/storage_isolation.py and tests/conftest.py. Existing ASHEN_DATA_DIR and ASHEN_PROVIDER_USAGE_PATH select disposable storage. A Python audit guard rejects writes/removes/renames to repository data, including explicit stale constants. This is test tooling, not a replacement persistence system. Snapshot paths derive from the configured root; fixtures may select further temporary roots. HTTP and holdout roots are under artifacts/pr_play_72. Browser host root was isolated before attachment.

Conservative line inventories in test_write_inventory.json cover campaigns, sessions, chat/log, saves, provider logs and import/lifespan risk. This lexical inventory identifies possible writers rather than proving a complete static call graph. No uncontrolled native writers or unguarded provider experiments were used.

Original expected session-log SHA256: b4706f3bb214861c34f7b9304ba39f4e51b72a7d8ef9e093cc83256311a33b13. Current bytes were copied before tests. Read-only repository file/archive searches found no exact match; no recovery is claimed.

```json
{
  "entries": 150,
  "preserved": 150,
  "changed": [],
  "session_log": "a6952ab704fabba72c92e4f88f4961c474705560cc7b2b1dea4d8fbbd90439e6",
  "historical_original_recovered": false
}
```

