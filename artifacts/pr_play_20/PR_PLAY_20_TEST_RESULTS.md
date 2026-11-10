# PR-PLAY-20 test results

Command (offline): `.venv/Scripts/python.exe -m pytest tests/test_pr_play_20_response_confidentiality.py
tests/test_pr_play_18_contract_alignment.py tests/test_pr_play_13_opening_renderer.py
tests/test_pr_play_04_opening_integrity.py tests/test_start_campaign_api.py tests/test_state_channels.py
tests/test_ui_mode_backend_integration.py tests/test_ui_mode_policy.py tests/test_turn_pipeline_shared.py
tests/test_frontend_ui_mode_hardening_objective15.py tests/test_ui_mode_regression_matrix_objective15.py --tb=short`.

Result: 17 failed, 172 passed, 1 warning in 76.13s (0:01:16). Full output: test_results.txt.

Focused regression mapping: A/B/C/D/E successful_start_serialized_boundary; F ordinary action success;
G ordinary rejection plus rejected_turn_with_composed_state; H invalid presentation plan and repeated
start; I player state retrieval; J established author/debug reads preserved and runtime mode denial.
The focused file has five collected cases, all passing. Serialized text is checked for the sentinel
anywhere, and complete response dictionaries must equal the recursive public projection.

Offline end-to-end initialization enters the real application lifespan and FastAPI HTTP route with
temporary storage. The real provider request builder/parser and engine renderer run; only SDK transport
is stubbed using PR-PLAY-18's helper. One mock presentation-plan dispatch occurs, opening publishes once,
one turn commits, public synchronization fields survive, and repeats return 409 without another dispatch.
Original and repaired narration and initialization summaries match (compatibility_comparison.json).

Provider/network controls: pytest live-model guard, skipped startup preflight, SDK constructor stub,
and external socket-connect denial in the new fixtures. Windows asyncio's internal loopback socketpair
is allowed. No real provider request occurred. Mock dispatch counts are not provider requests.

Existing failures: test_start_campaign_emits_opening_and_sets_started;
test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text;
test_start_campaign_promotes_valid_upstream_prepared_scene_opening. They assert prose substring/length
or upstream-prepared promotion behavior. All three reproduce with the projection helper replaced by
identity (preexisting_start_tests.txt: 3 failed, 9 passed), showing they precede this confidentiality repair.
The shared-turn suite additionally has 14 preexisting failures, reproduced with projection disabled
(preexisting_turn_tests.txt: 14 failed, 61 passed). Before diagnostic-assertion migration it reported
26 failures; afterward it returns to the same 14 preexisting failures. Failures concern routing, retry
expectations, older response shapes and prose/emission behavior. They were not fixed by changing game
behavior. All 17 remaining failure node IDs match the two projection-disabled comparison runs; see
preexisting_failure_comparison.json. Initial narrower run: 86 passed, 3 failed.

Evidence limitations: TestClient serializes actual ASGI HTTP responses without opening a listening
server; this validates the application response path, not live network deployment. Exported response
JSON is parsed from actual response bytes and sanitized for external review. No live gameplay was run.
