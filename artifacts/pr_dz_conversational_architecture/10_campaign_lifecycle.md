# Campaign Lifecycle

Current implementation:

- New campaign/reset exists: `/api/new_campaign`.
- Structured start exists: `/api/start_campaign` (`game/api.py:5592`).
- Fresh-run eligibility exists: `_session_allows_structured_start_campaign()` at `game/api.py:4248`.
- Opening narration resolution exists: `_opening_scene_normalized_action_and_resolution()` at `game/api.py:4215`.
- Chat start recognizer exists: `_is_campaign_start_turn_request()` at `game/api.py:4157` with exact cue phrases.
- The UI exposes Start Campaign button (`static/app.js:649`).

Product gap: lifecycle is implicit. There is no robust natural-language lifecycle router; plain chat start depends on cue matching and fresh log/turn state.

Minimum mechanism: after New Campaign, show or automatically trigger opening narration. Plain chat requests like "Would you start the game?" should route to the same opening lifecycle when the session is fresh.
