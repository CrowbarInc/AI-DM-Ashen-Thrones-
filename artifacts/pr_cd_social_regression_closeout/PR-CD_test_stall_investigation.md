# PR-CD Test Stall Investigation

Target file:

```text
tests/test_social_question_relevance_answer_selection.py
```

## Verbose run

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py -vv -s --tb=short --basetemp=codex_pytest_tmp_prcd_stall
```

Observed progress before silence:

```text
collected 24 items
test_general_ask_about_a_does_not_emit_b PASSED
test_general_ask_about_b_does_not_emit_a PASSED
test_general_unsupported_question_does_not_substitute_or_invent PASSED
test_general_relevant_but_unauthorized_does_not_leak PASSED
test_general_plain_relevant_answer_beats_unrelated_hook PASSED
test_general_relevant_authorized_hook_still_fires PASSED
test_general_natural_paraphrase_keeps_relevant_topic PASSED
test_general_first_ask_without_warmup PASSED
test_general_followup_context_does_not_hijack_with_unrelated_hook PASSED
test_general_explicit_subject_change_can_move_to_other_owned_topic PASSED
test_general_rejected_candidate_leaves_no_consequence PASSED
test_general_answer_selection_does_not_create_knowledge PASSED
tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b
```

Last completed test: `test_general_answer_selection_does_not_create_knowledge`.

Currently executing test at silence: `test_general_http_ask_a_not_b`.

Elapsed time: greater than 45 seconds for the individual test; the full-file run remained silent until interrupted.

## Individual reproduction

Command:

```text
.\.venv\Scripts\python.exe -c "... subprocess.run([... test_general_http_ask_a_not_b ...], timeout=45) ..."
```

Result: timeout after 45 seconds.

## Stack evidence

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b -vv -s --tb=short -o faulthandler_timeout=20 --basetemp=codex_pytest_tmp_prcd_fault
```

Representative stack:

```text
socket.py line 295 in accept
socket.py line 646 in socketpair
asyncio/proactor_events.py line 785 in _make_self_pipe
asyncio/windows_events.py line 315 in __init__
anyio/_backends/_asyncio.py line 2480 in run
anyio/from_thread.py line 536 in run_blocking_portal
starlette/testclient.py line 426 in _portal_factory
starlette/testclient.py line 351 in handle_request
httpx/_client.py line 1014 in _send_single_request
starlette/testclient.py line 555 in post
tests/test_social_question_relevance_answer_selection.py line 210 in _chat
tests/test_social_question_relevance_answer_selection.py line 355 in test_general_http_ask_a_not_b
```

CPU/process note: while the session appeared active, `Get-Process` did not show an active `python` process in a separate shell snapshot. The visible stack points to blocking during Windows asyncio event-loop/TestClient portal setup rather than social resolver computation.

## Isolation

Non-HTTP slice:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py -k "not http" -q --tb=short --basetemp=codex_pytest_tmp_prcd_social_no_http
```

Result:

```text
19 passed
```

## Cause classification

Classification: C is not supported. The stall is best classified as B / C-blocking-test-infrastructure, not a PR-CC social reply regression.

Evidence:

- The stalled frame is in Starlette/FastAPI `TestClient` / AnyIO / Windows asyncio socketpair setup.
- The application handler and social resolver are not reached in the captured stack.
- The same TestClient-pattern blocker appears in broad regression at a different file (`tests/test_activate_scene_validation_and_get_persistence.py::test_invalid_activate_scene_id_ignored_safely`).
- The pure social relevance tests pass (`19 passed`).
- No external provider call was made; `tests/conftest.py` also installs live-model guards.

No bounded repair was implemented because the blocker is not directly caused by PR-CC and repairing Windows TestClient/AnyIO behavior is outside this closeout scope.
