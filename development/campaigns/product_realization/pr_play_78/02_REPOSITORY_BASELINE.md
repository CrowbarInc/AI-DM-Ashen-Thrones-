# Repository baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD message: `fix: restore clarification recency and resolve planner audit false positive`
- Working tree at entry was already dirty with uncommitted PR-PLAY-55 through PR-PLAY-77 work. That work was left in place.
- This cycle did not commit or push.

Integration added in this cycle:

- `game/integrated_play.py` (new). Mixed-domain routing and per-store request ordering. Physical-only sequences still return `None` so `plan_physical` keeps them.
- Bounded social speech and narration checks in `game/expressive_dialogue.py`, gated by `ASHEN_BOUNDED_SPEECH` and `ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION`. Both default off.
- `plan_integrated` is called from the existing `controlled_request` / `resolve_controlled_fact` owners in `game/bounded_improvisation.py`.
- `client_request_id` on the chat model, write/read locking in the chat, action, state, and snapshot routes, and a busy Send button in `static/app.js`.
- Scene-scoped NPC grounding: addressed rows match `scene_id`, world NPCs match `location`.

`git diff --stat` on the already-tracked owners includes earlier uncommitted cycles, so those line counts are not a PR-PLAY-78-only delta. Untracked cycle files include `game/integrated_play.py`, `tests/test_pr_play_78_integrated.py`, `tests/test_pr_play_78_holdout.py`, `tests/test_pr_play_78_http.py`, and `tests/fixtures/pr_play_78_holdout.json`.

Governance read: `docs/DEVELOPMENT_CONSTITUTION.md` and the PR-PLAY-77 entry in `docs/NEXT_SESSION.md`. The prior entry forbade implementing PR-PLAY-78 inside that closure. This user message is the authorization for PR-PLAY-78 only.
