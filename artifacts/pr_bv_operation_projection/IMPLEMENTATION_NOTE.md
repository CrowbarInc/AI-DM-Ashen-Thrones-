# PR-BV implementation note

This cycle edited:

- `game/gm_resolution_decision.py`
- `tests/test_pr_bv_turn_local_operation_projection.py` (new)
- `tests/test_pr_bt_selective_epistemic_guidance.py` (recipe equality now allows the projection and the two aligned guidance fields)

`project_turn_local_operation` begins at line 4419. `build_decision_facing_answer_recipe` embeds `turn_operation` at line 4704. Labels begin at line 4220.

`_decision_from_contract` and `build_gm_resolution_decision` were not edited.

Not edited by this cycle: system prompt, response schema, validator, retry, response policy.

`gm_resolution_decision.py` is untracked in this working tree, so there is no git diff against HEAD for the projection alone. The bundled source file is the current file.
