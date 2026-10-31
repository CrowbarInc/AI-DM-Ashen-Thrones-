# PR-BP Verification Results

- PR-BN plus PR-BP focused: 28 passed.
- Focused obligation/routing/retry group: 64 passed.
- Core playability evaluator: 26 passed.
- Adjacent historical regression band: 182 collected, 176 passed, 6 failed.
- Wider evaluator/tool band: 5 failures in pre-existing reactive-player termination behavior.
- `py_compile`: passed.
- `git diff --check`: passed (line-ending warnings only).

The six adjacent failures are the previously recorded discovery-memory identifier mismatch and passive-pressure/suspicious-figure behavior failures in `test_turn_pipeline_shared.py`.
