# Ashen Thrones — Storage Cleanup Phase 2C Recovery

Status: **PASS WITH CAVEATS**. The 2,663 tracked files under `.venv-broken/` were archived from their working-tree bytes, recovered and checked outside the repository, and removed in one ordinary commit. Nothing was pushed.

Date: November 1, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

The caveat is recoverability. The new archive holds the exact working-tree bytes, including the two mixed-line-ending `METADATA` files, and it sits on the same disk as the repository (`C:`). It is a verified same-disk recovery copy, not an independent backup. Losing that disk loses the archive as well. Git history still contains the blobs from the parent commit.

This report and `artifacts/storage_cleanup_phase2c_recovery_manifest.json` are untracked. The earlier Phase 2C report was not overwritten.

## A. Executive Summary

| Item | Result |
| --- | --- |
| Status | **PASS WITH CAVEATS** |
| Files removed | 2,663 |
| Logical bytes removed | 24,397,647 |
| Commit created | Yes. `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Pushed | No |

The same-disk archive is the caveat. The deletion set, the recovery test, and the commit contents matched the authorization.

## B. Original Blocker

The previous Phase 2C attempt deleted nothing. Git could reproduce 2,661 of the 2,663 working-tree files. These two could not be rebuilt byte for byte:

| Path | Working tree | Git blob | `core.autocrlf=true` smudge |
| --- | ---: | ---: | ---: |
| `.venv-broken/Lib/site-packages/jiter-0.13.0.dist-info/METADATA` | 5,348 bytes; 112 CRLF and 33 LF | 5,236 bytes; 145 LF | 5,381 bytes |
| `.venv-broken/Lib/site-packages/pydantic_core-2.41.5.dist-info/METADATA` | 7,420 bytes; 143 CRLF and 37 LF | 7,277 bytes; 180 LF | 7,457 bytes |

Each Git blob is LF on every line. The working tree keeps LF on some lines and CRLF on others. Removing every CR from the working tree produces the blob, and no other byte differs. A normal checkout with `core.autocrlf=true` converts every LF to CRLF, which is a third byte sequence. The clean filter strips every CR, so Git reports no modification, but the blob does not record which lines had the CR. One checkout setting cannot reproduce both the LF files and these mixed files.

The external archive stores the working-tree bytes themselves, not a Git smudge of the blobs. Both `METADATA` files were extracted and matched their original working-tree SHA-256.

| Path | Working-tree SHA-256 |
| --- | --- |
| `.venv-broken/Lib/site-packages/jiter-0.13.0.dist-info/METADATA` | `b2d480b4d187a0374311d2257b9f4050826977ef2f4ab2a5cb94710debbce31e` |
| `.venv-broken/Lib/site-packages/pydantic_core-2.41.5.dist-info/METADATA` | `131f371cd30e6de6f405ed616d59f1e427b0cef22ad92d7c39e527ed4c0184a9` |

`core.autocrlf` is still `true`. No `.gitattributes` file was created. `core.eol` and `core.safecrlf` remain unset.

## C. Repository State

Confirmed before the archive was written, again immediately before deletion, and again after the commit.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| Original HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Original HEAD tree | `60bf2b46a306c16a5e2822f2f9195540f4e05eb0` |
| Final HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Final HEAD tree | `d285a29c569f11abe5902c9f93d4a8a67e6a5612` |
| Commit parent | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote-tracking ref | `origin/feature/product-realization` |
| Remote-tracking HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Merge, rebase, cherry-pick, or bisect | None in progress |
| Branch relationship | Ahead of the remote by 1 commit. Not pushed |

After the commit, `git status` shows no staged or unstaged tracked changes. The untracked files are the earlier cleanup reports and manifests, the Phase 2C recovery manifest, the earlier Phase 2C report, and this report.

## D. Inventory Reconciliation

The authorized set was every tracked regular file under `.venv-broken/`. Fresh index membership was compared with `tracked_files_excluded` in `artifacts/storage_cleanup_phase2b_c4_manifest.json`.

| Set | Files | Logical bytes | Match |
| --- | ---: | ---: | --- |
| Expected | 2,663 | 24,397,647 | — |
| `git ls-files` under `.venv-broken/` | 2,663 | 24,397,647 | Yes |
| On-disk regular files under `.venv-broken/` | 2,663 | 24,397,647 | Yes |
| Working-tree SHA-256 versus Phase 2B-C4 | 2,663 of 2,663 | — | Yes |

Every path was tracked at stage 0, present in `HEAD` with the same mode (`100644`) and object id, and had no staged or unstaged Git diff. None was a symbolic link or reparse point. No ignored or untracked file was inside `.venv-broken/`.

Reconstruction outside the repository, without changing the index, matched the earlier Phase 2C finding:

| Classification | Files |
| --- | ---: |
| Working tree matches the Git blob | 2,620 |
| Working tree matches the `core.autocrlf=true` smudge | 41 |
| Mixed line endings; neither Git form matches | 2 |

The two mixed files are the same two `METADATA` paths. No third reconstruction discrepancy appeared.

## E. Recovery Archive

| Item | Value |
| --- | --- |
| Path | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\ashen_thrones_phase2c_tracked_venv_broken_20261031.zip` |
| Compressed size | 7,535,019 bytes |
| SHA-256 | `9e98d345d5e6495afcb581b180526b3ecfcc788d1f2381df239b479b2881fd45` |
| Entries | 2,663 regular files |
| Same physical disk as the repository | Yes, `C:` |
| Independent backup | No. This is a same-disk recovery copy |

The archive was written as a `.partial` file and renamed only after every entry's path, uncompressed size, and SHA-256 matched the recovery manifest. `testzip` passed. Names are repository-relative. None is absolute, and none contains `..`. The manifest, the active `.venv/`, the separate `venv/`, and the earlier archives are not inside this zip.

The published archive was then extracted outside the repository:

| Check | Result |
| --- | --- |
| Extracted files | 2,663 |
| Extracted logical bytes | 24,397,647 |
| Paths versus the manifest | Exact set match |
| SHA-256 versus the working tree | 2,663 of 2,663 |
| Both mixed `METADATA` files | Exact working-tree hashes |

The extraction directory was removed. The published archive was opened again. `testzip` passed, the entry count was still 2,663, and the SHA-256 was unchanged. The same hash and `testzip` result were confirmed again after the commit. The source files were still present until the later deletion step.

Recovery: unzip so each entry lands at its repository-relative path. That restores the working-tree bytes, including the mixed line endings. Checking the parent commit back out does not restore those two files exactly, because Git still has only the LF blobs.

## F. Deletion and Commit

Removal used `os.remove` on the manifest paths, in manifest order. Immediately before each removal the path was inside `.venv-broken/`, it was a regular file, it was not a reparse point, the index still listed it at the manifest mode and object id, and its size and SHA-256 matched the manifest. No wildcard, `git clean`, recursive directory delete, or history rewrite was used.

| Result | Value |
| --- | --- |
| Files removed | 2,663 |
| Logical bytes removed | 24,397,647 |
| Files that failed verification | 0 |
| Partial deletion | No |
| `.venv-broken/` files remaining | 0 |
| `.venv-broken/` directories remaining | 464, including the root |

Empty directories were left in place.

The staged diff, checked before the commit, contained 2,663 deletions and nothing else. There were no additions, modifications, or renames. Every staged path was under `.venv-broken/`. Every deleted index object id was the object id recorded from the original `HEAD`. The unstaged tracked diff was empty. Reports and manifests were not staged.

| Item | Value |
| --- | --- |
| Commit SHA | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Subject | `chore: remove tracked obsolete virtual environment` |
| Parent | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Commit diff | 2,663 deletions, 0 additions, 0 modifications |
| Paths outside `.venv-broken/` | 0 |

`git diff --name-status HEAD^ HEAD` after the commit was the same 2,663 deletions. `git show --shortstat` reports 2,663 files changed and 589,604 deleted lines. That line count is Git's text diff. The logical file-byte total is 24,397,647.

## G. Preservation

Protected content was fingerprinted before deletion and compared again after deletion, before the commit. The commit did not change any other work-tree file.

| Check | Result |
| --- | --- |
| Active `.venv/` | Present. 5,951 files, 56,291,644 bytes, same fingerprint as the pre-deletion baseline. `pyvenv.cfg` still creates `.venv` |
| Separate `venv/` | Present. 5,390 files, 49,494,117 bytes, same fingerprint. Not the deletion target |
| `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, `experiments/` | Same file counts, byte totals, and content fingerprints |
| `artifacts/atgb/` | Same fingerprint |
| `artifacts/pr_eg_r6_r5/snapshots/` | Same fingerprint |
| `handoff/CURRENT_REVIEW.zip` | Same size and SHA-256 |
| `development/tmp/github_checkpoint/` | Same fingerprint |
| `development/tmp/storage_cleanup_phase1_control/` | Same fingerprint |
| Earlier cleanup reports and manifests | Same size and SHA-256, including the original Phase 2C report |
| Earlier external archives | Same size and SHA-256 |
| Unexpected tracked changes | None |
| Provider or API calls | None |
| Game, AI-DM, or regression suite | Not run |

The earlier archives remain:

| Archive | Size | SHA-256 |
| --- | ---: | --- |
| `ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` | 19,722,751 | `7df6f3a68feba8e3130de20ae98505601290327ffcac532a4a72d21a5ffd7740` |
| `ashen_thrones_phase2b_c3_checkpoint_4320bcd_20261031.zip` | 75,223,700 | `1f87961a5dca24047b8188c095dbcd01edbf6fc9fa7b035da9275f07796fb894` |
| `ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` | 37,865,504 | `fde74bd409eccc806e48db825c80b29e398c15c8a182638fc771f4b80eb3c858` |

No current launcher, test, workflow, or IDE interpreter setting selects `.venv-broken/`. `scripts/run_live_playtest.ps1` selects `.venv/Scripts/python.exe`. GitHub workflows install `requirements.txt` with `setup-python` 3.12. `.idea/misc.xml` selects the Python 3.9 SDK for the separate `venv/` tree. `VIRTUAL_ENV` was empty, and no process executable was running from `.venv-broken/`. Remaining mentions are historical records and cleanup exclusion lists.

## H. Storage Impact

| Metric | Change |
| --- | --- |
| Working-tree logical bytes removed | 24,397,647 |
| Recovery archive size | 7,535,019 |
| Net local disk-space recovery | 16,862,628 |
| Git object storage | Unchanged by this operation. No garbage collection and no history rewrite. The blobs remain reachable from the parent commit |
| GitHub storage | Unchanged. No push. A later push would upload this commit's tree, and the historical blobs would still be stored because the parent commit still points at them |

The working-tree reduction is the sum of the deleted file lengths. Net local recovery subtracts the new archive. Both figures are logical file bytes. Cluster slack is not included. Empty directories have no file bytes.

Do not treat this commit as deletion of the historical Git blobs. They are still in `e86fd4512028af4ce698090d48c1b672dd68600c`.

## I. Remaining Candidates

Not touched in this pass.

| Candidate | What it is | Notes |
| --- | --- | --- |
| C3 duplicate ZIP excess | Extra working-tree copies | Phase 2B-C4 recorded 66,621,016 excess bytes outside the current review trio. Not started |
| C4 leftovers | `venv/`, PR-PLAY overlays, other `development/tmp` material, `disposable_state/`, orphan bytecode | Phase 2 recorded 144,053,732 bytes. Not classified here as safe to delete. `.idea` still selects the Python 3.9 SDK |
| Active `.venv/` | Documented interpreter | 5,951 files, 56,291,644 bytes. Retained |
| Empty `.venv-broken/` directories | Directory shells after this deletion | 464 directories, 0 files |
| Empty `development/tmp/maintenance_ci_venv/` | Directory shell from Phase 2B-C4 | No file content |
| Checkpoint sibling diagnostics | Files beside the removed baseline checkout | Left in place |
| `development/tmp/storage_cleanup_phase1_control/` | Phase 1 evidence | Protected |
| `.git/cursor/` | Local IDE index | Not a deletion target |

## J. Recommendation

Phase 2C can be closed. The tracked obsolete environment is no longer in `HEAD` or the work tree. The exact working-tree bytes, including both mixed-line-ending files, are in the external archive, and that archive passed a full extraction and SHA-256 check before anything was deleted.

The commit `9f6a008837438b6a9b3128b31e2cd178c7f19e90` is ready for review. It is one commit ahead of `origin/feature/product-realization`. It has not been pushed. Review the commit before any push. The archive's same-disk limit should be part of that review: it does not protect against loss of drive `C:`.

Do not start another cleanup phase from this report. Duplicate ZIP copies, the separate `venv/` tree, and the other historical leftovers stay where they are until a later pass is explicitly authorized. Active `.venv/` stays.

The recovery manifest is `artifacts/storage_cleanup_phase2c_recovery_manifest.json`. It was written at `2026-11-01T07:01:25-05:00`, before the archive and before the deletion. It lists all 2,663 paths with size, working-tree SHA-256, Git object id, file mode, and recovery classification.
