# PR-CP regression results

LIVE CALLS: 0

## New replay tests

`tests/test_pr_cp_authorized_finalization.py`: 8 passed, 0 failed, 0 skipped.

## Focused regression

Command listed in `focused_tests.txt`.

371 passed, 4 failed, 0 skipped, 0 timed out, 0 interrupted. Elapsed about 10.6s.

Failed, all in `tests/test_exploration_resolution.py`:

- `test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `test_chat_observe_area_resolution_kwarg_to_build_messages`
- `test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `test_chat_exploration_parsed_routes_through_exploration`

Each failure is `resolution["kind"]` missing (`None` instead of `observe` or the exploration route). This repair does not edit exploration routing. `game/exploration.py` was not modified. Those four tests are not counted as repaired and are not counted as a narration-authority regression.

Passed groups in the same run:

- PR-CI authored-answer finalization (`tests/test_social_question_relevance_answer_selection.py`)
- PR-CC social reply planning
- PR-CE subjective classification
- PR-CK resolver selection
- PR-CN contextual extraction
- decision-level authority, claim extraction, and narration validation under the PR-BR / PR-BU files in the command
- immutable-response and C18/C19 authority files, including the two assertion updates described in the implementation report
- grounded refusal grammar

## Shared turn pipeline

`python -m pytest tests/test_turn_pipeline_shared.py -q --tb=no`

41 passed, 24 failed, 0 skipped, 0 timed out, 0 interrupted. Elapsed about 11.9s.

Inherited baseline was 41 passed / 24 failed. The after count is the same. The 24 failing names are the dialogue-lock, social-retry, mixed-investigation, and strict-social repair tests already listed in the run output. This repair does not claim those failures were resolved.

## Broad regression

Not run.
