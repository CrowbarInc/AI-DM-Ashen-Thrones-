# Baseline reconstruction

## Why HEAD was not executed

`game/conversational_orchestration.py` at HEAD does not define `authored_travel_admission`. The previous cycle checked that file out, pytest could not collect, and the in-progress backup restored the already-edited file. That backup is the post-edit text. No saved copy of the dirty pre-edit orchestration file exists.

This audit did not check out, reset, stash, or replace any worktree file.

## Historical execution evidence

`artifacts/pr_play_post_npc/adjacent_focus_junit.xml` is the previous cycle's 176-test run: 12 failures, the same test names. That file was recorded after the handoff edit. It is not a pre-edit baseline.

`artifacts/pr_play_post_npc/REGRESSION_RESULTS.md` says a pre-edit rerun was not obtained. Earlier PR-PLAY-47 and PR-PLAY-49 XML files mention some of these names, including a fixture-path error for the patrol-travel test. Those runs predate the dirty player-projection and travel code. They are not a baseline for the current worktree.

AT-OPT-02, AT-OPT-04, and AT-OPT-06 report 118 adjacent authority and publication tests passing. That selection is not these 12 HTTP assertions. The three known `provider_context_projection`, `gm_only`, and `social_context` KeyErrors were not in this 176-test selection and were not rerun.

## Source comparison

The handoff edit is the uncommitted diff of three files plus specific insertions in orchestration.

`git diff HEAD` for `game/conversational_continuity.py`, `game/intent_parser.py`, and `game/referenced_surface.py` contains only the hunks in `artifacts/pr_play_post_npc/implementation.diff`. For those three files, HEAD is the pre-handoff text.

`git diff HEAD` for `game/conversational_orchestration.py` also contains older uncommitted work, including `authored_travel_admission`. Reverting that whole file to HEAD is not a coherent pre-handoff package.

`game/player_http_projection.py` is untracked and was not one of the four files the handoff cycle edited. `game/api.py` was already dirty. Both the current tree and the comparison package use those same files. `project_player_response` sets `resolution` to `{}` whenever the key is present.

## Isolated package

A copy of the current `game` package was built outside the repository. Bytecode was not copied. A junction points that copy's `static` directory at the repository `static` directory so the application can import. The repository was not modified.

In that copy:

- continuity, the intent parser, and referenced-surface classification were replaced with `git show HEAD`;
- orchestration kept the current file, including `authored_travel_admission`, and the handoff insertions were removed.

The removed symbols are absent from the copy: `_local_presence_decision`, `_grounded_object_question`, `_unbound_physical_decline`, `established_scene_object_ids`, `local_object_not_a_destination`, `unsupported_physical_manipulation`, and `ambiguous_scene_object`.

The capture script imported that package first and the repository tests second. Storage was redirected before import. OpenAI construction was blocked. Provider, interpretation, and expression calls were disabled.

## Comparison result

`artifacts/pr_play_adjacent_regression/current_capture.json` and `historical_capture.json` have equal turn records and equal decision probes for all twelve cases. For the mill and notice utterances in those tests, `deterministic_conversational_decision` is `None` on both packages.

A separate twelve-style probe on the overlay still shows the pre-handoff T04 sentence: the notice board is "not an established destination". The current tree says the board is here and the player has not moved. That difference shows the overlay actually removed the local-contact repair. It is not a claim that the overlay reproduces every line of `baseline_trace.json`. In the short probe, the overlay's T04 refusal is a different previous publication from the original twelve-turn trace, so its T05 line is the disabled-narration sentence rather than the captain replay. The HTTP identity for the twelve assertions does not depend on that trace.

## Why the classification is defensible

Each assertion fails on the current tree. The same public sentence, the same empty resolution, and the same engine kind fail on source that does not contain the handoff symbols. The handoff's new decisions return `None` for these utterances, so they are not the owner of these publications.

The remaining limit is that the orchestration text was reconstructed by removing the documented handoff insertions, not by replaying a saved pre-edit file. The identical captures are the evidence that this reconstruction does not change these twelve outcomes. A missed handoff line that these utterances never execute would not change that result.

## Lightweight procedure for the next edit

Before the next production edit, in this same environment:

1. Record `git status --short` and the hashes of the files that will change.
2. Copy those files to a directory outside the repository. Do not `git checkout` a dirty file.
3. Run the exact pytest node ids and write `--junitxml` outside the repository.
4. After the edit, rerun those node ids in one process.
5. Compare the two junit files and the copied sources.

That is enough to separate a new failure from the dirty baseline. It does not need a new test framework. Do not treat HEAD as the baseline while uncommitted modules import one another.
