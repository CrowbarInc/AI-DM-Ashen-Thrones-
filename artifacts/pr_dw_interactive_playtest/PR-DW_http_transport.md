PR-DW HTTP transport

Verified against real running server, not FastAPI TestClient.

Endpoints checked:
- `GET /api/state?ui_mode=player`: returned player public state, scene `frontier_gate`, UI affordances, save summary.
- `GET /api/log?ui_mode=player`: returned `{ ok: true, ui_mode: "player", entries: [] }` before chat probes.
- `POST /api/chat?ui_mode=player`: accepted player message and returned response payload.
- `POST /api/chat?ui_mode=author`: returned HTTP 403 with `ui mode 'author' may not trigger runtime actions`.

Transport result:
- HTTP transport works.
- Session continuity works in disposable save data.
- Error response handling works for forbidden runtime mode.

Transport safety finding:
- A generic explicit OOC chat probe was misrouted as gameplay-like inspection and made live narration provider calls.

