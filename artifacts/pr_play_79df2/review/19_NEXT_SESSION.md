# Next session

PR-PLAY-79D-F2 is B / PARTIAL. Do not start AT-OPT-01.

The NPC dialogue defect is repaired: accepted speech and grounded fallbacks each leave one publication whose visible sentence is the sentence delivered, with provenance kept apart.

Exact remaining blocker: a non-mutating interpretation admission refusal publishes a player-facing sentence and a publication event, and leaves `session.last_publication` on the earlier gameplay turn.

Smallest correction: on that return, do not emit a completed-gameplay publication event, so the event and the pointer agree without mutating a non-mutating refusal. If a later decision wants the pointer to move, call `note_completed_publication` there and rerun the historical lanes that compare persisted session state.

Do not open a broad PR-PLAY cycle for that correction. Do not commit or push until asked.
