# PR-DS Regression Results

No unrelated defect was repaired. Every command set `ASHEN_DISABLE_LIVE_INTERPRETATION=1` through the PR-DR suite runner. No suite timed out.

| Suite | Timeout | Timed out | Return code | Summary |
| --- | --- | --- | --- | --- |
| PR-DS | 180s | no | 0 | 7 passed |
| PR-DR | 180s | no | 0 | 12 passed |
| PR-DQ | 180s | no | 0 | 23 passed |
| PR-DO | 120s | no | 0 | 12 passed |
| Exploration | 300s | no | 1 | 57 passed, 9 failed |
| Authority | 180s | no | 0 | 9 passed |
| Conversation | 180s | no | 0 | 34 passed |
| Turn pipeline | 300s | no | 1 | 41 passed, 24 failed |

Commands:

- `python -m pytest tests/test_pr_ds_operation_compatibility.py -q --tb=line`
- `python -m pytest tests/test_pr_dr_live_vertical_slice.py -q --tb=line`
- `python -m pytest tests/test_pr_dq_ic_ooc_messages.py tests/test_pr_dq_vertical_slice.py -q --tb=line`
- `python -m pytest tests/test_pr_do_authority_separation.py -q --tb=line`
- `python -m pytest tests/test_exploration_resolution.py tests/test_exploration_skill_checks.py tests/test_referenced_surface_grounding_inspection_resolution.py -q --tb=line`
- `python -m pytest tests/test_pr_cx_authority_assurance.py -q --tb=line`
- `python -m pytest tests/test_conversational_memory_window.py -q --tb=line`
- `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line`

## Turn pipeline

The 24 failures are the same 24 names recorded in `artifacts/pr_dr_live_vertical_slice/PR-DR_regression_results.md`. New turn-pipeline failures: 0. Inherited: 24.

## Exploration

PR-DR did not record this suite. This run failed 9 tests:

- `test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `test_chat_observe_area_resolution_kwarg_to_build_messages`
- `test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `test_chat_exploration_parsed_routes_through_exploration`
- `test_general_abstract_reference_does_not_become_physical`
- `test_general_readable_surface_communicates_contents`
- `test_general_hidden_object_is_not_revealed_by_naming`
- `test_general_failed_inspection_creates_no_world_facts`
- `test_frontier_gate_roster_http_does_not_use_observe_stock`

Those modules do not import `experiments.pr_dq` or `experiments.pr_dr`. `game/` does not import the new compatibility module. The failures are on the production chat path, which this change does not call. They were left as found. Focused adapter suites that do import the change passed: PR-DS 7, PR-DR 12, PR-DQ 23, PR-DO 12.
