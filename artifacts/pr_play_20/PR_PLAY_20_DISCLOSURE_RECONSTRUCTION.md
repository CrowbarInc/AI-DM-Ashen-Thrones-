# PR-PLAY-20 disclosure reconstruction

Confirmed historical disclosure: `POST /api/start_campaign`, default player mode, HTTP 200,
`response.campaign.character_secret.hidden_truth`. The response contains a broad flat state bundle
alongside `ok`, `gm_output` and `resolution`; this is not the `/api/state` envelope.

Evidence: `artifacts\atgb\pr_play_19\live\20261101T155921Z-dece64b94204/reports/result.json`, `steps[2].response`; after/persistent/campaign.json;
baseline/api_state.json and after/api_state.json. The hidden value is nonempty, matches the persisted
campaign, and is absent from both public-state captures. Only structural evidence is exported in
pr_play_19_structural_verification.json; real secret values and original historical payloads are excluded.

`game/api_turn_support.py:1382` reads `compose_state()` and constructs
`{'ok': True, 'gm_output': gm, **state}`. It does not invoke the public projection.
The opening persistence tail replaces the GM output with its canonical internal object and enriches
metadata before returning. Consequently filtering only the initial GM object would be insufficient.

Baseline offline reproduction used the actual FastAPI route via TestClient and the real opening
provider/parser/renderer path with an SDK constructor stub returning a valid presentation plan.
HTTP 200 included `PR_PLAY_20_HIDDEN_SENTINEL`; public state excluded it; authority retained it.
Nested campaign internal state, world internal state, scene hidden facts and synthetic hidden NPC/quest
records also appeared. See baseline_summary.json, baseline_response.json and baseline_test.txt.
The baseline regression failed at the nested hidden-record assertion after recording the response.

Historical structural comparison also identifies nonpublic scene/session/debug paths in the same
successful response; paths are preserved without their values. UI display of these fields was not tested.
The fixture proves the response boundary under the established key-based policy, not semantic secrecy
of arbitrary strings or unclassified keys. No live-provider reconstruction was attempted.
