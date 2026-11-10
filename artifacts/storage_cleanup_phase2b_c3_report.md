# Ashen Thrones — Storage Cleanup Phase 2B-C3

Status: **PASS WITH CAVEATS**. The historical checkpoint was archived outside the repository, the archive was recovered and checked against the working-tree bytes, and only the manifest files were deleted. No Git commit was created. Nothing was pushed.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report and `artifacts/storage_cleanup_phase2b_c3_manifest.json` are untracked. The manifest was written before deletion and is included in both deletion measurements below. This report was written after the post-deletion measurement, so its bytes are not part of those totals.

## 1. Executive Summary

Status: **PASS WITH CAVEATS**.

Deletion occurred. The external archive passed recovery verification: every archived file was extracted and matched the manifest path, length, and SHA-256. **15,308** files were then removed, **250,088,273** logical bytes.

The checkpoint root remains, as do its now-empty directories. Sibling diagnostics under `development/tmp/github_checkpoint/` were not modified. `HEAD` is still `e86fd4512028af4ce698090d48c1b672dd68600c`. No provider call was made, and the game, the AI-DM, and the test suite were not run.

The caveat is recoverability. Commit `4320bcdd50471c744746811f213a60b1893496d2` can rebuild the Git content of 15,210 paths. It does not reproduce the CRLF working-tree bytes of 15,039 of those paths, the edited bytes of 31 paths, or the 67 paths that were never in the commit. Those exact bytes are in the archive. The archive is a same-disk recovery copy, not an independent backup.

These files were ignored and were never current Git index entries. Removing them does not reduce GitHub repository storage. The historical commit still holds the blobs it already held.

## 2. Repository State

Confirmed before any checkpoint file was deleted, and again after deletion.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote tracking ref | `origin/feature/product-realization` |
| Remote tracking SHA | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Merge, rebase, cherry-pick, or bisect | None in progress |
| Staged changes | None |
| Unstaged tracked changes | None |

Untracked files present at the start were the earlier storage-cleanup reports and manifests. The Phase 2B-C3 manifest was added before deletion. They were left untracked.

Logical repository size immediately before deletion, with the manifest already present: **91,707** files, **3,690,654,138** bytes. The method is the sum of regular-file lengths in the whole project, including `.git`, without following reparse points. That walk found no reparse points.

The same measurement before the manifest existed was 91,706 files and 3,676,817,357 bytes. The difference is the manifest itself: 13,836,781 bytes. That earlier figure is 15,001 bytes and one file above Phase 2B-C2's post-deletion measurement, which is `artifacts/storage_cleanup_phase2b_c2_report.md`.

`git diff --stat` and `git diff --cached --stat` were empty before and after deletion. No commit was created. No fetch or push was run.

## 3. Historical Checkpoint Inventory

The only deletion root was `development/tmp/github_checkpoint/baseline_4320bcd/`. Its parent `development/tmp/github_checkpoint/` was not a deletion root. The target, its parent, `development/tmp/`, and `development/` were ordinary directories, not symbolic links, junctions, or other reparse points. The walk did not follow links. No nested Git directory was present. No reparse point was found anywhere in the repository walk.

A fresh inventory found **15,308** regular files and **1,280** directories below the checkpoint root, totaling **250,088,273** bytes. That matches the Phase 2 audit row for the checkout excluding bytecode, and it matches the Phase 2B-C1 remainder (248,556,335 bytes in the 15,241 commit paths plus 1,531,938 bytes in the 67 extra paths). The target had not gained or lost files since that audit.

Twenty-one of the directories were already empty `__pycache__` directories left by Phase 2B-C1. They contained no files.

Every regular file was ignored by `.gitignore` rule `development/tmp/` and was absent from `git ls-files`. No tracked file was inside the target.

| Relationship to commit `4320bcd` | Files | Logical bytes |
| --- | ---: | ---: |
| Exact working-tree bytes of the Git blob | 171 | 49,776,420 |
| Same Git content, CRLF checkout | 15,039 | 198,122,506 |
| Path exists in the commit, content differs | 31 | 657,409 |
| Absent from the commit | 67 | 1,531,938 |
| Total | 15,308 | 250,088,273 |

All 15,241 commit paths were present on disk. None of the commit paths were missing. Commit-associated disk bytes are 49,776,420 + 198,122,506 + 657,409 = **248,556,335**, the audit figure.

The 67 paths absent from the commit are individual manifest entries:

- 5 files under `.pytest_cache/`
- 61 files in six `development/tmp/pytest/test_golden_replay_*` stores
- `docs/maintenance/protected_replay_ci_20261018.md` (11,298 bytes)

Appendix D's prose figure of 1,532,640 bytes for the non-bytecode extras remains 702 bytes higher than the files on disk. Phase 2B-C1 already recorded that gap. The classification total of 1,531,938 bytes was used, and no file was added or dropped to force it.

## 4. Git Recoverability

Commit `4320bcdd50471c744746811f213a60b1893496d2` is in the local object database. `git cat-file -t` returned `commit`. Its tree is `c5e8c19e9ac9b333bf3f0bd1abc9f74df41e44d9`, and `git cat-file -t` returned `tree`. The tree lists 15,241 blobs, all mode `100644`, and 1,236 subtrees. Batch-check of the commit, the root tree, every subtree, and every blob reported no missing object. There are no symlinks and no submodules in that tree.

Comparison used Git blob hashes. Raw file bytes were hashed as Git blobs and checked with `git hash-object --no-filters` on a sample; the hashes matched. For text, CRLF was converted to LF using Git's rule that a NUL in the first 8,000 bytes marks a binary file and skips conversion. Samples of the CRLF files were also passed through `git -c core.autocrlf=true hash-object --path=<historical path>`. Those clean hashes matched the commit blobs. The repository's local `core.autocrlf` is `false`, and there is no `.gitattributes` file, so a checkout today writes the blob bytes rather than CRLF.

| Category | Files | Checkpoint bytes | Recoverable from the commit |
| --- | ---: | ---: | --- |
| Exact bytes | 171 | 49,776,420 | Yes, byte for byte. Blob size equals the file size. |
| CRLF checkout | 15,039 | 198,122,506 | Content yes. Exact CRLF bytes no. The corresponding blobs total 194,331,972 bytes; the 3,790,534 byte difference is the inserted CR bytes. |
| Content differs | 31 | 657,409 | The older blob is in Git. The checkpoint bytes are not. `core.autocrlf=true` clean filtering still did not match the blob. |
| Absent from the commit | 67 | 1,531,938 | No. |

The 31 differing files are LF files (`CR` count 0). They are local edits on top of the historical checkout, not a newline conversion. Eighteen are a single test-function rename that appends the test module name. One test passes `accepted_delivery` into an expectation call. The other twelve are larger local edits:

| Path | Checkpoint bytes | Blob bytes | Edit |
| --- | ---: | ---: | --- |
| `.github/workflows/convergence-checks.yml` | 5,343 | 5,037 | Protected-replay report path and shell steps |
| `game/immutable_valid_response.py` | 98,016 | 97,669 | Internal stage-label pattern |
| `requirements.txt` | 223 | 127 | `httpx` pin appended |
| `tests/helpers/failure_dashboard_orchestration.py` | 4,429 | 3,174 | Report-path environment handling |
| `tests/helpers/golden_replay.py` | 90,619 | 89,610 | `accepted_delivery` parameter |
| `tests/helpers/golden_replay_projection.py` | 18,373 | 17,617 | Sanitizer mode and delivery verification |
| `tests/test_failure_dashboard_orchestration.py` | 8,451 | 7,665 | Added test |
| `tests/test_golden_replay_projection.py` | 5,824 | 3,012 | Added tests |
| `tests/test_golden_replay_structural_invariants.py` | 8,585 | 8,224 | Assertion updated for host delivery |
| `tests/test_pr_br_continuation18_immutable_boundary.py` | 26,232 | 25,814 | Added parameter case |
| `tests/test_validation_layer_audit_smoke.py` | 6,601 | 5,565 | Added test |
| `tools/validation_layer_audit.py` | 28,933 | 27,643 | Gate-call scan signature |

`tests/test_co102_live_protected_replay_pipeline.py` is the single call-site edit (2,059 bytes on disk, blob 2,010). The eighteen renamed tests are the other `tests/test_*.py` files in the differing set. Their names and hashes are in the manifest.

These 31 edits were already inside the audited 250,088,273 bytes. The audit's sample had described one workflow delta. The exhaustive compare found the full set. The directory had not changed since the audit; the sample had not enumerated every edit.

## 5. Recovery Archive

| Item | Value |
| --- | --- |
| Path | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\ashen_thrones_phase2b_c3_checkpoint_4320bcd_20261031.zip` |
| Compressed size | 75,223,700 bytes |
| SHA-256 | `1f87961a5dca24047b8188c095dbcd01edbf6fc9fa7b035da9275f07796fb894` |
| Entries | 15,308 regular files |
| Created | 2026-10-31, before publication |
| Same physical disk as the repository | Yes, `C:` |
| Independent backup | No. This is a same-disk recovery copy. |

The archive was written as a `.partial` file and renamed only after verification. The published bytes are the partial bytes. The manifest is not inside the archive. Directory entries were not stored in the ZIP, because the entry count had to equal the file count. The manifest's `directories` list has all 1,280 directories, including the 21 that were already empty, so the directory tree can be recreated.

Verification before deletion:

1. `testzip` passed.
2. Entry count was 15,308, with no duplicate names.
3. No entry was absolute or contained `..`.
4. Every uncompressed size matched the manifest.
5. Every archived SHA-256 matched the manifest.
6. The archive was extracted outside the repository. The extracted path set, file count (15,308), logical byte total (250,088,273), and SHA-256 of every file matched the checkpoint manifest, not merely the Git blobs.
7. The extraction directory was removed. The ZIP was kept.
8. After the rename, the published archive opened again, `testzip` passed, the entry count was still 15,308, and the SHA-256 was unchanged.

After deletion, the same archive was still readable, `testzip` passed, and the SHA-256 was unchanged.

Recovery: unzip so each entry lands at its repository-relative path. Recreate directories from the manifest. Do not extract over live files outside the checkpoint directory. Use the commit only for the historical Git content described above.

## 6. Deletion Results

Removal used `os.remove` on the exact manifest paths, in manifest order. Immediately before each removal the path was checked again: it was inside the checkpoint root, it was a regular file, it was not a reparse point, and its size and SHA-256 matched the manifest. The whole target was untracked (`git ls-files` returned no paths) immediately before the loop. An exclusive open succeeded for every file before the loop and again immediately before each removal. No file was locked. No read-only attribute had to be cleared. No process command line contained `baseline_4320bcd`.

| Result | Value |
| --- | --- |
| Files removed | 15,308 |
| Logical bytes removed | 250,088,273 |
| Files that failed verification | 0 |
| Partial deletion | No |
| Checkpoint root | Still present |
| Directories remaining under the root | 1,280, all now empty of files |
| Files remaining under the root | 0 |

The root was not deleted. Parent directories were not deleted. No wildcard and no `git clean` were used.

## 7. Preservation Verification

The post-deletion repository walk is the check. Compared with the pre-deletion walk, the only removed paths were the 15,308 manifest paths. Nothing was added. No surviving file changed size or modification time.

| Check | Result |
| --- | --- |
| Manifest files absent | 15,308 of 15,308 |
| Unapproved files removed or resized | 0 |
| `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, `experiments/` | Present |
| `game/api.py`, `data/session.json` | Present |
| `artifacts/atgb/` | Present |
| `artifacts/pr_eg_r6_r5/snapshots/` | Present |
| `handoff/CURRENT_REVIEW.zip` | Present |
| `development/tmp/storage_cleanup_phase1_control/` | Present |
| Sibling diagnostics under `development/tmp/github_checkpoint/` | 96 files, 20,011,055 bytes, same SHA-256 and timestamps |
| `.venv/pyvenv.cfg` | Present |
| Tracked files | No tracked modification, deletion, or staging |
| `HEAD` and remote-tracking SHA | Unchanged |
| `.git` object payload | Unchanged, 312,105,733 bytes |
| External archive | Present, readable, same SHA-256 |

The sibling total matches the Phase 2 audit's C5 figure for files outside `baseline_4320bcd/`.

## 8. Storage Measurements

| Metric | Bytes or count |
| --- | ---: |
| Repository size before deletion | 91,707 files, 3,690,654,138 bytes |
| Repository size after deletion | 76,399 files, 3,440,565,865 bytes |
| Files removed | 15,308 |
| Logical bytes removed | 250,088,273 |
| Archive compressed size | 75,223,700 |
| Repository working-tree reduction | 250,088,273 |
| Net disk-space recovery | 174,864,573 |
| Unexpected file changes | 0 |
| Git object storage change | 0 |

The working-tree reduction is the before total minus the after total. The manifest is in both totals, so it is not part of the reduction. The archive lives outside the repository, so it is not part of the repository totals. Net disk recovery is the working-tree reduction minus the archive's 75,223,700 bytes.

`.git` stayed at 647,414,009 bytes. `.git/objects` stayed at 312,105,733 bytes. No garbage collection and no history rewrite were run. GitHub's stored history is unchanged because this checkpoint was ignored working material.

## 9. Unexpected Findings

The file count and byte total matched the audit, so the deletion set was not widened or narrowed.

The exhaustive Git compare is stronger than the audit's sample. Of the 15,241 commit paths, 15,210 match the commit after accounting for CRLF, and 31 are real LF edits. Those 31 were already in the measured byte total. Their checkpoint bytes exist only in the archive. Their previous blobs remain in commit `4320bcdd50471c744746811f213a60b1893496d2`.

The first archive extraction check compared path lists in Windows sort order rather than repository-relative sort order and stopped before publication. No checkpoint file was deleted. The partial ZIP was already hash-verified. A second extraction, compared as a path set, matched all 15,308 files and 250,088,273 bytes. The partial file was then renamed to the published name. Its SHA-256 did not change.

Empty directories, including 21 `__pycache__` directories from Phase 2B-C1, were left in place. The checkpoint root was left in place.

## 10. Remaining Cleanup Candidates

Not touched in this pass.

| Candidate | What it is | Bytes | Notes |
| --- | ---: | ---: | --- |
| Maintenance venv and ignored `.venv-broken` | Local environments | 63,307,128 + 29,959,799 | Appendix C is the package record. Active `.venv` stays |
| Tracked `.venv-broken` | Files still in the index | 24,397,647 | Separate ordinary commit |
| C3 duplicate ZIP excess | Extra working-tree copies | 66,621,016 outside the current PR-PLAY-12 trio | Current review copies stay |
| C4 leftovers | `venv/`, PR-PLAY overlays, other `development/tmp`, `disposable_state/`, 66 orphan bytecode files, and the 18,195-byte isolation directory | 144,053,732 | Not classified as safe to delete |
| Checkpoint sibling diagnostics | Files beside `baseline_4320bcd/` | 20,011,055 | Confirmed unchanged |
| `development/tmp/storage_cleanup_phase1_control/` | Phase 1 evidence | 17,652,087 | Left in place |
| `.git/cursor` | Local IDE index | Left as recorded in Phase 2A | Not a deletion target |

The empty directory tree under `development/tmp/github_checkpoint/baseline_4320bcd/` remains. It has no file content.

## 11. Recommendation

Phase 2B-C3 can be closed. The approved files are gone from the work tree, their bytes match the audit, and the external archive restored every file with the manifest hash before those files were deleted.

The safest next candidate, only if a later pass is authorized, is the maintenance virtual environment `development/tmp/maintenance_ci_venv/` (63,307,128 bytes) together with the ignored files in `.venv-broken/` (29,959,799 bytes). That pass has to keep the active `.venv`, and it should treat Appendix C as the package record. It is not authorized by this report. Tracked `.venv-broken` files need a separate ordinary commit and should not be mixed into that local deletion.

Phase 2A remains the pushed deletion of tracked pytest working stores. Phase 2B-C1 remains the local deletion of ignored checkpoint bytecode. Phase 2B-C2 remains the local archive-and-delete of the ignored pytest stores. Phase 2B-C3 is the local archive-and-delete of the remaining historical checkpoint files. The four are separate operations.
