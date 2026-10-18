# PR-CG Regression Results

## Bounded Probe Matrix

See `PR-CG_reliability_matrix.json`.

Unsandboxed supported execution:

- Minimal TestClient outside pytest: passed, no timeout.
- Minimal TestClient inside pytest: passed, no timeout.
- Default Windows event-loop policy: passed, no timeout.
- `WindowsSelectorEventLoopPolicy`: passed, no timeout.
- Previously stalled turn-pipeline test: passed, no timeout.
- Previously stalled scene-activation test: passed, no timeout.
- Social relevance HTTP test: failed by assertion, no timeout.
- Mixed-order HTTP subset: executed, 3 passed and 1 assertion failure, no timeout.

## Repeated Verification

`repetition_verification.txt` records 3 repetitions each:

- Minimal TestClient pytest file: 3/3 passed.
- `tests/test_turn_pipeline_shared.py::test_action_and_chat_social_use_equivalent_shared_turn_logic`: 3/3 passed.
- `tests/test_activate_scene_validation_and_get_persistence.py::test_post_scene_activate_clears_interaction_context`: 3/3 passed.
- `tests/test_explicit_world_action_social_lock_override.py::test_http_inspect_while_bound_is_not_social_probe`: 3/3 passed.

No hangs or timeouts occurred in the repeated supported run.

## Application Assertion Failure

`tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b` executed and failed with an ordinary assertion:

```text
assert "morning bell" in text or "kiln three" in text
```

The response text was:

```text
kiln tender says, "i cannot answer that from what is settled here."
```

This is preserved as application behavior evidence, not an HTTP harness hang.

