# PR-DS Implementation Report

Bounded replay of the stored PR-DR interpretations. No new model output was generated. No production chat path was wired to this adapter.

## Phase 0

Git HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

Dirty worktree at start: 404 status lines. Status sha256: `a9e0f25d6dcfc8d99bf5ef7b1982a6cfaf0cc54d1603a834525debcdeb8cc0f0`. Those modifications were left in place.

Production save sha256 values before and after the replay and the regression run:

- `data/session.json` `0a77beb47a2c30deb0b1977e915f3a5e2f67f5560e15a8bf0a5874015e244023`
- `data/world.json` `3592e4af8723e631bb14d4f512431e8697987546f7fdf8076b3fbd1b135a42ef`
- `data/combat.json` `ac977a4ab7d9eae556ba30893d9b09ec075efaf70ba67de0a6d60736eaf685b9`
- `data/session_log.jsonl` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

The replay ran inside `ProductionSaveGuard` and `forbid_provider_calls`. `experiments.pr_dr.runner._call_one` and `openai.OpenAI` were patched to raise if called. Provider hits: 0. `raw_results.json` sha256 stayed `dfa32a80218647a1e68d47384536b6b0550be78025dbe26c38e39278ade18e42`.

## What changed

The experimental connector in `experiments/pr_dr/bind.py` can offer an INSPECT of a visible description to the existing investigate resolver. `experiments/pr_dq/surface_compat.py` holds the eligibility and acceptance checks. `experiments/pr_dq/gameplay.py` accepts that one resolver result when the checks pass. `experiments/pr_dr/turn.py` passes the original player utterance into the connector and records `compatibility` on the turn.

`game/exploration.py` was not edited. The interpretation schema, the model prompt, the PR-DR raw outputs, and the PR-DR expected labels were not edited.

## Replay

`experiments/pr_ds/replay.py` reads the ten stored `parsed` objects from `artifacts/pr_dr_live_vertical_slice/raw_results.json` and applies them in scenario order on a fresh disposable session. Each stored provider text was checked equal to its parsed object before any turn ran. The rebuilt visible-scene prompts matched the stored prompts on all ten rows.

DR01, DR05, DR08, and DR10 executed. The six other rows did not. Disposable reload matched after every row. PR-DR `sequence_complete` stays false because that rule still requires DR01's operation class to be PERCEIVE.
