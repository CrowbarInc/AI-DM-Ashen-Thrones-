# Repository baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD subject: fix: restore clarification recency and resolve planner audit false positive
- The working tree was already dirty before this cycle. Unrelated changes were left in place. Nothing was committed or pushed.
- Governance read for this cycle: `docs/DEVELOPMENT_CONSTITUTION.md` and the PR-PLAY-78 entry in `docs/NEXT_SESSION.md`. That entry forbids starting PR-PLAY-79 until this cycle is closed.
- Authored actions live in `experiments/pr_play_70/scene_actions.json` and are applied by `game/authored_consequences.py` only when the branching gate and campaign enrollment allow it.
- Button path remains `POST /api/action` with an exploration action id. Chat now proposes an id and then uses that same executor.
