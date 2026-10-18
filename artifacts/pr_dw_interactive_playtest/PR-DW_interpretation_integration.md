PR-DW interpretation integration

Existing integration observed:
- `static/app.js` submits normal player chat to `/api/chat?ui_mode=player`.
- `game.api.chat()` contains PR-DU stored interpretation bridge support through `_stored_interpretation_for_player_text()` and `normalized_action_from_interpretation()`.
- Rejected stored interpretations are blocked by `_stored_interpretation_blocks_execution()`.
- Live semantic interpretation is controlled by `ASHEN_DISABLE_LIVE_INTERPRETATION`.

Observed ordinary input behavior:
- With live interpretation disabled, deterministic fast path still interpreted a generic OOC probe as inspect-like gameplay.
- The generic OOC probe caused `turn_counter: 1` and `time_pressure: 1`.
- Interpretation telemetry showed `interpretation_api_calls: 0`; the provider calls were narration generation, not semantic interpretation.

Conclusion:
- The existing PR-DU bridge is present.
- Ordinary player input is not safely connected for broad IC/OOC handling.
- Explicit OOC handling is currently phrase-narrow rather than robust.

