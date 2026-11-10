# ADVERSARIAL LEAKAGE TESTS

Existing CANARY_* fixtures carry GM notes, private NPC motives, hidden destination/clue identifiers, quest twists and unrelated world data. Frozen HOLDOUT_SENTINEL_* cases add internal fields and nested objects. Synthetic exception/import/request sentinels exercise error serialization. Full-body scans detect zero exposures after repair. Source sentinels remain in server state and serialized snapshot storage.

Fixtures and schema paths are in frozen_holdout.json and tests/test_pr_play_67_player_projection.py. Leakage checks do not infer privacy from key names alone: unknown leaf values under innocuous nested keys are excluded by source-specific schemas. An actual player-authorized narration/string field still relies on its established upstream authority; this cycle does not claim universal semantic information-flow proof.
