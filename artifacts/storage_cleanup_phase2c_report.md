# Ashen Thrones — Storage Cleanup Phase 2C

Status: **FAIL**. No tracked file was deleted. No commit was created. Nothing was pushed.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

The deletion stopped at recovery verification. The tracked inventory matches Phase 2B-C4, and Git can reproduce 2,661 of the 2,663 working-tree files exactly. Two `METADATA` files contain a mix of CRLF and LF lines. Their Git blobs are LF only. A normal checkout converts every LF to CRLF. Neither form is the working-tree bytes, and Git does not store which lines currently carry the extra CR. Those two files were left in place, and the rest of `.venv-broken/` was left in place with them.

`artifacts/storage_cleanup_phase2c_manifest.json` was not written. There is no approved deletion list.

## A. Executive Summary

| Item | Result |
| --- | --- |
| Status | **FAIL** |
| Deletion occurred | No |
| Commit created | No |
| Pushed | No |

The stop condition was exact reconstruction. The other gates that ran before that check passed.

## B. Repository State

Confirmed before any reconstruction, and again after the stop.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| Original HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Final HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Remote-tracking ref | `origin/feature/product-realization` |
| Remote-tracking HEAD | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| HEAD tree | `60bf2b46a306c16a5e2822f2f9195540f4e05eb0` |
| Merge, rebase, cherry-pick, or bisect | None in progress |
| Staged changes | None |
| Unstaged tracked changes | None |
| `core.autocrlf` | `true` |
| `.gitattributes` | None |

Untracked files present at the start were the earlier storage-cleanup reports and manifests. They were left untracked. This report is an additional untracked file.

## C. Inventory

The Phase 2 audit and the Phase 2B-C4 report both record 2,663 tracked files and 24,397,647 bytes under `.venv-broken/`. The Phase 2B-C4 manifest stores a path, size, and SHA-256 for each of those files in `tracked_files_excluded`.

Fresh inventory, compared path by path with that preserved list:

| Set | Files | Logical bytes | Match |
| --- | ---: | ---: | --- |
| Expected | 2,663 | 24,397,647 | — |
| `git ls-files` under `.venv-broken/` | 2,663 | 24,397,647 | Yes |
| On-disk regular files under `.venv-broken/` | 2,663 | 24,397,647 | Yes |
| Working-tree SHA-256 versus Phase 2B-C4 | 2,663 of 2,663 | — | Yes |

Every candidate is tracked, stage 0, and present in `HEAD` with the same mode and object id. Every path is beneath `.venv-broken/`. None is a symbolic link or reparse point. None has a staged or unstaged Git diff. `git diff` is empty for these paths, including the two files that fail exact reconstruction, because `core.autocrlf=true` strips CR before it compares them with the index.

No ignored or untracked file is inside `.venv-broken/`. The ignored files removed in Phase 2B-C4 are still absent.

## D. Recovery

Recovery commit, if a later checkout is authorized: `e86fd4512028af4ce698090d48c1b672dd68600c`.

Recovery tree: `60bf2b46a306c16a5e2822f2f9195540f4e05eb0`.

Object check: `git cat-file --batch-check` read all 2,663 index objects as blobs.

Reconstruction was performed outside the repository and then removed. It did not write into the work tree.

1. `git -c core.autocrlf=false checkout-index` restored blob bytes for every candidate. **2,620** files matched the working-tree size and SHA-256.
2. The other **43** files are larger on disk than their blobs. `checkout-index` with the repository's `core.autocrlf=true` setting was applied to those 43 only. **41** matched the working tree exactly. **2** did not.

The 43 size differences are line endings, not a second copy of the source. Thirty are `RECORD` files. The rest are `METADATA`, `LICENSE`, a few pydantic/jiter sources, the venv activation scripts, and `pyvenv.cfg`. For the 41, the working tree is the CRLF smudge of an LF blob, and that smudge was reproduced outside the repository.

The two failures are mixed. The blob is LF on every line. The working tree keeps LF on some lines and CRLF on others. Smudge turns every line into CRLF, which is larger than the working tree. The clean filter turns the mix back into the LF blob, which is why Git does not report a modification.

| Path | Working tree | Git blob | Autocrlf smudge |
| --- | ---: | ---: | ---: |
| `.venv-broken/Lib/site-packages/jiter-0.13.0.dist-info/METADATA` | 5,348 bytes; 112 CRLF and 33 LF | 5,236 bytes; 145 LF | 5,381 bytes |
| `.venv-broken/Lib/site-packages/pydantic_core-2.41.5.dist-info/METADATA` | 7,420 bytes; 143 CRLF and 37 LF | 7,277 bytes; 180 LF | 7,457 bytes |

Line-by-line, every difference between each working-tree file and its blob is a CR on a line whose blob form ends in LF. No other byte differs. Which lines have that CR is not in the blob, so Git cannot rebuild these two files exactly. The text those blobs do contain is still in `e86fd4512028af4ce698090d48c1b672dd68600c`.

One checkout setting cannot reproduce the whole tree. `core.autocrlf=false` preserves the 2,620 LF files and drops the CR from the other 43. The default `core.autocrlf=true` checkout preserves the 41 fully converted files and rewrites the 2,620 LF files, and it still does not reproduce the two mixed files.

The Phase 2B-C4 archive was not modified. It still does not contain tracked `.venv-broken` files.

| Item | Value |
| --- | --- |
| Path | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` |
| Size | 37,865,504 bytes |
| SHA-256 | `fde74bd409eccc806e48db825c80b29e398c15c8a182638fc771f4b80eb3c858` |

That hash is the hash recorded in the Phase 2B-C4 report.

## E. Deletion and Commit

No file was deleted. No path was staged. No commit was created.

| Item | Value |
| --- | --- |
| Files deleted | 0 |
| Logical bytes removed | 0 |
| Commit SHA | None |
| Staged diff | Empty |

## F. Preservation

No application file, active environment, archive, or historical tree was edited. The operation wrote only this untracked report.

| Check | Result |
| --- | --- |
| Active `.venv/pyvenv.cfg` | Present. Interpreter command creates `.venv` with Python 3.12.0 |
| `.venv-broken/` | Still the 2,663 tracked files |
| `.github/`, `scripts/`, `tools/`, `tests/`, `game/` | No reference to `.venv-broken` |
| `scripts/run_live_playtest.ps1` | Selects `.venv/Scripts/python.exe` |
| `.idea/misc.xml` | Project SDK `Python 3.9 (ashen_thrones_ai_gm)`, the separate `venv/` tree |
| `pytest.ini`, `Makefile`, `requirements.txt` | No reference to `.venv-broken` |
| Process using `.venv-broken` | None |
| `VIRTUAL_ENV` | Empty |

Historical mentions of `.venv-broken` remain in earlier cleanup reports, the repository organization note, and the PR-AB campaign note. They are records, not launchers. They were not modified.

`game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, `experiments/`, ATGB, golden replay, PR-PLAY evidence, `artifacts/pr_eg_r6_r5/snapshots/`, `development/tmp/github_checkpoint/`, and `development/tmp/storage_cleanup_phase1_control/` were not part of the deletion set and were not changed. `venv/` and `.git/cursor` were not changed.

## G. Storage Impact

| Metric | Change |
| --- | --- |
| Working-tree bytes removed | 0 |
| `.git` object storage | Unchanged. No commit, no repack, no prune |
| GitHub storage | Unchanged. No push |

The 24,397,647 tracked bytes are still in the work tree and still in Git history.

## H. Next Steps

Phase 2C did not remove `.venv-broken/`. Any later attempt needs an explicit decision about the two mixed `METADATA` files. Until then they stay on disk.

These other candidates were not opened for cleanup:

* Duplicate ZIP archives from the C3 class.
* Historical leftovers from the C4 class, including `venv/`.
* The active `.venv/`.
* Tracked pytest working stores already removed in the earlier commit remain removed. Further scratch trees, if any remain in later audits, were not revisited here.

No push is pending for this phase because no commit was created.

## Environment check detail

The active environment and the obsolete tree are different installs that share a base interpreter. `.venv/pyvenv.cfg` records `python -m venv` of `.venv`. `.venv-broken/pyvenv.cfg` records the same base interpreter and a create command for `.venv`; it is a renamed earlier environment. No current workflow, script, test, game module, or IDE interpreter setting points at `.venv-broken`.
