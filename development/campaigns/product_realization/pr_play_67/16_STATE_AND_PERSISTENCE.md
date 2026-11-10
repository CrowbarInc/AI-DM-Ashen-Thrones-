# STATE AND PERSISTENCE

Projection is pure and does not delete or rewrite GM state. Both modes retain session GM notes, world private motives and original scene-template canaries. Full snapshot files retain synthetic hidden values; snapshot load restores them while the player response excludes them. Projection tests independently compare source objects before/after and mutate a projected item to verify container detachment.

raw_authority_audit.json compares unredacted in-memory authoritative world/character/combat, scene, visited locations, runtime discovery/overlays, clocks, turn counter and GM notes across identical five-action enabled/disabled runs: 5/5 equal. Earlier full-session comparisons differ in session IDs, latency/debug stamps and presentation-memory snippets; those raw results are preserved, not relabeled as complete session equality. Protected hashes are in protected_integrity.json.

Existing explicit new-campaign/session reset semantics still clear runtime state by design; projection does not perform those resets. The app has one active persisted campaign store, not a multi-tenant session model; session-bound experiment tests do not prove a new concurrent authorization system.
