# PR-PLAY-20 repair report

Root cause: an internal mixed-visibility state bundle was treated as a finished player HTTP response.
The existing `/api/state` projection was never applied to successful turn packaging, and opening
enrichment could restore internal GM fields after initial packaging.

Production modification: game/api.py adds `_project_player_runtime_response` and applies it at the
three final HTTP response boundaries: start_campaign, api_action and api_chat. A small internal
`_start_campaign_response` extraction lets all start rejection returns share the same boundary.
It reuses `deep_project_public_payload`, processing GM output, resolution, nested lists and state
together after enrichment. JSONResponse rejection status, headers and background callbacks survive;
content-length is recalculated. No visibility rules were added or weakened.

Tests added: tests/test_pr_play_20_response_confidentiality.py. Existing test_start_campaign_api.py
now expects emission diagnostics to remain in the debug log lane rather than the player response.
The directly related tests/test_turn_pipeline_shared.py now obtains diagnostic assertions from persisted
engine logs/session separately; it no longer relies on debug data in player HTTP responses.
source_changes.diff isolates this pass from preexisting working-tree api.py edits. No commit/push.

No renderer, prompt, schema, provider contract, model, budget, narration or authority mutation changed.
The full internal turn helpers remain usable by engine diagnostics and persisted logs. Projection
creates a new tree without removing engine secrets. Tests compare the whole campaign document and
the injected world subtrees before/after HTTP response generation; all survive unchanged.

Compatibility: public flat state fields, public_hint inside character_secret, public NPC/quest labels,
opening narration, initialization flags and turn counter survive. Baseline/repaired opening text and
initialization summaries match. compatibility_comparison.json lists removed and added paths. Removed
paths are author/debug classified under the existing policy, including emission diagnostics; diagnostic
consumers must use the established debug log/state surfaces. No legitimate public field is intentionally
removed. Run IDs and times vary naturally across independent fixture runs.

Limitations: key-based policy treats unknown keys as public and cannot infer secret semantics in text.
Existing client-selected privileged read lanes have no authentication check at this API boundary.
That separate authorization issue is documented, not redesigned. Seventeen older opening/turn pipeline tests fail
with and without projection; no unrelated gameplay repairs were made.
