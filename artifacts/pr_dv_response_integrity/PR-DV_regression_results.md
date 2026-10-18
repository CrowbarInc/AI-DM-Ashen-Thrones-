PR-DV Regression Results

Focused:
- `python -m pytest tests/test_pr_du_player_pipeline.py -q --basetemp=codex_pytest_tmp_prdv_focus`
- Result: 5 passed.

Inherited PR-DQ/DR/DS/DU:
- `python -m pytest tests/test_pr_dq_vertical_slice.py tests/test_pr_dq_ic_ooc_messages.py tests/test_pr_dr_live_vertical_slice.py tests/test_pr_ds_operation_compatibility.py tests/test_pr_du_player_pipeline.py -q --basetemp=codex_pytest_tmp_prdv_inherited2`
- Result: 47 passed.

Relevant broader batch:
- `python -m pytest tests/test_turn_pipeline_shared.py tests/test_exploration_resolution.py tests/test_exploration_skill_checks.py tests/test_realization_authority.py tests/test_scene_transition_authority.py tests/test_narrative_authority_rules.py tests/test_bounded_improvisation_authority.py tests/test_conversational_memory_window.py -q --basetemp=codex_pytest_tmp_prdv_relevant`
- Result: failed with 28 failures.
- Assessment: inherited/out-of-scope failures in broad shared HTTP/social/parser expectations; no focused PR-DV regression identified.

Environment/coverage limitation:
- `tests/test_pr_dt_authoritative_narration.py` is not present in this checkout.
- HTTP transport was not claimed as browser-level verified.
