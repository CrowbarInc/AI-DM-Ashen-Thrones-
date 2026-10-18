# 19 — Source Change Inventory

Cycle-relevant files, against the already dirty worktree:

| Path | Change |
| --- | --- |
| game/expressive_dialogue.py | New host contract, compact prompt, deterministic validator, one provider attempt, continuity reword hook |
| game/immutable_valid_response.py | `adopt_host_speech` applies a validated line before the existing seal |
| game/api.py | Continuity answers may reword through the same seal; expression audit is attached |
| game/conversational_continuity.py | “Other words” with no new subject binds the latest line of the only speaker |
| tests/conftest.py | Pytest disables expression generation |
| tests/helpers/live_model_guard.py | Blocks an unstubbed expression provider call |
| tests/test_pr_eg_r3_expressive_dialogue.py | Mission cases, holdouts, production HTTP seams, name and apostrophe checks |
| tools/validate_pr_eg_r3.py | Frozen 15-turn and 12-turn fresh /api/chat qualification |
| tools/validate_pr_eg_r1.py | `calls_since` counts expression separately from narration |

`game/api.py` and `tests/conftest.py` are modified tracked files. The other listed modules are untracked in this worktree, together with a large pre-existing campaign history. No active campaign data file was edited for this cycle. Disposable live sessions under `artifacts/pr_eg_r3/disposable_state/` are excluded from the review bundle.
