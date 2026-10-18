PR-DW implementation report

Decision: D - LIVE INTERPRETATION BLOCKED.

Summary:
- Added a minimal `ASHEN_DATA_DIR` persistence override in `game/storage.py` so the existing application can run against disposable copied save data.
- Started the normal FastAPI application with `python run.py` on `http://127.0.0.1:8000`.
- Verified the real HTTP state/log/chat/error transport.
- Verified the browser UI loads, accepts player input, sends through the existing UI transport, and displays the player-visible GM response.
- Stopped short of a human unscripted live playtest because the ordinary chat path misclassified an explicit OOC probe and made live narration provider calls.

Important finding:
- Input: `OOC: I am checking whether the interface is alive; do not change game state.`
- Result: treated as an inspect-style request, advanced `turn_counter` and `time_pressure`, and generated a GM response: `The inspection establishes no further reliable detail from the current scene.`
- This violates PR-DW IC/OOC safety expectations for ordinary OOC input.

No production save mutation observed:
- Production `data/session.json` remained `turn_counter: 0`, `last_saved_at: 2026-10-09T22:36:15.473168Z`.
- Disposable save path was `artifacts/pr_dw_interactive_playtest/disposable_data`.

