# Ashen Thrones — Storage Cleanup Phase 2B-C1

Status: **complete.** Phase 2A is pushed. Phase 2B-C1 removed the audited checkpoint bytecode from local disk. Phase 2B-C1 did not create a Git commit.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report and `artifacts/storage_cleanup_phase2b_c1_manifest.json` are untracked. They are not in the deletion totals below. The manifest is included in both repository-size measurements, because it was written before those measurements.

## 1. Executive summary

Phase 2A's deletion commit is on `origin/feature/product-realization` at `e86fd4512028af4ce698090d48c1b672dd68600c`. The push was a normal fast-forward. Local and remote now match. Nothing was force-pushed and history was not rewritten.

Phase 2B-C1 then removed 1,064 ignored `.pyc` files, 35,207,113 logical bytes, from `development/tmp/github_checkpoint/baseline_4320bcd/`. Every removed path was in the manifest. No other file was deleted. The corresponding `.py` sources remain. The checkpoint directory remains. `HEAD` is still the Phase 2A commit. No provider call was made.

These bytecode files were never in Git. Removing them does not reduce GitHub repository storage.

## 2. Phase 2A push verification

The closeout had already finalized the cleanup locally and had not pushed it. Before the push, this pass re-checked that record.

| Check | Result |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Parent | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Subject | `chore: remove historical pytest working stores` |
| Name-status | 31,886 deletions, no additions, no modifications |
| Manifest | Every committed path is in `artifacts/storage_cleanup_phase2a_manifest.json`, and every manifest path is in the commit |
| Manifest logical bytes | 523,570,476 |
| Protected paths in the commit | None under `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `experiments/`, `docs/`, `handoff/`, `artifacts/atgb/`, `artifacts/pr_eg_r6_r5/`, or `artifacts/pr_play` |
| Staged or unstaged tracked changes | None |
| Untracked reports | Left untracked. They were not staged |
| Merge, rebase, cherry-pick, or bisect | None in progress |

`origin` is `https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-.git`, the repository named in `docs/maintenance/protected_replay_ci_20261018.md`. The remote URL was not changed. No new remote was created.

`git fetch origin` completed. `origin/feature/product-realization` was still `c16d922865b7182d47b87d27ec633f9308f1ef4c`. The local branch was ahead by 1 and behind by 0.

## 3. Remote branch and commit SHA

Push command: `git push origin feature/product-realization`. No `--force`, `--force-with-lease`, `--mirror`, `--all`, or `--tags`.

Result:

```text
To https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-.git
   c16d9228..e86fd451  feature/product-realization -> feature/product-realization
```

| Item | Value |
| --- | --- |
| Remote | `origin` |
| Branch | `feature/product-realization` |
| Local HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote HEAD after the push | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| `git ls-remote` after Phase 2B-C1 | `e86fd4512028af4ce698090d48c1b672dd68600c refs/heads/feature/product-realization` |
| Ahead / behind | 0 / 0 |

The remote branch was checked again after the bytecode deletion. It was unchanged.

## 4. C1 pre-deletion inventory

The Phase 2 audit's C1 row is bytecode that exists only in the ignored checkout of commit `4320bcdd50471c744746811f213a60b1893496d2`: `development/tmp/github_checkpoint/baseline_4320bcd/**/__pycache__` and `*.pyc`. Expected size: 1,064 files, 35,207,113 bytes.

The checkout on disk still matched the audit's whole-tree totals: 16,372 files, 285,295,386 bytes. All 15,241 paths from commit `4320bcd` were present. None of those committed paths is a `.pyc` file. The checkout had 1,131 extra paths. Of those, 1,064 are `.pyc` files totaling 35,207,113 bytes. The other 67 extra paths are pytest stores and pytest cache, and they were left in place.

Each of the 1,064 files passed the deletion checks:

1. Path is under `development/tmp/github_checkpoint/baseline_4320bcd/`.
2. The extension is `.pyc`.
3. `git check-ignore` ignores it.
4. `git ls-files` does not track anything under the checkpoint.
5. It is a regular file.
6. The checkpoint root and every walked directory and file were free of symlinks, junctions, and other reparse points. Resolved paths stayed inside the checkpoint.
7. The corresponding `.py` source exists in the checkpoint. Cache names follow `module.cpython-<tag>.pyc`, including pytest's extended tag. 598 files use a `-pytest-` tag. The source path is the module name before `.cpython-`, beside the `__pycache__` directory. All 1,064 sources were regular files inside the checkpoint.
8. No active workflow requires these caches. The maintenance note retains sibling diagnostics under `development/tmp/github_checkpoint/` outside this checkout. Those siblings were not touched. Searches for `baseline_4320bcd` land in the storage-cleanup reports, which classify this bytecode as the local deletion. A later Python run inside the snapshot would compile again from the `.py` files.
9. No path is inside `.venv`, `.venv-broken`, or `venv`. No other Python, pytest, or uvicorn process was running. No process command line was using the checkpoint.
10. The Phase 2 audit protects the sibling diagnostics, the 66 orphan bytecode files elsewhere, active `.venv`, and the pinned evidence trees. This set is the audit's C1 row, and it is distinct from those protections.

The files sit in five top-level folders of the checkpoint checkout:

| Folder inside the checkpoint | Files | Logical bytes |
| --- | ---: | ---: |
| `tests` | 742 | 26,616,189 |
| `game` | 210 | 6,878,113 |
| `experiments` | 75 | 862,531 |
| `tools` | 36 | 845,639 |
| `scripts` | 1 | 4,641 |
| **Total** | **1,064** | **35,207,113** |

`development/tmp/github_checkpoint/baseline_4320bcd/game/api.py` was present before deletion.

## 5. C1 deletion manifest

`artifacts/storage_cleanup_phase2b_c1_manifest.json`

Written at `2026-10-31T17:47:07-04:00`, before any deletion. 455,518 bytes. It is untracked.

It records the branch, `HEAD`, the remote branch SHA, the audit reference, the file count, the byte total, and one record per file: relative path, logical size, SHA-256, ignored status, tracked status, and source path.

After the write, every record was read back and every file was hashed again. The hashes still matched. No file was deleted until that check passed. Immediately before each deletion, size, modification time, and SHA-256 were checked again. None had changed.

## 6. Exact files removed

1,064 files. The path list is the `files` array in the manifest. The directory totals are in section 4.

Removal used `os.remove` on those exact paths. Parent directories were not deleted. Empty `__pycache__` directories were left in place. No recursive directory delete, no `git clean`, and no wildcard outside the manifest.

## 7. Logical bytes removed

**35,207,113** logical bytes. That is the sum of the file lengths in the manifest, and it is the sum of the lengths of the files actually removed.

## 8. Actual local disk reduction

Measured as the sum of regular-file lengths in the whole project, including `.git`, after the manifest existed and before deletion, then again after deletion.

| Point | Files | Logical bytes |
| --- | ---: | ---: |
| Before deletion | 97,872 | 3,815,643,463 |
| After deletion | 96,808 | 3,780,436,350 |
| Net | 1,064 | 35,207,113 |

The NTFS allocation of the 1,064 files, from `FILE_STANDARD_INFO.AllocationSize`, was **37,432,720** bytes. Deleting the files released that allocation. The gap of **2,225,607** bytes is cluster slack: the filesystem had rounded each file up to a whole cluster, so the clusters freed are larger than the logical lengths.

The logical repository total dropped by the same 35,207,113 bytes as the file lengths. The before-and-after path inventory differed only by the 1,064 manifest paths. No other file was added, removed, or resized between the two measurements, so `.git` did not change size in that interval.

Why the figures are not one number:

- Logical bytes are the file contents. That total is 35,207,113, and the repository's summed file lengths fell by the same amount.
- On-disk allocation was 37,432,720 because NTFS stores each file in whole clusters. The extra 2,225,607 bytes were unused space inside those clusters, not additional content.
- GitHub storage is unchanged. The files were ignored, and they were never objects in the remote repository. No garbage collection and no history rewrite was run.
- The manifest is in both size measurements, so its 455,518 bytes do not appear in the net reduction. It remains on disk as the deletion record.
- Empty `__pycache__` directories remain. Directory entries are not file lengths, so they are not part of the 35,207,113.

## 9. Preservation verification

| Check | Result |
| --- | --- |
| Approved `.pyc` files absent | 1,064 of 1,064 |
| Unapproved files removed | 0 |
| Other files resized during the deletion | 0 |
| Corresponding `.py` sources | All 1,064 still present |
| Checkpoint `game/api.py` | Still present |
| Checkpoint directory | Still present |
| Other checkpoint contents | Unchanged. The 15,241 commit paths and the 67 non-bytecode extra paths were not in the manifest |
| Live `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `experiments/`, `docs/`, `handoff/` | Not in the deletion set. The whole-tree inventory shows they were not removed or resized |
| `artifacts/atgb/`, `artifacts/pr_play*`, `artifacts/pr_eg_r6_r5/` | Not in the deletion set. Same inventory result |
| Golden replay evidence and campaign state | Not in the deletion set |
| Tracked files | No tracked modification |
| `.venv`, `venv`, `.venv-broken` | Not in the deletion set |
| Python sources | None deleted |
| Earlier storage-cleanup reports and the Phase 2A manifest | Still present and untracked |
| `.gitignore` | Unchanged |
| Provider calls | None |

The `game/`, `tests/`, `experiments/`, `tools/`, and `scripts/` names in section 4 are folders inside the checkpoint checkout. They are not the live project trees.

## 10. Final Git status

Branch `feature/product-realization`.

| Item | Value |
| --- | --- |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Parent | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| `origin/feature/product-realization` | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Ahead / behind | 0 / 0 |
| Staged changes | None |
| Unstaged tracked changes | None |
| New commit from Phase 2B-C1 | None |

Untracked, and left untracked:

- `artifacts/storage_cleanup_audit.md`
- `artifacts/storage_cleanup_phase1_report.md`
- `artifacts/storage_cleanup_phase2_audit.md`
- `artifacts/storage_cleanup_phase2a_closeout.md`
- `artifacts/storage_cleanup_phase2a_manifest.json`
- `artifacts/storage_cleanup_phase2a_regression_investigation.md`
- `artifacts/storage_cleanup_phase2a_report.md`
- `artifacts/storage_cleanup_phase2b_c1_manifest.json`
- `artifacts/storage_cleanup_phase2b_c1_report.md` (this file)

## 11. Unexpected findings

The C1 file count and byte total matched the audit, so the deletion set was not widened or narrowed.

Appendix D of the Phase 2 audit says the 67 non-bytecode extra paths are 1,532,640 bytes. The files on disk total 1,531,938 bytes, which is 702 bytes lower. The same audit's classification row for the checkout excluding bytecode is 250,088,273 bytes. That row matches the disk: 285,295,386 − 35,207,113 = 250,088,273, and 248,556,335 bytes in the 15,241 commit paths plus 1,531,938 in the 67 extra paths is the same 250,088,273. The prose figure was not used to add or drop files.

598 of the caches use pytest's extended tag, `cpython-312-pytest-…`. The source file is still the module named before `.cpython-`. All of those sources existed. This is the same cache-name rule the original storage audit describes for source-backed bytecode.

## 12. Remaining cleanup candidates

Not touched in this pass.

| Candidate | What it is | Bytes | Notes |
| --- | ---: | --- | --- |
| C2 ignored pytest stores | Ignored `test_*` stores, including the cited PR-AR and PR-AQ reg directories | 105,879,032 | Audit step 3. Zip and verify hashes before deleting. Git does not have these bytes |
| Checkpoint remainder | `baseline_4320bcd/` after this bytecode removal, including the 67 extra non-bytecode paths | 250,088,273 | C2. Commit `4320bcd` remains the restore source for the checkout's committed paths. Sibling diagnostics stay C5 |
| Maintenance venv and ignored `.venv-broken` | Local environments | 63,307,128 + 29,959,799 | Appendix C is the package record. Active `.venv` stays |
| Tracked `.venv-broken` | Files still in the index | 24,397,647 | Separate ordinary commit. Not this pass |
| C3 duplicate ZIP excess | Extra working-tree copies | 66,621,016 outside the current PR-PLAY-12 trio | Current review copies stay |
| C4 leftovers | `venv/`, PR-PLAY overlays, other `development/tmp`, `disposable_state/`, 66 orphan bytecode files | 144,053,732 | Not classified as safe to delete |
| `.git/cursor` | Local IDE index | Left as recorded in Phase 2A | Not a deletion target |

Empty `__pycache__` directories inside the checkpoint remain. They are not file content.

## 13. Recommended next phase

Stop here.

The next storage candidate, only if a later pass is authorized, is the ignored pytest stores in audit step 3: 105,879,032 bytes. That pass has to write a verified archive first. It is not a Git commit, and it is not authorized by this report.

Phase 2A remains the pushed historical deletion of tracked pytest working stores. Phase 2B-C1 remains a local deletion of ignored bytecode. The two are separate operations.
