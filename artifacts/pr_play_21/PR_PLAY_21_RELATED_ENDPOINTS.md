# PR-PLAY-21 related endpoint review

All read endpoints in the FastAPI route inventory were checked for the shared
selector path. No separate read-only character, NPC, quest or world endpoint
exists here; their available state is nested in `/api/state` and passes through
its public recursive projection. Their public/hidden classification is unchanged.

| Endpoint | Selector / original check | Potential restricted serialization | Repair |
| --- | --- | --- | --- |
| GET /api/state | query ui_mode; membership only | author_state, debug_state, nested campaign/scene/world/character data | shared resolver 403 before compose_state |
| GET /api/log | query ui_mode; membership only | debug returns complete enriched entries, including resolution/internal state | shared resolver 403 before load_log |
| GET /api/debug_trace | query ui_mode; requested debug capability | raw session.debug_traces | shared resolver 403 before load_session |
| GET /api/snapshots | query ui_mode; runtime-only policy | id/time/operator label metadata only; no snapshot contents | public metadata retained; privileged requests 403 before listing |
| POST /api/campaign | query or body ui_mode/uiMode; requested author-write capability | merged existing campaign on response; confirmed source-connected alternate author-read path | same resolver denies before read/write |
| POST /api/scene, /api/world | query or body ui_mode/uiMode; requested author-write capability | request data echoed/saved; no independent entitlement | same resolver denies before writes |
| POST /api/snapshots, /api/snapshots/load, /api/reset_session | runtime-only policy; shared state projection | public_state for admitted player mode | privileged denial inherited; public behavior unchanged |
| POST /api/action, /api/chat, /api/start_campaign | runtime-only policy; PR-PLAY-20 final public boundary | player-only HTTP response | existing runtime denials and public projection preserved |

Source locations: `game/api.py:5108-5136`, `:5150-5170`, `:5203-5211`,
`:5298-5360`; common resolver `game/api_ui_mode.py:16-48`; shared state helper
`game/api.py:5024`; log helper `:5093`. Policies are in `game/ui_mode_policy.py`;
projection recursion is in `game/state_channels.py`.

Baseline HTTP confirms four disclosing endpoint/mode combinations: author state,
debug state, debug log, debug_trace. Author-mode log was public but lacked
authorization for the selected mode, so it also now fails closed. Campaign POST
was additionally source-confirmed: save_campaign merges existing fields then
returns load_campaign; caller-controlled author mode could therefore return
existing hidden fields. Body selector regression tests cover campaign/scene/world
denial and persistence preservation. No new unsupported header/body selector
interface was invented. Read routes consume only query ui_mode; HTTP headers
provide no authorization mechanism. Duplicate query semantics remain the
framework's final-value semantics, with safe projection for an effective player
value and denial for an effective privileged value.

Error paths use the existing JSON error adapter. The privileged error is a fixed
constant with no state/diagnostics; unknown selectors still use 400. Tests replace
state loaders/projectors with failure sentinels to prove privileged read denial
precedes data access and examine complete serialized HTTP text.

Scope: same resolver/projection mechanism only. Other runtime mutations are not
certified safe for untrusted clients. Snapshot labels are operator metadata under
the existing contract, not an alternate way to download hidden snapshot state.
