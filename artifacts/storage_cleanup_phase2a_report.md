# Ashen Thrones — Storage Cleanup Phase 2A

Status: **STOPPED.** The approved tracked files were removed from the worktree and staged. Required regression validation did not pass. **No cleanup commit was created. Nothing was pushed.**

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

## 1. Original branch and HEAD

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Baseline commit locally available | Yes (`git cat-file -t` returned `commit`) |
| Tracked source, configuration, and tests at start | Clean. The only untracked files were the three storage-audit reports. |

HEAD and branch were unchanged at the stop. They are still `feature/product-realization` and `c16d922865b7182d47b87d27ec633f9308f1ef4c`.

## 2. New commit SHA

Not created. Validation failed, and the required test also left one unrelated tracked file modified. The staged deletion was preserved for inspection.

## 3. Original project size

Measured immediately before deletion. Logical file lengths. The figure includes the three pre-existing audit reports and the ignored preflight scratch under `development/tmp/phase2a_preflight/`. It matches the Phase 2 tracked totals.

| Class | Files | Bytes |
| --- | ---: | ---: |
| Whole project, including `.git` | 129,023 | 4,388,074,558 |
| Tracked worktree files | 75,403 | 2,905,056,229 |
| Root `.git` | 220 | 732,207,649 |
| Worktree excluding `.git` | — | 3,655,866,909 |

Phase 2 had reported a project total of 4,377,487,757 bytes while excluding its own report. Tracked file count and tracked bytes are the same numbers Phase 2 recorded. `.git` object bytes were 312,071,957.

## 4. Final project size

Measured after the staged deletion and the validation runs, and after copying the manifest into `artifacts/`. This report is not included.

| Class | Files | Bytes |
| --- | ---: | ---: |
| Whole project, including `.git` | 97,610 | 3,807,553,110 |
| Root `.git` | 217 | 647,602,283 |
| Worktree excluding `.git` | — | 3,159,950,827 |

`.git/objects` is unchanged: 170 files, 312,071,957 bytes. No pack was rewritten and no object was deleted.

The worktree shrink is smaller than the tracked-byte removal because validation scratch was added under ignored `development/tmp/` and the untracked manifest was copied into `artifacts/`. See unexpected findings for the `.git/cursor` change.

## 5. Tracked files removed

**31,886** files removed from the worktree and staged as deletions.

`git diff --cached --shortstat` reports `31886 files changed, 10552219 deletions(-)`. That deletion count is lines, not bytes.

## 6. Total logical bytes removed

**523,570,476** logical bytes of tracked files. This matches the Phase 2 scope. It is a working-tree reduction. Existing Git history still contains the blobs. No GitHub storage reduction is claimed.

## 7. Exact deletion scope

49 directories. Appendix A rows with `tracked_bytes` > 0, plus the four explicitly approved directories. Ignored rows and `tracked_bytes` = 0 rows were not included. One untracked 14-byte file inside an approved directory was not deleted.

| Directory | Tracked files | Tracked bytes |
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
| `artifacts/pr_eg_r2c_r1/target_final_tmp` | 450 | 4,375,751 |
| `artifacts/pr_eg_r2c_r1/target_verified_tmp` | 450 | 4,374,637 |
| `artifacts/pr_eg_r4_r1/tmp_focus4` | 306 | 3,791,286 |
| `artifacts/pr_eg_r2c_r1/supplementary_final_tmp` | 162 | 3,677,207 |
| `artifacts/pr_eg_r2c_r1/supplementary_baseline_tmp` | 162 | 3,652,740 |
| `artifacts/pr_eg_r2c_r2/targeted_qualified_tmp` | 342 | 3,563,076 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final5` | 134 | 3,113,147 |
| `artifacts/pr_eg_r2c_r2/targeted_status_tmp` | 324 | 3,018,140 |
| `artifacts/pr_eg_r2c_r1/recall_bypass_tmp` | 161 | 2,595,505 |
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
| `artifacts/pr_eg_r2c/baseline_tmp` | 9 | 10,616 |
| `artifacts/pr_eg_r2c_r1/baseline_tmp` | 9 | 10,616 |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp` | 393 | 21,144,219 |
| `artifacts/pr_ck_resolver_selection/pytest_basetemp` | 88 | 2,230,424 |
| `artifacts/pr_eg_r2/pytest_local` | 261 | 3,454,006 |
| `artifacts/pr_cf_regression_triage/pytest_representative` | 8 | 11,021 |
| **Total** | **31,886** | **523,570,476** |

Before deletion, each directory's on-disk file count and byte total matched Appendix A, including `focused_tmp` at 55 files / 1,571,820 bytes of which 54 files / 1,571,806 bytes were tracked. Each tracked file was a regular file, index tag `H`, stage 0, mode `100644` or `100755`, and its index blob matched the baseline tree. All 8,915 distinct blobs were present locally. No selected path was a symlink or a reparse point, and none resolved outside the repository.

No selected path is under `game/`, `data/`, `tests/`, `experiments/`, `scripts/`, `tools/`, `docs/`, `handoff/`, `artifacts/atgb/`, `artifacts/pr_eg_r6_r5/`, a virtual environment, or `disposable_state/`.

Deletion command: `git rm --pathspec-from-file` with NUL-separated exact file paths. No `git clean`, `git reset --hard`, `git filter-repo`, or recursive delete of `artifacts/`, `development/`, `handoff/`, `tests/`, `data/`, or `experiments/`.

## 8. Preservation verification

Checked immediately after `git rm`, before tests:

- Staged diff: 31,886 deletions, every path in the allowlist, no additions or modifications.
- Unstaged tracked diff: empty.
- Untracked files: only the three audit reports.
- Preserved inside the scope: `artifacts/pr_eg_r6_r4_r1/focused_tmp/test_sensitive_recursive_and_o0/.env` (14 bytes, untracked). It is still present.

After the required tests, one additional unstaged modification appeared:

`artifacts/pr_eg_r4_r1/replay_state/data/session.json`

`tools.qualify_pr_eg_r4_r1.replay()`, called by `test_original_failure_frozen_production_finalization`, seeds `artifacts/pr_eg_r4_r1/replay_state`. The diff is the session timestamps and the payload integrity hash that covers `last_saved_at`. It was not restored.

No reader of these stores was found in `tests/`, `game/`, `experiments/`, `scripts/`, `tools/`, `.github/`, `data/`, `artifacts/atgb/`, or `artifacts/pr_play_12/`. Historical review packagers under `artifacts/pr_eg_r2/` exclude `pytest_local` by name. They were not modified.

## 9. Regression validation results

Provider calls were disabled with `ASHEN_DISABLE_PROVIDER_CALLS=1`, `ASHEN_DISABLE_LIVE_INTERPRETATION=1`, `ASHEN_DISABLE_EXPRESSION_GENERATION=1`, `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`, and `ASHEN_PROVIDER_REQUEST_LIMIT=0`. Pytest's existing live-model guard was also active. Baselines and fixed PR-PLAY outputs were not regenerated on purpose. Test output used `development/tmp/phase2a_pytest`. `artifacts/pr_eg_r5/verify_bundle.py` and `artifacts/pr_eg_r5/build_reports.py` were not run.

Import check: `import game.api` printed `IMPORT_OK`.

Tests:

- `tests/test_pr_eg_r2c_speech_adoption.py`
- `tests/test_pr_eg_r2c_r2_reference_eligibility.py`
- `tests/test_pr_eg_r4_r1_delivery_integrity.py`
- `tests/test_golden_replay_artifact_manifest.py`
- `tests/test_atgb_readiness.py::test_incompatible_baseline_refused_before_store_creation`

Collected 193. Final run: **189 passed, 3 failed, 1 error, 0 skipped.**

Failed:

- `test_independent_clarification_holdout[C01]`
- `test_independent_clarification_holdout[C02]`
- `test_independent_clarification_holdout[C03]`

Error:

- `test_targeted_reference_matrix[T05-...]` — `PermissionError` replacing `session.json` inside the isolated basetemp. The first run had already used that directory. This is not a missing deleted store.

Likely cause of the three failures: they call `continuity_directive` on questions such as "Can you repeat that?" and expect the frozen clarification line. Current `game/conversational_continuity.py` returns `_absent_line` instead, because the test world has no NPCs and an earlier NPC disclosure is on the session. The fixtures are `artifacts/pr_eg_r2c_r2/clarification_holdouts.json` and `clarification_freeze.json`, which were not in the deletion scope. `game/` was not modified. These failures are not explained by the removed pytest stores.

The first run had also blocked loopback sockets, which broke Starlette's local `socketpair`. That run is not the result above. The final run allows only `127.0.0.1`, `::1`, and `localhost`, and still blocks other connects.

## 10. Git working-tree status

Branch and HEAD unchanged.

Staged: the 31,886 approved deletions only.

Unstaged tracked modification: `artifacts/pr_eg_r4_r1/replay_state/data/session.json`.

Untracked, not staged:

- `artifacts/storage_cleanup_audit.md`
- `artifacts/storage_cleanup_phase1_report.md`
- `artifacts/storage_cleanup_phase2_audit.md`
- `artifacts/storage_cleanup_phase2a_manifest.json`
- `artifacts/storage_cleanup_phase2a_report.md`

No commit. No push. No history rewrite.

## 11. Historical verification caveats

`artifacts/pr_eg_r5/baseline.json` and the related `protected()` walk include hashes for temporary files under `artifacts/pr_eg_r4_r1/tmp_*`. Those scripts and that baseline were not modified and were not executed. Phase 2 already found that a fresh walk disagrees with current `game/`, `data/`, and `tests/`. Removing the tmp trees would add those paths to a check that is already stale and is not part of `tests/`.

The deleted bytes remain in commit `c16d922865b7182d47b87d27ec633f9308f1ef4c`.

## 12. Restoration instructions

The deletion commit does not exist. HEAD still points at the baseline. To put the staged files back:

```text
git restore --source=c16d922865b7182d47b87d27ec633f9308f1ef4c --staged --worktree --pathspec-from-file=<allowlist> --pathspec-file-nul
```

The allowlist is the `path` field of each object in `artifacts/storage_cleanup_phase2a_manifest.json`. Do not use `git reset --hard`; that would also discard the unrelated `session.json` edit and any other local work.

If a deletion commit is created later, restore with:

```text
git checkout c16d922865b7182d47b87d27ec633f9308f1ef4c -- <path>
```

while that commit remains reachable, or `git revert` that later commit. This cleanup did not rewrite history, so the blobs are still in the local object store.

## 13. Unexpected findings

- Validation failed for the reason in section 9. The cleanup commit was not created.
- `replay()` wrote new timestamps into `artifacts/pr_eg_r4_r1/replay_state/data/session.json`. Left in place.
- `.git/cursor` no longer contains the previous commit's crepe index (`bc7fa3b8568e42f853434d8b1a4067b19289760f`, 79,357,970 bytes in the Phase 2 audit). The current HEAD index is still there at 328,354,559 bytes. This was not a `git rm` of project files and was not a manual edit of `.git`. Object count and object bytes are unchanged. The index file itself shrank because the staged deletions removed 31,886 entries.
- A first socket block was too broad and rejected the loopback pair Starlette uses for `TestClient`. It was corrected before the run reported in section 9. No external host was contacted.

## Machine-readable deletion manifest

`artifacts/storage_cleanup_phase2a_manifest.json`

Each record has `path`, `size`, `blob`, `mode`, `directory`, and `sha256`. The file also lists the one preserved untracked path inside the scope. It is not staged.

## What was not done

No commit. No push. No history rewrite. No `.gitignore` edit. No virtual-environment cleanup. No Phase 2B. No other Category C candidate was removed.
