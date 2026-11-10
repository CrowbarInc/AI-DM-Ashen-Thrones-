# Integrity

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- No commit. No push. No reset. No clean.
- The worktree was already dirty at entry. Preexisting dirty files were left in place.
- During a parallel pytest and replay, `data/scenes/frontier_gate.json` lost its interactables. It was restored with `git checkout HEAD -- data/scenes/frontier_gate.json`. After the restore, `git status` shows that file clean, and `notice_board` is present. The solo replay and the 28/28 holdout ran after that restore.
- `data/scenes/mill_loft.json` appeared as untracked test debris when isolation did not hold. It was deleted. It was not campaign content.
- Production files touched by this cycle: `game/conversational_continuity.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/intent_parser.py`.
- New test: `tests/test_pr_play_post_npc_handoff.py`.
- `git diff HEAD -- game/conversational_orchestration.py` includes preexisting uncommitted work. HEAD of that file does not contain `authored_travel_admission`.
- Protected evidence: 150 files unchanged. Frozen holdout digest file was not rewritten. Result: `artifacts/pr_play_post_npc/holdout_rerun.json`.
- Live provider calls: 0. No new campaign was opened. No provider configuration or budget was changed.
- A discarded parallel replay wrote an earlier `corrected_trace.json` while the scene file was damaged. The file now on disk is the solo rerun.
