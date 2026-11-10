# Ashen Thrones — Storage Cleanup Phase 2A Closeout

Status: **finalized locally.** The approved historical pytest deletions are in one new commit. Nothing was pushed. Phase 2B was not started.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report is untracked. It is not in the size figures below.

## 1. Executive summary

Phase 2A removed 31,886 tracked historical pytest working-store files, 523,570,476 logical bytes, from the worktree and the index. This closeout verified that inventory against the manifest and against commit `c16d922865b7182d47b87d27ec633f9308f1ef4c`, restored one test-generated `session.json` edit, and committed only those deletions.

The controlled regression investigation remains **PASS WITH CAVEATS**. C01–C03 fail the same way on the original commit and on the cleaned tree. T05 passed in both states when given a fresh temporary directory. No cleanup-introduced regression was demonstrated. The regression suite is not described as passing.

The new commit does not rewrite history. The deleted blobs remain recoverable from the parent commit. A smaller working tree does not reduce existing GitHub object storage.

## 2. Finalization status

| Requirement | Result |
| --- | --- |
| Approved deletions committed | 31,886 deletions, no additions, no modifications |
| Logical bytes | 523,570,476 |
| Unrelated changes in the commit | None |
| `session.json` restored after verification | Yes. Worktree only. Not staged |
| Comparison worktree closed | Yes. `git worktree remove` after a clean status |
| Investigation evidence preserved | Yes. External directories were not deleted |
| Application source, tests, protected evidence | Unchanged |
| History rewrite, garbage collection, or push | None |
| Provider calls | None in this finalization |
| Phase 2B | Not started |

## 3. Original baseline commit

`c16d922865b7182d47b87d27ec633f9308f1ef4c`

Branch at verification: `feature/product-realization`. That commit is still the parent of the cleanup commit, and it is still the commit recorded by `origin/feature/product-realization`.

## 4. New cleanup commit SHA

`e86fd4512028af4ce698090d48c1b672dd68600c`

Subject: `chore: remove historical pytest working stores`

The body records the Phase 2A scope, the baseline commit, the file and byte counts, recoverability from history, the pre-existing C01–C03 failures, the T05 before/after pass, and that application source and protected evidence were not changed. The local commit machinery also appended `Co-authored-by: Cursor <cursoragent@cursor.com>`. The commit was not amended.

## 5. Commit parent and branch

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Parent | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Commits since the baseline | 1 |
| Remote-tracking branch | `origin/feature/product-realization` still at the baseline |
| Ahead/behind | Ahead 1. Not pushed |

## 6. Exact committed deletion inventory summary

`git diff --shortstat HEAD^ HEAD` reports `31886 files changed, 10552219 deletions(-)`. That deletion count is lines, not bytes. Name-status is 31,886 `D` entries and nothing else. Every committed path is in `artifacts/storage_cleanup_phase2a_manifest.json`, and every manifest path is in the commit. Each path's Git blob and mode matched the baseline tree before the commit. No committed path is under `game/`, `data/`, `tests/`, `experiments/`, `scripts/`, `tools/`, `docs/`, `handoff/`, `artifacts/atgb/`, `artifacts/pr_eg_r6_r5/`, `artifacts/pr_play`, or `artifacts/pr_eg_r4_r1/replay_state/`.

49 directories:

| Directory | Tracked files | Logical bytes |
| --- | ---: | ---: |
| `artifacts/pr_eg_r4_r1/tmp_baseline` | 2,363 | 37,718,667 |
| `artifacts/pr_eg_r4_r1/tmp_repaired` | 2,363 | 37,366,234 |
| `artifacts/pr_eg_r2c_r2/final_tmp` | 2,327 | 36,571,752 |
| `artifacts/pr_eg_r2c_r1/complete_final_tmp` | 1,967 | 32,946,215 |
| `artifacts/pr_eg_r2c_r2/baseline_tmp` | 1,985 | 32,946,012 |
| `artifacts/pr_eg_r2c_r1/qualification_final_tmp` | 1,985 | 32,945,706 |
| `artifacts/pr_eg_r2c/baseline_local_tmp` | 1,778 | 30,400,549 |
| `artifacts/pr_eg_r2c_r1/final_verified_tmp` | 1,805 | 29,269,081 |
| `artifacts/pr_eg_r2c_r1/final_tmp` | 1,805 | 29,268,025 |
| `artifacts/pr_eg_r2c_r1/post_tmp` | 1,787 | 29,217,453 |
| `artifacts/pr_eg_r2c_r1/baseline_verified_tmp` | 1,787 | 29,149,459 |
| `artifacts/pr_eg_r2c/final_tmp` | 1,787 | 29,149,428 |
| `artifacts/pr_eg_r2c/post_tmp` | 1,778 | 28,660,684 |
| `artifacts/pr_eg_r2c/post_final_tmp` | 1,778 | 28,375,433 |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp` | 393 | 21,144,219 |
| `artifacts/pr_eg_r2c_r1/target_final_tmp` | 450 | 4,375,751 |
| `artifacts/pr_eg_r2c_r1/target_verified_tmp` | 450 | 4,374,637 |
| `artifacts/pr_eg_r4_r1/tmp_focus4` | 306 | 3,791,286 |
| `artifacts/pr_eg_r2c_r1/supplementary_final_tmp` | 162 | 3,677,207 |
| `artifacts/pr_eg_r2c_r1/supplementary_baseline_tmp` | 162 | 3,652,740 |
| `artifacts/pr_eg_r2c_r2/targeted_qualified_tmp` | 342 | 3,563,076 |
| `artifacts/pr_eg_r2/pytest_local` | 261 | 3,454,006 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final5` | 134 | 3,113,147 |
| `artifacts/pr_eg_r2c_r2/targeted_status_tmp` | 324 | 3,018,140 |
| `artifacts/pr_eg_r2c_r1/recall_bypass_tmp` | 161 | 2,595,505 |
| `artifacts/pr_ck_resolver_selection/pytest_basetemp` | 88 | 2,230,424 |
| `artifacts/pr_eg_r2c_r2/targeted_final_tmp` | 297 | 2,198,653 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final4` | 90 | 2,102,257 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final2` | 72 | 1,839,597 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final` | 72 | 1,839,024 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final3` | 82 | 1,838,113 |
| `artifacts/pr_eg_r2c_r1/target_tmp` | 117 | 1,750,913 |
| `artifacts/pr_eg_r2c_r1/owners_verified_tmp` | 99 | 1,716,915 |
| `artifacts/pr_eg_r6_r4_r1/focused_tmp` | 54 | 1,571,806 |
| `artifacts/pr_eg_r2c_r2/targeted_tmp` | 270 | 1,365,009 |
| `artifacts/pr_eg_r4_r1/tmp_other_new` | 17 | 820,994 |
| `artifacts/pr_eg_r2c_r1/owner_tmp` | 36 | 776,084 |
| `artifacts/pr_eg_r4_r1/tmp_targeted3` | 18 | 540,993 |
| `artifacts/pr_eg_r4_r1/tmp_fact6` | 9 | 521,465 |
| `artifacts/pr_eg_r4_r1/tmp_fact5` | 9 | 508,405 |
| `artifacts/pr_eg_r2c/target_tmp` | 9 | 292,885 |
| `artifacts/pr_eg_r2c_r1/focused_tmp` | 9 | 292,885 |
| `artifacts/pr_eg_r4_r1/tmp_targeted` | 18 | 270,801 |
| `artifacts/pr_eg_r4_r1/tmp_targeted2` | 18 | 270,801 |
| `artifacts/pr_eg_r6_r4/test_tmp_workspace` | 18 | 29,058 |
| `artifacts/pr_eg_r6_r4_r1/regression_tmp` | 18 | 16,729 |
| `artifacts/pr_cf_regression_triage/pytest_representative` | 8 | 11,021 |
| `artifacts/pr_eg_r2c/baseline_tmp` | 9 | 10,616 |
| `artifacts/pr_eg_r2c_r1/baseline_tmp` | 9 | 10,616 |
| **Total** | **31,886** | **523,570,476** |

The untracked 14-byte file `artifacts/pr_eg_r6_r4_r1/focused_tmp/test_sensitive_recursive_and_o0/.env` is still on disk. It was not staged and is not in the commit.

## 7. Total logical bytes removed

**523,570,476** logical bytes, summed from the manifest sizes of the committed paths. Those sizes matched the baseline blob identities verified before the commit.

This is a working-tree and future-checkout reduction. `git count-objects -v` still reports size-pack **303,667 KiB** in 35 packs, the same packed size recorded in the Phase 2 audit. The deleted file contents remain in those packs through the parent commit.

The commit introduced 13 new loose objects (the commit and the replacement trees). `.git/objects` is 183 files and 312,105,733 bytes, up 13 files and 33,776 bytes from the Phase 2A figure of 170 files and 312,071,957 bytes. The pre-existing garbage object `.git/objects/92/tmp_obj_xKdgkS` is still present. No garbage collection was run.

## 8. Final repository size

Measured after the commit and after removal of `C:\p2a_c16d922`, and before this closeout report existed. Sums are filesystem file lengths.

| Class | Files | Bytes |
| --- | ---: | ---: |
| Whole project, including `.git` | 97,870 | 3,815,166,999 |
| Tracked worktree files | 43,517 | 2,381,485,785 |
| Root `.git` | 230 | 647,413,860 |
| `.git/objects` | 183 | 312,105,733 |
| `.git/cursor` | 4 | 328,354,559 |
| Worktree excluding `.git` | 97,640 | 3,167,753,139 |

Tracked file count is 75,403 minus 31,886. None of the remaining tracked paths were missing on disk. The index is 6,920,753 bytes.

`.git/cursor` still holds only the crepe index for `c16d922865b7182d47b87d27ec633f9308f1ef4c` (328,354,559 bytes). No second index for the cleanup commit was present at measurement.

### Comparison

| Point | Bytes |
| --- | ---: |
| Original project | 5,919,390,899 |
| After Phase 1 | 4,377,470,981 |
| After Phase 2A deletion, before this commit | 3,807,553,110 |
| This measurement | 3,815,166,999 |

This measurement is **7,613,889 bytes larger** than the post-deletion, pre-commit snapshot. The commit did not put the deleted files back. The difference is elsewhere:

- Worktree excluding `.git`: **+7,802,312** bytes. Files touched after the Phase 2A report are 7,803,129 bytes. Of that, 817 bytes are the previous `session.json`, which the restore replaced. The net addition is 7,802,312. Almost all of it is bytecode written when the regression investigation imported the application at 17:07: `game/__pycache__` 6,279,627 (181 files), `tests/helpers` 1,176,130 (46), `tests/__pycache__` 239,752 (8), plus smaller bytecode under `game/behavioral_evaluators`, `game/importers`, and `experiments/`. Also included are this phase's previously excluded or later reports: `storage_cleanup_phase2a_report.md` (13,805) and `storage_cleanup_phase2a_regression_investigation.md` (26,204), `.pytest_cache` (796), and **+32** bytes on `session.json` because `git restore` wrote CRLF while Git still treats the file as clean. Those bytecode files are ignored. `git status` does not list them, and this closeout did not run the tests again.
- Root `.git`: **−188,423** bytes (647,602,283 down to 647,413,860). Object bytes rose by 33,776. The rest of `.git` shrank by more than that, including the index after the deletion commit and removal of the temporary worktree's admin files. Packed object size did not change.

Phase 1 to this measurement is a working-tree drop dominated by the deleted pytest stores, offset by the investigation bytecode and the untracked manifest. Original to Phase 1 was the earlier cleanup, not this commit.

No Git maintenance command was run. No additional savings were manufactured.

## 9. Verification of protected files

Checked before the commit and again on `HEAD^..HEAD`:

- Application source under `game/`, `tests/`, `tools/`, `scripts/`, `experiments/`, and `docs/` is not in the commit.
- Canonical campaign data under `data/` is not in the commit.
- ATGB baselines under `artifacts/atgb/` are not in the commit.
- `artifacts/pr_eg_r6_r5/` and `artifacts/pr_play` paths are not in the commit.
- Golden replay inputs used by the investigated tests, including `artifacts/pr_eg_r2c_r2/clarification_holdouts.json` and `clarification_freeze.json`, are not in the manifest and are not in the commit.
- `artifacts/pr_eg_r4_r1/replay_state/data/session.json` is not in the commit.
- The six pre-existing audit reports and the manifest were still untracked after the commit. This closeout file was created afterward and was not staged.

`git diff --name-status` against the worktree is empty. No tracked modification remains.

## 10. Regression investigation conclusion

**PASS WITH CAVEATS.**

The investigation compared the original baseline, with the historical pytest directories present, to the post-cleanup tree. It did not edit application code, test expectations, or fixtures. This closeout did not rerun the suite and did not repair conversational continuity.

C01–C03 failed in both states with the same expected and actual lines. T05 passed in both states on a fresh temporary directory. The Phase 2A `PermissionError` was not reproduced. No deleted directory is required by those tests.

The full 193-test selection from Phase 2A was not re-run in the investigation. Phase 2A's own final run was 189 passed, 3 failed, and 1 error. That error was the unreproduced T05 `PermissionError`. Those results are not a clean suite, and this closeout does not treat them as one.

## 11. Outstanding C01–C03 failures

These three tests still fail. They are pre-existing. They call `continuity_directive` and expect the frozen clarification line. The observed line is the absent-NPC sentence, reason `absent_npc_reference`, because the test world has no NPCs and the earlier NPC disclosure is the row the current code keeps.

| Case | Question | Expected line |
| --- | --- | --- |
| C01 | Can you repeat that? | Which sailor do you mean: Fenn or Rook? |
| C02 | What did you mean by that? | Which library do you mean? |
| C03 | Say that again in simpler words. | Which tower are you asking about? |

The holdout and freeze files were not deleted. `game/conversational_continuity.py` was not modified. Repairing this behavior is outside storage cleanup.

## 12. T05 environmental caveat

`test_targeted_reference_matrix` case T05 passed on the baseline and on the cleaned tree when `--basetemp` was a fresh directory outside the repository. The writes stayed in those external directories. The Phase 2A `PermissionError` happened while replacing `session.json` inside a basetemp a previous run had already used. This investigation did not recreate that error. A later run that reuses `development/tmp/phase2a_pytest` or `development/tmp/pytest` can hit a Windows file-lock or basetemp-reuse error again. That is independent of the deleted trees.

## 13. Session.json restoration verification

Before restore, the active file's raw SHA-256 was `14d635e9944fd264ffc72198ca0967591706028ea0ca71aea70ada868566a30d` (817 bytes), matching the investigation. It was not staged. The diff against HEAD changed only:

- `saved_at`: `2026-10-18T16:34:22.613229Z` to `2026-10-31T20:54:32.536508Z`
- `payload.last_saved_at`: the same two timestamps
- `integrity.payload_sha256`: `3c77d68a8a110114b537b457ba23c5437d6a829c95276e80ebe54001d6dd90e0` to `2935611bd3a747e38171a62f4404899e35600945c6b755caf72f0302ba54f131`

`canonicalization` stayed `json/sort_keys,separators`. `hash` stayed `sha256`. With those three fields removed, the document matched HEAD. That shape is what `test_original_failure_frozen_production_finalization` writes, and the investigation reproduced it on the pre-cleanup commit.

Restore command, worktree only:

```text
git restore --worktree -- artifacts/pr_eg_r4_r1/replay_state/data/session.json
```

Afterward, `git diff --name-status` was empty, so Git considers the file identical to HEAD. The on-disk file is 849 bytes because `core.autocrlf` is true and the restore wrote CRLF. Newline-normalized bytes match the HEAD blob. The staged deletion count stayed 31,886. The replay test was not run again in the active tree.

## 14. Temporary worktree removal result

`C:\p2a_c16d922` was a registered detached worktree at `c16d922865b7182d47b87d27ec633f9308f1ef4c`. Its only tracked modification was `artifacts/pr_eg_r4_r1/replay_state/data/session.json`. The diff was the second baseline replay:

- `saved_at` and `payload.last_saved_at`: `2026-10-31T21:09:22.840473Z`
- `integrity.payload_sha256`: `4fc5428b0c7366b575a53de93f7240866062cf33d7888e729eca83f031fde130`

No other tracked or untracked files were present in that worktree. The same document was already stored at `C:\p2a_inv\session_run2.json`. The worktree copy was restored with a path-scoped `git restore --worktree`. Status was then empty. Removal used `git worktree remove C:\p2a_c16d922` with no `--force`. The directory is gone. `git worktree list` shows only the active repository. HEAD stayed `e86fd4512028af4ce698090d48c1b672dd68600c` on `feature/product-realization`. No other worktree was pruned. Garbage collection was not run.

## 15. Preserved external investigation evidence

These paths were confirmed and were not deleted, moved, or added to Git.

| Path | Files | Bytes |
| --- | ---: | ---: |
| `C:\p2a_inv\` | 17 | 50,265 |
| `C:\p2a_pytest_baseline` | 9 | 9,836 |
| `C:\p2a_pytest_postclean` | 9 | 9,836 |
| `C:\p2a_pytest_replay1` | 0 | 0 |
| `C:\p2a_pytest_replay2` | 0 | 0 |

`C:\p2a_inv\` holds the pytest logs, the replay logs, and `session_run1.json` and `session_run2.json`. The two replay directories exist and are empty. They can be removed in a later housekeeping pass after this commit is reviewed. They were not copied into project artifact directories.

## 16. Final Git status

Branch `feature/product-realization`, ahead of `origin/feature/product-realization` by 1 commit. No tracked modifications. No staged changes.

Untracked, and left untracked:

- `artifacts/storage_cleanup_audit.md` (71,109)
- `artifacts/storage_cleanup_phase1_report.md` (8,599)
- `artifacts/storage_cleanup_phase2_audit.md` (58,602)
- `artifacts/storage_cleanup_phase2a_manifest.json` (9,837,334)
- `artifacts/storage_cleanup_phase2a_regression_investigation.md` (26,204)
- `artifacts/storage_cleanup_phase2a_report.md` (13,805)
- `artifacts/storage_cleanup_phase2a_closeout.md` (this file, written after the size measurement)

Ignored investigation bytecode under `game/__pycache__` and `tests/` remains on disk from the earlier test run. It is not staged.

## 17. Restoration instructions

The deleted files are still in the parent commit. To restore the whole set without rewriting history:

```text
git revert e86fd4512028af4ce698090d48c1b672dd68600c
```

To restore individual paths while `c16d922865b7182d47b87d27ec633f9308f1ef4c` remains reachable:

```text
git checkout c16d922865b7182d47b87d27ec633f9308f1ef4c -- <path>
```

The path list is the `path` field of each object in `artifacts/storage_cleanup_phase2a_manifest.json`. Do not use `git reset --hard`. Do not run `git filter-repo` or `git gc` to drop the blobs. A revert or a checkout creates a new commit or worktree state; it does not erase the cleanup commit unless someone later rewrites history on purpose.

## 18. Remaining storage-cleanup candidates

These were not touched.

| Candidate | What it is | Bytes | Notes |
| --- | --- | ---: | --- |
| C1 checkpoint bytecode | Ignored `.pyc` under `development/tmp/github_checkpoint/baseline_4320bcd/` | 35,207,113 | Local disk only. Phase 2 called this the verified-safe deletion |
| C2 ignored local stores | Ignored pytest stores, the rest of the checkpoint checkout, maintenance venv, ignored half of `.venv-broken` | 449,234,232 | Not in Git history. An archive or recorded package list is required first |
| Tracked `.venv-broken` half | Tracked files inside `.venv-broken/` | 24,397,647 | Separate from the pytest stores committed here |
| C3 duplicate ZIP excess | Extra working-tree copies of ZIP bytes | 74,214,968 | Git already stores one shared blob. Current PR-PLAY-12 copies stay protected |
| C4 narrower leftovers | Legacy `venv/`, PR-PLAY-05 overlay, other `development/tmp`, `disposable_state/`, orphan bytecode | 144,053,732 | Not counted as safe to delete yet |
| `.git/cursor` | Local crepe index | 328,354,559 | IDE metadata. Not project content. Not a deletion target |
| External investigation dirs | `C:\p2a_inv` and the four `C:\p2a_pytest_*` directories | about 70,000 | Keep until this commit has been reviewed |

`disposable_state/` (531 files, 20,310,198 bytes) and source-snapshot directories (205 files, 12,834,563 bytes) remain tracked campaign material. They were not part of Phase 2A.

## 19. Recommendation for the next phase

Stop here. Do not push `e86fd4512028af4ce698090d48c1b672dd68600c` until the deletion commit has been reviewed. Do not describe the regression suite as passing. Leave C01–C03 for a separate continuity fix.

The next storage stage, only if a later pass is authorized, is the Phase 2 C1 checkpoint bytecode: 35,207,113 ignored bytes, local disk only, not a history rewrite. After that, ignored C2 stores need an archive before deletion. The external `C:\p2a_*` directories can be removed in a housekeeping pass after review. Do not start those steps as part of this closeout.

Historical pytest files removed by this commit stay recoverable from `c16d922865b7182d47b87d27ec633f9308f1ef4c`. GitHub storage does not shrink by 523,570,476 bytes until history itself is rewritten, which this phase does not do.
