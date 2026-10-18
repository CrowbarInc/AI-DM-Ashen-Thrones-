# 22 — Persistence and State Integrity

Save/load checks ran on turns 4, 8, and the last turn of each conversation. Results are in `state_audit.json`. No `save_load_mismatch` is present.

Nonpassive world diffs: [].

Observed world paths are the passive faction and event-log ticks recorded on each turn. Generated sentences did not add a quest, a reward, a patrol schedule, a secret, or a faction relationship. Commitment diffs are included per turn in the state audit.

Adopted lines are the last delivered-history sentence of their turn. The north-street candidate is not among them. The characterization sentence is present because it was adopted, and a later turn reused that adopted line as the host fallback.

Primary turn 15 asked whether the preference still held and delivered the adopted explanation with zero provider calls. That is stored speech, not a new generation.
