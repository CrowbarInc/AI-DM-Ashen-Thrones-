# PR-CF Representative Reproductions

No live model/API calls were made.

## PR-CE Preserved Evidence

PR-CE recorded the broad command and result: 7431 passed, 202 failed, 99 skipped, 0 timed out, 0 interrupted. It also recorded that `tests/test_social_question_relevance_answer_selection.py` completed with 20 passed and 4 failed, and that those four failures were narration assertions, not TestClient hangs.

## PR-CF Last-Failed Diagnostic

`artifacts/pr_cf_regression_triage/lastfailed_diagnostic.xml` contains 202 failing/error testcases across 65 files. Because the first PR-CF diagnostic used a nested `--basetemp` whose parent did not yet exist, 161 entries are setup errors with `FileNotFoundError` for `artifacts/pr_cf_regression_triage/pytest_lastfailed`. These are not application failures and are marked as environment/fixture noise in the inventory.

The 41 non-noise failures show real signatures: speaker contract mismatch, governance/import guard expectation drift, dialogue plan fallback accepting quoted speech, fallback/state TypeError, final emission orchestration metadata shifts, social reply kind `unknown` vs `refusal`, prompt guidance text drift, reactive-player stop reason drift, and live-model guard blocking an unstubbed provider call.

## Representative HTTP Rerun

A bounded representative run over turn pipeline, explicit world action, social relevance, exploration, and investigation tests was interrupted after faulthandler showed the Windows TestClient/socketpair `accept` hang in `tests/test_turn_pipeline_shared.py::test_action_and_chat_social_use_equivalent_shared_turn_logic`. This directly reproduced the infrastructure frame PR-CE had investigated, so further HTTP representative reproduction was stopped.
