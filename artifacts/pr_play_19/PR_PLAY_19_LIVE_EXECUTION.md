# PR-PLAY-19 Live Execution
Timestamp: 2026-11-01T15:59:21.612636+00:00 (2026-11-01 10:59:21 EST, America/New_York).

Exact invocation from repository root:
```powershell
.venv/Scripts/python.exe artifacts/pr_play_19/execute_validation.py live
```
The wrapper calls existing runner.run_playtest(scenario='CampaignOpening', mode='Live', authorize_live=True, capture_response=True, output_root=artifacts/atgb/pr_play_19/live). It launches the existing worker through worker_capture.py for observation. Application endpoints, adapter, admission, parsing, rendering and persistence execute normally.

| Milestone | Actual result |
| --- | --- |
| HTTP readiness | PASS; diagnostics/http_ready.json |
| Provider requests | 1 admitted, 1 dispatched, 1 completed; zero pending |
| Real provider HTTP | 200 POST /v1/responses |
| Schema acceptance | PASS; completed strict response |
| JSON parsing / plan compliance | PASS; six approved required selections in order |
| Renderer acceptance | PASS; renderer_result.json ok=true |
| Opening publication | PASS; start_campaign HTTP 200, ok=true, campaign_started=true |
| Publication confidentiality | FAIL at raw response boundary; see publication_boundary_review.json |
| Ordinary turns | 0 |
| Stop reason | Successful initialization; no subsequent action |

Provider response ID: resp_0debce0c8046739d006ae761e1443087d2888801cc5ff5066a. SDK request ID: req_6c06c16e18104bdf9c912097f45943bf. Returned model gpt-4.1-mini-2025-04-14. No provider error, refusal or incomplete status. Provider status completed. Worker stopped and port released (live_port_release.json); harness uses process termination and reports exit code 1, not graceful lifespan completion.

Evidence root: artifacts/atgb/pr_play_19/live/20261101T155921Z-dece64b94204. Preserve diagnostics/provider_usage.jsonl, provider_http.json, provider_response.json, renderer_result.json, prepared_public_catalog.json, predipatch check (predispatch_contract_check.json), baseline/, after/, reports/result.json and existing evidence/evidence.zip. The generic parser_output_form diagnostic says malformed even though JSON parsing/structured validation, renderer, semantic checks and publication all pass. Treat that field as a telemetry inconsistency; no parser rejection occurred.

Confirmed issue: raw start response includes campaign.character_secret.hidden_truth and debug roots. Expected player-mode response applies public projection. Evidence: response in reports/result.json versus baseline/after api_state public_state, publication_boundary_review.json; game/api.py:6297-6342 calls api_turn_support._build_turn_response_payload:1382 and returns the raw composed state. Default UI mode is player (api_ui_mode.py:16). Confidence HIGH for HTTP exposure; actual browser display untested. Failure boundary: response packaging after valid rendering/persistence. Smallest next investigation: audit/project successful start_campaign responses through the established public channel; no repair performed here.
