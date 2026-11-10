# PR-PLAY-21 baseline reproduction

Actual FastAPI application routes were exercised with TestClient, application
lifespan, temporary synthetic storage, blocked live-model constructors and blocked
external sockets. Windows asyncio's internal loopback socketpair is permitted.
No listening server or real campaign was used. The first capture attempt failed
startup because its fixture omitted an exit target; switching to the existing
complete backend fixture resolved that setup issue before capture.

Fixture: `scene.scene.hidden_facts = ["PR_PLAY_21_PRIVILEGED_SENTINEL"]`;
`session.debug_traces` contains a synthetic debug sentinel; a log entry contains
a synthetic `resolution.internal_state` sentinel. Public narration/input are
distinct ordinary strings. Original source hash and complete serialized response
structures are in `baseline_http.json`. Restricted non-sentinel strings are
redacted; the sentinel-presence flags were computed on original response text.

| GET request | Status | Requested/effective mode | Sentinel in serialized response |
| --- | --- | --- | --- |
| /api/state | 200 | player/player | No |
| /api/state?ui_mode=author | 200 | author/author | Yes |
| /api/state?ui_mode=debug | 200 | debug/debug | Yes |
| /api/log | 200 | player/player | No |
| /api/log?ui_mode=author | 200 | author/author | No (public transcript) |
| /api/log?ui_mode=debug | 200 | debug/debug | Yes |
| /api/debug_trace | 403 | player/none | No |
| /api/debug_trace?ui_mode=debug | 200 | debug/debug | Yes |
| /api/snapshots | 200 | player/player | No (metadata only) |

Baseline author response keys: `ui_mode`, `public_state`, `author_state`.
The author lane includes `scene.scene.hidden_facts` with the exact sentinel.
Debug state has `debug_state`; debug log contains enriched raw resolution;
debug_trace returns `traces` verbatim. No independent authorization was checked.
The debug-trace check tested the requested mode's capability only.

Source trace: `game/api_ui_mode.py:16` resolves query/payload then validates mode
membership; `game/api.py:5111` calls it, composes state, and invokes
`_project_state_for_ui_mode` (`:5024`). That helper selects recursive public,
author, or debug projections from `game/state_channels.py`. Log selection is
`_project_log_entry_for_ui_mode` (`:5093`), called by `/api/log` (`:5118`).
`/api/debug_trace` (`:5128`) uses `assert_mode_allows_debug_read` then loads session.
The projection helper is functioning as designed; the missing permission check
at its HTTP entry is the defect.

Reproduction command, before repair:
`.venv/Scripts/python.exe artifacts/pr_play_21/capture_http.py artifacts/pr_play_21/baseline_http.json`.
After repair the same harness writes `repaired_http.json`: all author/debug
requests above return 403, no effective projection, fixed error body, no sentinel.
Both captures confirm the authoritative scene sentinel remains stored.
