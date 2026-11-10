# Ashen Thrones — Storage Cleanup Phase 2B-C2

Status: **complete.** The audited ignored pytest working stores were archived outside the repository, the archive was recovered and checked, and only those files were deleted. No Git commit was created. Nothing was pushed.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report and `artifacts/storage_cleanup_phase2b_c2_manifest.json` are untracked. The manifest was written before deletion and is included in both deletion measurements below. This report was written after the post-deletion measurement, so its bytes are not part of those totals.

## 1. Executive summary

Status: **COMPLETE**.

Deletion occurred. The external archive passed recovery verification: every archived file was extracted and matched the manifest path, length, and SHA-256. **5,105** files were then removed, **105,879,032** logical bytes.

No other file was deleted or resized. `HEAD` is still the Phase 2A commit. Phase 2B-C1 was not reversed. No provider call was made, and the game, the AI-DM, and the test suite were not run.

These files were ignored and were never Git objects. Removing them does not reduce GitHub repository storage.

## 2. Repository state

Confirmed before any file in the candidate set was changed.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote tracking ref | `origin/feature/product-realization` |
| Remote tracking SHA | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Merge, rebase, cherry-pick, or bisect | None in progress |
| Staged changes | None |
| Unstaged tracked changes | None |

Untracked files present at the start were the earlier storage-cleanup reports and manifests. They are outside the candidate directories. They were left untracked.

Logical repository size at that point, before this phase's manifest existed: **96,809** files, **3,780,450,524** bytes. The method is the sum of regular-file lengths in the whole project, including `.git`, without following reparse points. That walk found no reparse points.

Available free space on `C:` immediately before the archive was created: **421,671,170,048** bytes.

The same checks were repeated immediately after deletion. Branch, `HEAD`, and the remote-tracking SHA were unchanged. `git diff` and `git diff --cached` were empty. No commit was created. No push was run, and the remote-tracking ref was not updated by a fetch.

## 3. Source inventory

The Phase 2 audit's step 3 candidate is the ignored `test_*` stores whose audited size is **105,879,032** bytes. That figure is the sum of two tables, and the sum was recalculated before anything was deleted:

- Appendix A rows that are ignored and whose children are `test_*` stores. `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` is C4 in that table and was not included. The empty `artifacts/prak_pytest_tmp` and `artifacts/prao_pytest_tmp` rows contribute nothing.
- Appendix B, the three ignored `pytest_reg` roots.

| Approved root | Files | Logical bytes |
| --- | ---: | ---: |
| `artifacts/pr_eg_r4/pytest_tmp` | 2,363 | 37,718,668 |
| `artifacts/pram_pytest_tmp` | 330 | 7,885,288 |
| `artifacts/prar_pytest_tmp` | 218 | 4,831,626 |
| `artifacts/pral_pytest_tmp` | 110 | 2,868,262 |
| `artifacts/pran_pytest_tmp` | 110 | 2,848,726 |
| `artifacts/prap_pytest_tmp` | 90 | 2,708,935 |
| `artifacts/praq_pytest_tmp` | 89 | 2,083,255 |
| `artifacts/pr_eg_r5/pytest_tmp` | 81 | 1,879,397 |
| `artifacts/prar_pytest_tmp2` | 66 | 1,304,467 |
| `artifacts/pr_eg_r2/pytest_tmp` | 27 | 612,649 |
| `artifacts/prar_pytest_reg1` | 1,117 | 27,617,175 |
| `artifacts/praq_pytest_reg2` | 503 | 13,519,683 |
| `artifacts/prar_pytest_reg2` | 1 | 901 |
| **Total** | **5,105** | **105,879,032** |

Expected audited bytes: **105,879,032**. Actual bytes: **105,879,032**. File count: **5,105**. Approved directory count: **13** roots. Those roots contained **1,727** directories, including the roots themselves.

Every approved file was a regular file. Every path resolved inside its approved root. No symlink, junction, or other reparse point was found on a candidate path or on a parent component. `git ls-files` returned nothing under the 13 roots. `git check-ignore` ignored every file. Every file lived under a top-level child whose name starts with `test_`.

No file was added to the set to make the total match. No audited file was missing.

## 4. Archive details

| Item | Value |
| --- | --- |
| Destination | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` |
| Filename | `ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` |
| Compressed size | 19,722,751 bytes |
| SHA-256 | `7df6f3a68feba8e3130de20ae98505601290327ffcac532a4a72d21a5ffd7740` |
| Entry count | 5,105 |
| Inside the repository | No |
| Physically independent storage | No |

The destination is a sibling of the repository on drive `C:`. It is writable, it is not inside the work tree, and `git status` does not list it. The archive was written to a `.partial` name and renamed only after the checks below passed. No earlier file used this name.

The archive uses standard ZIP deflate. Entry names are the repository-relative paths with forward slashes. There are no absolute paths and no `..` components. Symbolic links were not followed.

Verification before deletion:

1. The archive opened and `testzip` reported no bad entry.
2. Entry count was 5,105, equal to the manifest, with no duplicate names and no extra names.
3. Every entry's uncompressed length matched the manifest.
4. Every entry's SHA-256 matched the manifest.
5. The archive was extracted to a temporary directory outside the repository. The extracted path set, file count (5,105), logical byte total (105,879,032), and SHA-256 of every file matched the manifest.
6. The temporary extraction directory was removed. The archive was kept.
7. After the rename, the published archive opened again, `testzip` passed, and the entry count was still 5,105. After deletion, the same archive was still readable and its SHA-256 was unchanged.

This archive is a recovery copy against accidental cleanup of the working tree. It is on the same physical disk as the repository. It is not an independent backup. A failure of that disk would lose the archive and the repository together.

Rollback of these files is unzip of this archive onto the original repository-relative paths.

## 5. Deletion manifest

`artifacts/storage_cleanup_phase2b_c2_manifest.json`

Written at `2026-10-31T17:56:22-04:00`, before the archive and before any deletion. 2,230,864 bytes. It is untracked and not ignored.

It records the operation, the timestamp, the branch, `HEAD`, the remote-tracking SHA, the audit reference, the expected and actual byte totals, the file count, the 13 approved roots, the archive destination, and one record per file. Each record has the repository-relative path, logical size, SHA-256, modification timestamp, ignored status, tracked status, and the classification `C2 ignored pytest test_* working store`. Records are sorted by path.

After the write, the file was read back. The file count, byte total, and archive path matched. There were no duplicate paths. The records were sorted. Every required field was present, with ignored true and tracked false. Every SHA-256 and length was recalculated from disk and matched the record. No file was archived or deleted until that check passed.

## 6. Exact deletion results

| Result | Count |
| --- | ---: |
| Files removed | 5,105 |
| Manifest files still present | 0 |
| Unexpected deletions | 0 |
| Partial failures | 0 |

Removal used `os.remove` on the exact manifest paths, in manifest order. Immediately before each removal, the path was checked again as a regular file and its size, modification time, and SHA-256 were compared with the manifest. None had changed.

Immediately before that loop, `git ls-files` still showed nothing under the 13 roots and `git check-ignore` still ignored every path. An exclusive read opened and closed every file, so none was locked by another process. No process command line named an approved store path.

`git clean` was not used. Directories were not removed. No wildcard delete was used. The 13 roots remain, with **0** files and **1,727** directories.

## 7. Storage measurements

Logical lengths, same walk both times, including `.git`. The manifest exists in both measurements. This report does not.

| Point | Files | Logical bytes |
| --- | ---: | ---: |
| Before this phase's manifest | 96,809 | 3,780,450,524 |
| Immediately before deletion | 96,810 | 3,782,681,388 |
| Immediately after deletion | 91,705 | 3,676,802,356 |

| Quantity | Bytes |
| --- | ---: |
| Files deleted | 5,105 |
| Logical bytes removed | 105,879,032 |
| Archive compressed size | 19,722,751 |
| Net logical reduction inside the repository | 105,879,032 |
| Net logical reduction on the shared disk | 86,156,281 |

The repository total fell by the same 105,879,032 bytes as the deleted file lengths. The before-and-after path inventory differed only by those 5,105 paths. No other file was added, removed, or resized, and no other modification timestamp changed, during that interval.

The manifest's 2,230,864 bytes are in both deletion measurements, so they are not part of the 105,879,032. Compared with the pre-manifest measurement, the repository is smaller by 103,648,168 bytes, which is the deleted content minus the manifest that remains.

The archive is on the same disk. Net logical content recovered on that disk is 105,879,032 − 19,722,751 = **86,156,281** bytes, not 105,879,032. Empty directories remain and are not file content. GitHub storage is unchanged. No garbage collection and no history rewrite was run.

## 8. Preservation verification

The post-deletion inventory is the check. The only paths removed were the manifest paths. The paths below were also confirmed present after deletion.

| Check | Result |
| --- | --- |
| Approved manifest files absent | 5,105 of 5,105 |
| Unapproved files removed or resized | 0 |
| Live `game/api.py`, `data/session.json`, `tests/`, `tools/`, `scripts/`, `experiments/` | Present |
| `artifacts/atgb/` | Present |
| `artifacts/pr_eg_r6_r5/snapshots/` | Present |
| `handoff/CURRENT_REVIEW.zip` | Present |
| Checkpoint `development/tmp/github_checkpoint/baseline_4320bcd/game/api.py` | Present |
| `development/tmp/storage_cleanup_phase1_control/` | Present |
| Phase 2 audit, Phase 2A manifest, Phase 2B-C1 manifest and report | Present |
| `.venv/pyvenv.cfg`, `.venv-broken/`, `venv/` | Present |
| C4 `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` | Still 10 files, 18,195 bytes |
| Empty `artifacts/prak_pytest_tmp` and `artifacts/prao_pytest_tmp` | Still present, 0 files |
| Tracked files | No tracked modification, deletion, or staging |
| `HEAD` and remote-tracking SHA | Unchanged |
| External archive | Present, readable, same SHA-256 |

Phase 2B-C1's closing measurement was 96,808 files and 3,780,436,350 bytes, taken before its report existed. This phase's pre-manifest measurement was one file and 14,174 bytes larger. That file is `artifacts/storage_cleanup_phase2b_c1_report.md`, which is 14,174 bytes. The 1,064 bytecode files removed in Phase 2B-C1 were not restored.

## 9. Unexpected findings

The file counts and byte totals of all 13 roots matched the audit, so the deletion set was not widened or narrowed.

`artifacts/pr_eg_r4/pytest_tmp` has 297 child directories, matching the audit's 297/297 `test_*` children. Twenty-six of those directories were already empty, so 271 children held the 2,363 files. `artifacts/pr_eg_r5/pytest_tmp` has 10 child directories, matching 10/10, and one of them was already empty. Empty directories have no logical bytes. They were not deleted.

`artifacts/pr_cj_turn_pipeline_reconciliation/pytest_regression` is an empty directory ignored by `artifacts/**/pytest_reg*/`. It is not in Appendix A or Appendix B and it is not part of the 105,879,032 bytes. It was left in place.

A first process scan treated every Python process, and any command line containing the search text itself, as a hit. That scan matched this operation's own PowerShell command and two short-lived Python processes that did not name the stores. It stopped the script before any archive existed. The scan used for the deletion gate matches only the thirteen approved repository paths, and every candidate file also had to open for an exclusive read. That gate passed.

## 10. Remaining cleanup candidates

Not touched in this pass.

| Candidate | What it is | Bytes | Notes |
| --- | ---: | --- | --- |
| Checkpoint remainder | `baseline_4320bcd/` after the Phase 2B-C1 bytecode removal, including the 67 extra non-bytecode paths | 250,088,273 | Audit step 4. Commit `4320bcd` remains the restore source for the committed paths. Sibling diagnostics stay |
| Maintenance venv and ignored `.venv-broken` | Local environments | 63,307,128 + 29,959,799 | Appendix C is the package record. Active `.venv` stays |
| Tracked `.venv-broken` | Files still in the index | 24,397,647 | Separate ordinary commit |
| C3 duplicate ZIP excess | Extra working-tree copies | 66,621,016 outside the current PR-PLAY-12 trio | Current review copies stay |
| C4 leftovers | `venv/`, PR-PLAY overlays, other `development/tmp`, `disposable_state/`, 66 orphan bytecode files, and the 18,195-byte isolation directory | 144,053,732 | Not classified as safe to delete |
| `.git/cursor` | Local IDE index | Left as recorded in Phase 2A | Not a deletion target |

The empty directory trees under the 13 pytest roots remain. They are not file content. `artifacts/pr_cj_turn_pipeline_reconciliation/pytest_regression` remains and was not an audited file store.

## 11. Recommendation

Phase 2B-C2 can be closed. The approved files are gone from the work tree, their bytes match the audit, and the external archive restored every file with the manifest hash before those files were deleted.

The next storage candidate, only if a later pass is authorized, is audit step 4: the checkpoint checkout `development/tmp/github_checkpoint/baseline_4320bcd/` after the bytecode removal, 250,088,273 bytes. That pass has to keep the sibling diagnostics, and it needs its own archive if the exact CRLF checkout must be recoverable. It is not a Git commit, and it is not authorized by this report.

Phase 2A remains the pushed deletion of tracked pytest working stores. Phase 2B-C1 remains the local deletion of ignored checkpoint bytecode. Phase 2B-C2 is the local archive-and-delete of the ignored pytest stores. The three are separate operations.
