# PR-CE TestClient repair

## Decision

No TestClient or event-loop change was applied.

## Why a policy switch was not applied

`WindowsSelectorEventLoopPolicy` works for a trivial `TestClient` request (200 in 0.027s). On Python 3.12 for Windows, the selector loop still creates its self-pipe with `socket.socketpair()`, and native `socketpair` is absent. A selector policy therefore does not remove the `accept()` frame from the PR-CD stack.

The default Proactor path also completed every isolated probe and the previously stalled HTTP tests. There is no demonstrated failure on this machine for a policy change to fix.

An unconditional or production event-loop override was not added.

## What was verified after leaving the harness unchanged

1. Minimal reproduction: all eight isolated cases completed. See `PR-CE_testclient_minimal_reproduction.md`.
2. `test_general_http_ask_a_not_b`: completed, assertion failed, no timeout.
3. Full `tests/test_social_question_relevance_answer_selection.py`: 20 passed, 4 failed, no timeout.
4. `test_invalid_activate_scene_id_ignored_safely`: passed.
5. `tests/test_activate_scene_validation_and_get_persistence.py`: 6 passed.

The four HTTP assertion failures are pre-existing narration results, recorded in `focused_tests.txt`. They are outside the subjective-classifier edit. No workaround was added to turn them green.
