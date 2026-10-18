# 18 — Persistence and State Integrity

Adoption integrity findings on the repaired transcript: [].

For every adopted turn, the candidate equals the quoted player-facing sentence and is the final delivered-history sentence. For every rejected turn, the candidate is absent from player-facing text and from delivered history. Save/load was requested during the live plan; no `save_load_mismatch` flag was recorded. `state_audit.json` lists per-turn world paths. Observed world diffs are passive faction-pressure and event-log ticks. `world_nonpassive_diff` is empty on the repaired turns. No new quest, reward, patrol schedule, secret, or faction relationship was written from a generated sentence.

The pre-repair “north street” sentence is retained in the historical transcript. It is not part of the repaired session. Rejected characterization and refusal candidates from the repaired run remain only in the expression audit.
