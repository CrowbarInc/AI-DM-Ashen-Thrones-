# 06 — UI Failure Feedback

PR-PLAY-07 · 2026-10-29 America/New_York. Synthetic-provider evidence only.

The old handler indirectly recognized HTTP 422 via ok=false and read data.error, then
called reloadAll. loadLog erased chatLog and rebuilt from saved entries. Failed opening
has no narration/log entry, so its error disappeared. State refresh caused silent failure;
422 recognition itself existed. Fetch/JSON exceptions escaped with no useful feedback.

Localized handler now explicitly recognizes HTTP errors/422/ok=false and shows safe text:
campaign did not start, no gameplay commit, retry available. Failure refresh calls loadState
only; refresh failure keeps feedback visible. Already-started 409 gets truthful separate
feedback. Existing upstream/budget blocked presentation remains. Provider internal error
text is not exposed in the new player failure path. Network/JSON errors instead say the
request could not be confirmed and require state refresh, because transport loss cannot
prove the server did not commit. Finally restores busy/button state from authoritative UI.
Success retains normal narration and log reload. No fabricated narration, auto-retry,
false success, duplicate initialization or backend gameplay change.

U1 success/log/started state; U2 semantic rejection visible; U3 HTTP provider exception
without raw detail; U4 explicit 422; U5 same handler failure->successful manual retry;
U6 repeated Start after success/initial started state sends no duplicate; U7 failed state
refresh retains feedback. Transport and invalid JSON controls also pass. Nine cases in
artifacts/pr_play_07/ui_results.json. tests/helpers/pr_play_07_ui.cjs executes the actual
localized handler in Node vm with browser-boundary stubs; existing frontend source-contract
tests also pass. This is not rendered-browser/screenshots evidence. Backend tests separately
prove rollback for rejected opening and exactly one commit on valid retry.
