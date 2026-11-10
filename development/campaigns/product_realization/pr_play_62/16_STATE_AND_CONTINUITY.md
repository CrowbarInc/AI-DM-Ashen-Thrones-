# State and continuity

Zero protected canonical data/baseline hash changes relative to entry. Storage
is patched to disposable directories before initialization. before_initialization
records absent disposable storage; after_initialization captures authority.
Per-turn projections, final complete session and final authority are preserved.

All five per-action mechanical resolutions and authority projections match the
deterministic control, excluding campaign_run_id. Campaign/player/scene remain
stable within each run. Compared: visited scenes, clues, inventory, equipment,
HP, conditions, NPC runtime, quests, world flags, clocks and combat. The route is
recorded once and retained across repeats/fallbacks. Full terminal session records
conversation/history; intermediate projections are not complete raw-session dumps.

Deterministic changes: turn 1 route disclosure; time_pressure +1 per action in
game/api.py; at pressure 3 the existing game/world.py faction agenda update sets
the same three flags in control and experiment. Normal runtime initialization
and action/conversation history are host changes, never candidate instructions.
All required faults match deterministic first-action authority too.

A distinct session received no experimental marker. Default/off and session
binding regressions are rerun. No narration-to-state write channel was introduced.
State equality does not establish open-ended narration safety.
