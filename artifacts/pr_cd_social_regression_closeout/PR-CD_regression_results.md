# PR-CD Regression Results

Live provider calls: 0.

## Focused PR-CC tests

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_cc_social_reply_reconciliation.py tests\test_social.py::test_question_without_topic_marks_consequential_unknown_and_non_invention_hint tests\test_dialogue_social_plan.py tests\test_dialogue_social_plan_block_x_contract_pins.py tests\test_dialogue_social_plan_block_y.py -q --tb=short --basetemp=codex_pytest_tmp_prcd_focused
```

Result:

```text
36 passed
```

## Social relevance tests

Full file:

```text
tests/test_social_question_relevance_answer_selection.py
```

Result: timed out/hung at first HTTP TestClient case after 12 passed.

Isolated non-HTTP slice:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py -k "not http" -q --tb=short --basetemp=codex_pytest_tmp_prcd_social_no_http
```

Result:

```text
19 passed
```

## Social resolver tests

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_social.py -q --tb=short --basetemp=codex_pytest_tmp_prcd_social_resolver
```

Result:

```text
31 passed
```

## Dialogue social plan tests

Included in the focused PR-CC command above:

```text
tests/test_dialogue_social_plan.py
tests/test_dialogue_social_plan_block_x_contract_pins.py
tests/test_dialogue_social_plan_block_y.py
```

Result included in focused total:

```text
36 passed
```

## PR-BY retry-contract and PR-BW narration-only tests

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_by_narration_only_retry_contract.py tests\test_pr_bw_narration_only_envelope.py -q --tb=short --basetemp=codex_pytest_tmp_prcd_bybw
```

Result:

```text
27 passed
```

## Authority integrity tests

Combined broader authority run:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_br_resolution_contract.py tests\test_pr_br_authority_reconciliation.py -q --tb=short --basetemp=codex_pytest_tmp_prcd_authority
```

Observed: 26 passing dots printed, then no further output before interruption. No pass claim is made for the combined run.

Focused authority controls:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_br_resolution_contract.py::test_consequential_information_does_not_enter_incidental_authority tests\test_pr_br_authority_reconciliation.py::test_incidental_structured_narration_can_seal_without_a_consequential_claim -q --tb=short --basetemp=codex_pytest_tmp_prcd_authority_focus
```

Result:

```text
2 passed
```

## Broad deterministic regression

Command:

```text
.\.venv\Scripts\python.exe -m pytest -q --tb=short -o faulthandler_timeout=30 --basetemp=codex_pytest_tmp_prcd_broad
```

Outer timeout: 90 seconds.

Result:

```text
TIMEOUT after 90 seconds
13 passing dots printed before timeout
```

Representative blocking stack:

```text
socket.py line 295 in accept
socket.py line 646 in socketpair
asyncio/proactor_events.py line 785 in _make_self_pipe
anyio/from_thread.py line 536 in run_blocking_portal
starlette/testclient.py line 426 in _portal_factory
starlette/testclient.py line 351 in handle_request
starlette/testclient.py line 555 in post
tests/test_activate_scene_validation_and_get_persistence.py line 77 in test_invalid_activate_scene_id_ignored_safely
```

Broad deterministic regression did not complete and is not claimed as passed.

## Summary counts

- Passed: 36 focused PR-CC/dialogue plan + 19 social relevance non-HTTP + 31 social resolver + 27 PR-BY/PR-BW + 2 focused authority controls.
- Failed: 0 in completed slices.
- Skipped: none reported in completed slices.
- Timed out: social relevance full file HTTP lane; broad deterministic regression.
- Interrupted: broader authority run after partial passing output.
