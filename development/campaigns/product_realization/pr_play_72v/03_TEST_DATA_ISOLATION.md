# PR-PLAY-72V — TEST DATA ISOLATION

Before mutating tests, the existing tests.helpers.storage_isolation.install helper configured isolated roots and an audit guard. Campaign/world/character/conditions templates were copied read-only. Session, log, combat, scenes, snapshots and provider usage derive from ASHEN_DATA_DIR or ASHEN_PROVIDER_USAGE_PATH. HTTP, holdout, browser, latency and analysis have distinct roots under artifacts/pr_play_72v; pytest uses temporary fixture roots. Reports and XML go to this cycle. No import-time protected write succeeded.

The controlled save/load probe and unchanged hashes are in isolation.json. The guard later blocked a legacy test's hardcoded historical-report write; another redirected output was incorrectly reused for fixture input. Only these test boundaries were repaired. isolation_repairs.xml verifies both. The guard was never disabled. protected_integrity.json records all 150 entry/final hashes.
