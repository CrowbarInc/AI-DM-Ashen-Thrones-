# Ashen Thrones — Storage Cleanup Phase 2B-C4

Status: **PASS WITH CAVEATS**. The inactive maintenance environment and the ignored files in `.venv-broken/` were archived outside the repository, the archive was recovered and checked against the working-tree bytes, and only the manifest files were deleted. No Git commit was created. Nothing was pushed.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report and `artifacts/storage_cleanup_phase2b_c4_manifest.json` are untracked. The manifest was written before deletion and is included in both deletion measurements below. This report was written after the post-deletion measurement, so its bytes are not part of those totals.

## 1. Executive Summary

Status: **PASS WITH CAVEATS**.

Deletion occurred. The external archive passed recovery verification: every archived file was extracted and matched the manifest path, length, and SHA-256. **9,632** files were then removed, **93,266,927** logical bytes.

`development/tmp/maintenance_ci_venv/` now contains no files. Its directory tree remains. `.venv-broken/` still contains the **2,663** tracked files, **24,397,647** bytes, that this phase was required to leave in place. `HEAD` is still `e86fd4512028af4ce698090d48c1b672dd68600c`. No provider call was made, and the game, the AI-DM, and the test suite were not run.

The caveat is recoverability. The archive holds the exact deleted bytes, and it sits on the same disk as the repository (`C:`). It is a same-disk recovery copy, not an independent backup. Losing that disk loses the archive as well.

These files were ignored. The maintenance tree was never in the Git index. The deleted `.venv-broken` files were not index entries. Removing them does not reduce GitHub repository storage. The tracked `.venv-broken` blobs remain in history and in the index.

## 2. Repository State

Confirmed before any target file was deleted, and again after deletion.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote tracking ref | `origin/feature/product-realization` |
| Remote tracking SHA | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Merge, rebase, cherry-pick, or bisect | None in progress |
| Staged changes | None |
| Unstaged tracked changes | None |

Untracked files present at the start were the earlier storage-cleanup reports and manifests. The Phase 2B-C4 manifest was added before deletion. They were left untracked.

Logical repository size immediately before deletion, with the manifest already present: **76,401** files, **3,452,562,256** bytes. The method is the sum of regular-file lengths in the whole project, including `.git`, without following reparse points. That walk found no reparse points.

The same measurement before the manifest existed was 76,400 files and 3,440,583,520 bytes. The difference is the manifest itself: 11,978,736 bytes. That earlier figure is 17,655 bytes and one file above Phase 2B-C3's post-deletion measurement, which is `artifacts/storage_cleanup_phase2b_c3_report.md`.

`git diff` was empty of tracked changes before and after deletion. No commit was created. No fetch or push was run.

## 3. Reference Audit Reconciliation

Fresh counts matched the Phase 2 audit. Nothing was added or dropped to force the totals.

| Set | Audit | Fresh inventory |
| --- | ---: | ---: |
| `development/tmp/maintenance_ci_venv/` | 7,088 files, 63,307,128 bytes | 7,088 files, 63,307,128 bytes |
| `.venv-broken/` total | 5,207 files, 54,357,446 bytes | 5,207 files, 54,357,446 bytes |
| `.venv-broken/` tracked | 2,663 files, 24,397,647 bytes | 2,663 files, 24,397,647 bytes |
| `.venv-broken/` ignored | 29,959,799 bytes | 2,544 files, 29,959,799 bytes |
| Eligible total | 93,266,927 bytes | 9,632 files, 93,266,927 bytes |

The audit states the ignored byte total and the tracked file count. The ignored file count of 2,544 is the remainder of 5,207 − 2,663. That remainder was on disk.

Both roots, `development/`, `development/tmp/`, and the repository root were ordinary directories. The walk did not follow links. No reparse point, inaccessible path, or non-regular file was inside either target. Top-level entries in each target were `Include`, `Lib`, `Scripts`, and `pyvenv.cfg`.

Installed distribution directory names under `Lib/site-packages` matched Appendix C exactly.

Maintenance environment: annotated_doc-0.0.5, annotated_types-0.8.0, anyio-4.15.1, certifi-2026.10.18, click-8.5.0, colorama-0.4.6, fastapi-0.146.0, h11-0.16.0, httpcore-1.0.9, httpcore2-2.14.0, httpx-0.28.1, httpx2-2.14.0, idna-3.20, iniconfig-2.3.1, jiter-0.17.0, openai-3.35.1, opentelemetry_api-1.45.1, packaging-26.3, pip-25.0.1, pluggy-1.7.0, pydantic-2.14.1, pydantic_core-2.50.1, pygments-2.21.0, pytest-9.1.1, python_dotenv-1.2.4, python_multipart-0.0.32, sniffio-1.3.1, starlette-1.9.0, truststore-0.10.5, typing_extensions-4.16.0, typing_inspection-0.4.4, uvicorn-0.54.0.

`.venv-broken`: annotated_doc-0.0.4, annotated_types-0.7.0, anyio-4.13.0, certifi-2026.2.25, click-8.3.1, colorama-0.4.6, distro-1.9.0, fastapi-0.135.3, h11-0.16.0, httpcore-1.0.9, httpx-0.28.1, idna-3.11, iniconfig-2.3.0, jiter-0.13.0, openai-2.30.0, packaging-26.0, pip-26.1.2, pluggy-1.6.0, pydantic-2.12.5, pydantic_core-2.41.5, pygments-2.20.0, pytest-9.0.2, python_dotenv-1.2.2, python_multipart-0.0.22, sniffio-1.3.1, starlette-1.0.0, tqdm-4.67.3, typing_extensions-4.15.0, typing_inspection-0.4.2, uvicorn-0.42.0.

Every maintenance file was untracked and ignored by `.gitignore` line 22, pattern `development/tmp/`. Every ignored `.venv-broken` file was untracked and ignored by `.gitignore` line 12, pattern `.venv-broken/`. Tracked status came from `git ls-files`, not from the ignore rule. The ignore rule also matches the tracked `.venv-broken` paths; those 2,663 index entries were excluded from the manifest anyway.

Directory inventory, not counting the two target roots: **581** directories under the maintenance environment and **464** under `.venv-broken`.

## 4. Environment Activity Investigation

Neither target was in use. Neither environment was activated for this inspection.

| Check | Result |
| --- | --- |
| `VIRTUAL_ENV` | Empty |
| Shell `python` | `WindowsApps\python.exe`, then `AppData\Local\Python\bin\python.exe` |
| Shell `pip` | `AppData\Local\Python\bin\pip.exe` |
| Operator interpreter | `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\python.exe` |
| Process executable inside either target | None |
| Process command line using either target | None |
| Python, pytest, uvicorn, or pip process | None, other than the inventory interpreter above |
| Exclusive open of every target file | Succeeded. No file was locked |
| `.github` workflows, `scripts/`, `docs/`, `Makefile` | No reference to either target |
| `scripts/run_live_playtest.ps1` | Selects `.venv/Scripts/python.exe` |
| `.idea/misc.xml` | Project SDK `Python 3.9 (ashen_thrones_ai_gm)`, the separate `venv/` tree |

`pyvenv.cfg` identifies the trees without activating them.

The maintenance environment was created by `C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m venv` of `development/tmp/maintenance_ci_venv`, Python 3.12.14. That line is the creation record. No current launcher calls that interpreter.

`.venv-broken/pyvenv.cfg` records Python 3.12.0 and the create command `python -m venv` of `.venv`. It is a renamed earlier environment. The active `.venv/pyvenv.cfg` records the same base interpreter and a create command for `.venv`. Appendix C shows the two installs are different package sets. The active tree was not opened for deletion.

A repository text search found 71 mentions. All of them are historical:

| Kind | Hits |
| --- | ---: |
| Earlier cleanup reports | 37 |
| Recorded commands in `development/tmp/github_checkpoint/` | 24 |
| Exclusion lists in the Phase 1 control script and the Phase 2A preflight | 7 |
| Repository organization note | 2 |
| PR-AB campaign status note | 1 |

The checkpoint hits are saved command lines and a pip install log from a past run. The Phase 1 and Phase 2A scripts name the directories so those passes would leave them alone. None of those files launches either interpreter. The checkpoint siblings and `development/tmp/storage_cleanup_phase1_control/` were not modified.

## 5. Eligible and Excluded File Inventory

Eligibility required a regular file that was untracked, ignored, not a reparse point, inside one of the two authorized roots, and not in use. Tracked files under `.venv-broken/` were ineligible.

| Class | Files | Logical bytes | In the deletion manifest |
| --- | ---: | ---: | --- |
| Maintenance environment | 7,088 | 63,307,128 | Yes |
| Ignored `.venv-broken` files | 2,544 | 29,959,799 | Yes |
| Tracked `.venv-broken` files | 2,663 | 24,397,647 | No |
| Eligible total | 9,632 | 93,266,927 | Yes |

No untracked file inside either target failed the ignore check. No eligible file was read-only. SHA-256 for every eligible file, and for every excluded tracked file, is in the manifest.

The manifest is `artifacts/storage_cleanup_phase2b_c4_manifest.json`. It was written at 2026-10-31T20:15:35-04:00, before the archive was published and before any file was deleted.

## 6. Recovery Archive

| Item | Value |
| --- | --- |
| Path | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` |
| Compressed size | 37,865,504 bytes |
| SHA-256 | `fde74bd409eccc806e48db825c80b29e398c15c8a182638fc771f4b80eb3c858` |
| Entries | 9,632 regular files |
| Created | 2026-10-31, before publication |
| Same physical disk as the repository | Yes, `C:` |
| Independent backup | No. This is a same-disk recovery copy. |

The archive was written as a `.partial` file and renamed only after verification. The published bytes are the partial bytes. The manifest is not inside the archive. Directory entries were not stored in the ZIP, because the entry count had to equal the file count. The manifest's directory lists have all 581 maintenance directories and all 464 `.venv-broken` directories, so the directory tree can be recreated. Those directories are still present in the work tree.

Tracked `.venv-broken` files are not in the archive. Active `.venv` files are not in the archive. Paths were stored as repository-relative names. Symbolic links and junctions were not followed; none were present.

Verification before deletion:

1. `testzip` passed.
2. Entry count was 9,632, with no duplicate names.
3. No entry was absolute or contained `..`.
4. Every uncompressed size matched the manifest.
5. Every archived SHA-256 matched the manifest.
6. The archive was extracted outside the repository. The extracted path set, file count (9,632), logical byte total (93,266,927), and SHA-256 of every file matched the manifest.
7. The extraction directory was removed. The ZIP was kept.
8. After the rename, the published archive opened again, `testzip` passed, the entry count was still 9,632, and the SHA-256 was unchanged.

After deletion, the same archive was still readable, `testzip` passed, and the SHA-256 was unchanged.

Recovery: unzip so each entry lands at its repository-relative path. Recreate any missing directories from the manifest. Leave the tracked `.venv-broken` files as they are. Do not extract over `.venv/`.

## 7. Deletion Results

Removal used `os.remove` on the exact manifest paths, in manifest order. Immediately before each removal the path was checked again: it was inside its authorized root, it was a regular file, it was not a reparse point, `git ls-files` did not list it, `git check-ignore` still ignored it, and its size and SHA-256 matched the manifest. An exclusive open succeeded immediately before each removal. No file was locked. No read-only attribute had to be cleared.

| Result | Value |
| --- | --- |
| Files removed | 9,632 |
| Logical bytes removed | 93,266,927 |
| Files that failed verification | 0 |
| Partial deletion | No |
| Maintenance root | Still present, 581 subdirectories, 0 files |
| `.venv-broken/` files remaining | 2,663 |
| `.venv-broken/` bytes remaining | 24,397,647 |

Parent directories were not deleted. No wildcard and no `git clean` were used. Empty directories were left in place.

## 8. Preservation Verification

The post-deletion repository walk is the check. Compared with the pre-deletion walk, the only removed paths were the 9,632 manifest paths. Nothing was added. No surviving file changed size or modification time.

| Check | Result |
| --- | --- |
| Manifest files absent | 9,632 of 9,632 |
| Unapproved files removed or resized | 0 |
| `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, `experiments/` | Present |
| `game/api.py`, `data/session.json` | Present |
| `artifacts/atgb/` | Present |
| `artifacts/pr_eg_r6_r5/snapshots/` | Present |
| `handoff/CURRENT_REVIEW.zip` | Present |
| `development/tmp/storage_cleanup_phase1_control/` | Present |
| `development/tmp/github_checkpoint/` | Present |
| Active `.venv/` | 5,951 files, 56,291,644 bytes, same SHA-256 for every file |
| `venv/` `pyvenv.cfg` | Present |
| Tracked `.venv-broken` files | 2,663 of 2,663 present, same size and SHA-256 |
| Tracked files | No tracked modification, deletion, or staging |
| `HEAD` and remote-tracking SHA | Unchanged |
| `.git/index` and `.git/HEAD` | Same SHA-256 as before deletion |
| `.git` object payload | Unchanged, 312,105,733 bytes |
| External archive | Present, readable, same SHA-256 |

The active `.venv` size matches the Phase 2 audit figure for that tree. It was compared file by file, before deletion and after.

## 9. Storage Measurements

| Metric | Bytes or count |
| --- | ---: |
| Repository size before the manifest | 76,400 files, 3,440,583,520 bytes |
| Repository size before deletion | 76,401 files, 3,452,562,256 bytes |
| Repository size after deletion | 66,769 files, 3,359,295,329 bytes |
| Files removed | 9,632 |
| Logical bytes removed | 93,266,927 |
| Archive compressed size | 37,865,504 |
| Repository working-tree reduction | 93,266,927 |
| Net disk-space recovery | 55,401,423 |
| Unexpected file changes | 0 |
| Git object storage change | 0 |

The working-tree reduction is the before-deletion total minus the after-deletion total. The manifest is in both totals, so it is not part of the reduction. The archive lives outside the repository, so it is not part of the repository totals. Net disk recovery is the working-tree reduction minus the archive's 37,865,504 bytes. That figure is logical file bytes, the same method used in Phase 2B-C3. Cluster slack is not included.

`.git` stayed at 647,414,009 bytes. `.git/objects` stayed at 312,105,733 bytes. No garbage collection and no history rewrite were run. GitHub's stored history is unchanged because the deleted files were ignored working material.

## 10. Unexpected Findings

The file counts and byte totals matched the audit, so the deletion set was not widened or narrowed.

No reparse points were found. No file was locked. No untracked, non-ignored file was inside either target. No non-environment top-level material was present.

Empty directories were left in place, including the maintenance root and its 581 subdirectories. `.venv-broken/` remains because its tracked files remain. The remaining tracked files are not a runnable environment. The active interpreter is `.venv`.

## 11. Remaining Cleanup Candidates

Not touched in this pass.

| Candidate | What it is | Bytes | Notes |
| --- | ---: | ---: | --- |
| Tracked `.venv-broken` | Files still in the index | 24,397,647 | Separate ordinary commit. Not a local ignored-file deletion |
| C3 duplicate ZIP excess | Extra working-tree copies | 66,621,016 outside the current review trio | Not started |
| C4 leftovers | `venv/`, PR-PLAY overlays, other `development/tmp`, `disposable_state/`, 66 orphan bytecode files, and the isolation directory | 144,053,732 | Not classified as safe to delete. `.idea` still selects the Python 3.9 SDK |
| Checkpoint sibling diagnostics | Files beside the removed `baseline_4320bcd/` tree | 20,011,055 | Left in place |
| `development/tmp/storage_cleanup_phase1_control/` | Phase 1 evidence | Left in place | Protected |
| `.git/cursor` | Local IDE index | Left as recorded in Phase 2A | Not a deletion target |
| Active `.venv/` | Documented interpreter | 56,291,644 | Retained |

The empty directory tree under `development/tmp/maintenance_ci_venv/` remains. It has no file content. The empty directory tree under `development/tmp/github_checkpoint/baseline_4320bcd/` also remains from Phase 2B-C3.

## 12. Recommendation

Phase 2B-C4 can be closed. The approved files are gone from the work tree, their bytes match the audit, and the external archive restored every file with the manifest hash before those files were deleted.

Do not start another cleanup phase from this report. Tracked `.venv-broken` files need their own ordinary commit if they are later authorized to leave the index. Duplicate ZIP copies and the historical leftovers, including `venv/`, stay where they are until a later pass is explicitly authorized. Active `.venv/` stays.

Phase 2A remains the pushed deletion of tracked pytest working stores. Phase 2B-C1 remains the local deletion of ignored checkpoint bytecode. Phase 2B-C2 remains the local archive-and-delete of the ignored pytest stores. Phase 2B-C3 remains the local archive-and-delete of the remaining historical checkpoint files. Phase 2B-C4 is the local archive-and-delete of the maintenance virtual environment and the ignored files in `.venv-broken/`. The five are separate operations.
