# PR-PLAY-26 state integrity

Snapshots: live/initial before reset, live/baseline after the sole /api/new_campaign reset and before opening, live/opening after start, live/turns/T1/before and after, live/after after cleanup. No post-follow-up state exists. Raw snapshots and normalized diffs are preserved.

Initialization publishes the opening and initializes normal scene/turn context. During conversation: turn_counter 1 -> 2, time_pressure 1 -> 2; interlocutor/engagement and history updated. Each faction pressure and agenda_progress advances by one through existing deterministic progression; Ordo Pyric pressure event added. NPC last_interaction_turn changes null -> 2 (game/social.py:3811); relationship values and revealed knowledge remain unchanged. These are normal turn progression, not dialogue-created facts or rewards. See game/world.py:160-172, game/world_progression.py and native CTIR progression evidence.

Location and date unchanged; character/inventory/currency documents, NPC relationships and persistent NPC knowledge, quest/clue/lead state and remaining world facts unchanged. Machine checks all pass: True. Full diffs retain runtime and telemetry changes.

Unauthorized mutations: none found. Narrative/state mismatches: none found in published dialogue. It only advertises existing offerings. Hidden-information protection: restricted-string scan results in confidentiality_verification.json; manual transcript review finds no hidden truths/private quest or restricted NPC disclosures. The sole exact match is _runtime_canonical_ctir_stamp_v1 telemetry, not a hidden campaign fact; explicitly classified in the scan evidence. Exact-string detection is a limited check, not a proof against all paraphrases. Diagnostics remain internal evidence.

Owned process stopped and loopback port released; no gameplay source/state was changed to improve results.
