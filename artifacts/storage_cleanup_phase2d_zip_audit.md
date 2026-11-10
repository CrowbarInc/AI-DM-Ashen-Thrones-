# Ashen Thrones — Storage Cleanup Phase 2D

Status: **PASS WITH CAVEATS**. The Phase 2C commit is on `origin/feature/product-realization`. The repository ZIP audit is complete. No ZIP was deleted, moved, or modified.

Date: November 1, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

This report and `artifacts/storage_cleanup_phase2d_zip_inventory.json` are untracked investigative artifacts. They are not a deletion authorization.

## A. Executive Summary

| Item | Result |
| --- | --- |
| Audit result | **PASS WITH CAVEATS** |
| Git synchronization | Fast-forward push succeeded. Local and remote HEAD are `9f6a008837438b6a9b3128b31e2cd178c7f19e90`. Ahead/behind is 0/0. |
| ZIP inventory | 431 files, 260,537,941 bytes. 423 tracked, 8 ignored, 0 untracked. |
| Exact-duplicate excess | 34 groups, 70,680,001 excess bytes |
| Logical duplicates | 0 groups |
| Strong deletion scope (D1) | 4 ignored files, 1,125,262 bytes |
| Conditional scope (D2) | 20 files, 30,679,686 bytes |
| Retained (D3) | 407 files, 228,732,993 bytes |
| Uncertain (D4) | 0 |

The earlier 66,621,016-byte figure is real excess from the Phase 2 measurement, after removing the protected PR-PLAY-12 trio, and it reconciles exactly with this inventory. It is not a safe deletion amount. Most of those bytes are campaign history packages, protected PR-PLAY and ATGB copies, or timestamped handoff snapshots that still have a distinct path.

Recommendation: do not delete from the 66,621,016 figure. If a later phase is explicitly authorized, limit it to the four ignored D1 ZIPs, leave their sibling markdown and manifest files in place, and keep every preservation copy named below. Tracked staging copies and older timestamped handoff ZIPs stay until the conditions in the candidate table are accepted. That later phase should be separate from any commit.

Caveats:

- One D1 preservation copy, `handoff/CURRENT_REVIEW(20261019-181208).zip`, is the only tracked copy of that hash.
- Each D1 directory also holds `CURRENT_REVIEW.md` and `REVIEW_MANIFEST.json`. Those files were not classified.
- The external recovery archives sit on the same disk as the repository. They are not an independent backup.
- Deleting a tracked ZIP in a normal commit does not remove its Git blob while another path or an ancestor commit still points at it.

## B. Git Synchronization

Preflight matched the authorized Phase 2C commit before the push.

| Check | Result |
| --- | --- |
| Branch | `feature/product-realization` |
| Starting local HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Parent | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Subject | `chore: remove tracked obsolete virtual environment` |
| Merge, rebase, cherry-pick, or bisect | None |
| Staged or unstaged tracked changes | None |
| Commit contents | 2,663 deletions, all status `D`, all under `.venv-broken/` |
| Recovery archive | `ashen_thrones_phase2c_tracked_venv_broken_20261031.zip` |
| Archive SHA-256 | `9e98d345d5e6495afcb581b180526b3ecfcc788d1f2381df239b479b2881fd45` |
| Archive readability | Opened read-only. 2,663 members, payload read to completion. |

Fetch of `origin` (`https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-.git`) left `origin/feature/product-realization` at `e86fd4512028af4ce698090d48c1b672dd68600c`. That commit is the parent of local HEAD, so the push was a fast-forward. No unexpected remote commits were present.

Push result: `e86fd451..9f6a0088  feature/product-realization -> feature/product-realization`.

| Check after push | Result |
| --- | --- |
| Local HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Remote HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Ahead / behind | 0 / 0 |
| Tracked worktree changes | None |
| Pre-existing untracked cleanup reports | Same set as before the push |

No force-push, amend, new commit, or garbage collection was run.

## C. Inventory Methodology

Search scope: every regular file whose name ends in `.zip` under the repository, including ignored files. `.git` was not walked. The three virtual-environment directories were included in the walk and contained no ZIP files. External storage-cleanup archives were opened for context and are excluded from the deletion classes.

Hashing: SHA-256 of each ZIP's file bytes. For each distinct file hash, every member was streamed and hashed. The payload fingerprint is the SHA-256 of sorted lines `path`, uncompressed size, and member SHA-256. A second sorted central-directory fingerprint uses path, uncompressed size, and CRC-32. Duplicate copies of a file hash were opened and their sorted central-directory fingerprints were compared with the first copy.

Integrity: `zipfile.testzip()` was run on all 431 repository ZIPs. No bad member was returned. An early unsorted CRC comparison flagged two `evidence.zip` copies; that comparison was wrong, and the recheck cleared both. No archive is corrupt.

Logical comparison: two ZIPs are logical duplicates when the payload fingerprint matches and the file hash does not. That means the same uncompressed members with different ZIP metadata or compression. Same member names with a different payload fingerprint are different versions. Review packages whose member-name Jaccard is at least 0.80, and whose file hashes differ, are overlaps.

Git bytes: for all 423 tracked ZIPs, `git hash-object --no-filters` matched the index blob id. The worktree was clean. Those working-tree bytes are the Git blobs. No line-ending conversion applies to them.

References: the 79 paths that participate in an exact-duplicate group were searched as full relative paths, with both slash directions, across 48,437 text files. Basenames `REVIEW.zip`, `CURRENT_REVIEW.zip`, and `evidence.zip` were not treated as references, because they match many unrelated files. Timestamped basenames were searched. Six JSON files larger than 30 MB were omitted from the bulk read. A separate search for the candidate directory names did not find those names in them. Hits under `tests/`, `game/`, `tools/`, `scripts/`, `experiments/`, `.github/`, `docs/`, `development/campaigns/`, and top-level handoff markdown were classified ACTIVE. Hits under `artifacts/storage_cleanup*` were classified as audit citations. Other hits were HISTORICAL.

No ZIP timestamp or byte was intentionally changed. Inspection was read-only.

## D. Duplicate Findings

### Exact duplicates

34 groups, 79 files, 70,680,001 excess bytes (45 extra copies). 352 ZIPs have a unique file hash.

The largest groups:

| Copies | Excess bytes | What the copies are |
| ---: | ---: | --- |
| 3 | 15,081,628 | PR-EG-R2C-R1 history package, plus a review-staging copy and a predecessor copy under `artifacts/` |
| 2 | 8,229,096 | Two `handoff/history/` packages for PR-EG-R4-R1 and the PR-EG-R5 predecessor |
| 3 | 7,593,952 | `handoff/CURRENT_REVIEW.zip`, `handoff/CURRENT_REVIEW(20261031-141539).zip`, and `handoff/history/pr_play_12/REVIEW.zip` |
| 2 | 6,598,350 | PR-EG-R5 history package and `artifacts/pr_eg_r5/package_staging/CURRENT_REVIEW.zip` |
| 2 | 5,289,542 | Two `handoff/history/` packages for PR-EG-R4 and its before-R1 alias |

Every ignored ZIP is an exact copy of a tracked ZIP. The full group list, hashes, and member fingerprints are in the inventory.

### Logical duplicates

Zero. No two ZIPs share uncompressed member hashes while differing in ZIP metadata or compression.

### Overlapping archives

Eleven `evidence.zip` groups share an identical member-name list and differ in every payload hash. The largest is 60 ATGB automated-playtest archives. They are different runs with the same archive shape. They are D3.

Nine review-package pairs have member-name Jaccard of at least 0.80 and different file hashes. The closest pair is `handoff/CURRENT_REVIEW(20261019-070553).zip` and `handoff/CURRENT_REVIEW(20261019-070606).zip`: 113 shared names, one extra member in the earlier file. The other pairs are successive ATGB history packages (`atgb_03` / `atgb_03a`, `atgb_04` / `atgb_05` / `atgb_05a`, and the two constitution-governance packages). Those are different versions. Both sides stay.

### Unique archives

352 ZIPs have no exact duplicate. They include the rest of the ATGB playtest evidence, human-playtest archives, and historical review packages that were never copied. They are D3.

### Names that only look alike

`evidence.zip` occurs 278 times. `REVIEW.zip` occurs 93 times. `CURRENT_REVIEW.zip` occurs 26 times. Shared names were not treated as duplication. Classification used file hashes and member hashes.

## E. Dependency and Recovery Findings

### Active references

No exact-duplicate path is opened by `tests/`, `game/`, `tools/`, current `docs/`, or CI. `handoff/CURRENT_REVIEW.zip` is the active package: current report scripts and `docs/NEXT_SESSION.md` name it. That file is the preservation copy of the PR-PLAY-12 trio, and it is D3.

Historical campaign scripts name some temporary directories. Those scripts live under `artifacts/` and are classified HISTORICAL, with the effect recorded on the D2 rows:

- `artifacts/pr_eg_r5/build_reports.py` opens `package_staging/CURRENT_REVIEW.zip`.
- `artifacts/pr_play_03/package.py` builds into `development/tmp/pr_play_03/review_stage` and then reads `CURRENT_REVIEW.zip` there.
- `artifacts/atgb/atgb_r1_09/package_review.py` writes `development/tmp/atgb_r1_09_export` and then reads the ZIP.
- `artifacts/atgb/atgb_r2_01/finalize_review.py` and `artifacts/atgb/atgb_r1_04/package_review.py` copy a handoff ZIP into a temporary backup only when that file is absent.

### Historical references

Most other hits are git-status captures (`repository_status_*.txt`, `entry_status.txt`, checkpoint file lists) and the earlier storage-cleanup audits. They record that a path existed. They do not load the archive.

`handoff/history/<campaign>/REVIEW.zip` is the campaign-local package. Where two history directories hold the same bytes, each directory remains a citation target. Those copies are D3.

### Recoverability

All 423 tracked ZIPs match their Git blobs byte for byte, verified with `git hash-object --no-filters` against the index. `git cat-file blob HEAD:<path>` reproduces those files. The 8 ignored ZIPs are not Git paths. Each one's bytes match a tracked ZIP, so the content is recoverable from that tracked blob. Restoring the ignored path is a copy from the tracked file, not a checkout of the ignored path.

A same-disk archive is not an independent backup. The four external recovery ZIPs do not contain the current review-package duplicate groups as nested members. The Phase 2B-C3 checkpoint archive contains 14 historical ZIPs from the removed `baseline_4320bcd` checkout. Thirteen of those hashes are still in the working tree. The remaining file, 6,286 bytes, SHA-256 `fc07954a8ebc2e176425a8a9657bca8d7358d5692a7298f850677addaac1fac3`, matches the blob `4320bcdd50471c744746811f213a60b1893496d2:handoff/CURRENT_REVIEW.zip`.

### Protected evidence

Kept as D3 even where another exact copy exists:

- `handoff/CURRENT_REVIEW.zip`, `handoff/CURRENT_REVIEW(20261031-141539).zip`, and `handoff/history/pr_play_12/REVIEW.zip`
- PR-PLAY 10 and 11 history packages and their timestamped handoff snapshots `CURRENT_REVIEW(20261030-212347).zip` and `CURRENT_REVIEW(20261030-222931).zip`
- `artifacts/pr_play_10/`, `artifacts/pr_play_11/`, and `artifacts/pr_play_12/` archives, including the two `evidence.zip` files that are byte-identical to ATGB automated-playtest runs
- `artifacts/atgb/` and `handoff/history/atgb*`
- Every `handoff/history/` package, including predecessor aliases

No ZIP in this inventory is under `artifacts/pr_eg_r6_r5/snapshots/`, a source-snapshot directory, Phase 1 control evidence, or `data/`. Golden-replay evidence was not found in ZIP form. External recovery archives are protected and are not candidates.

## F. Candidate Table

Preservation copies below are D3 and have the same SHA-256 as the candidate. Sibling `CURRENT_REVIEW.md` and `REVIEW_MANIFEST.json` files are outside this table.

| Path | Size | Class | Preservation copy | References | Rationale |
| --- | ---: | --- | --- | --- | --- |
| `development/tmp/atgb_r1_07_export/CURRENT_REVIEW.zip` | 280,133 | D1 | `handoff/history/atgb_r1_07/REVIEW.zip` | UNREFERENCED | Ignored exact copy. The tracked history package retains the bytes. |
| `development/tmp/atgb_r1_07_export/history/atgb_r1_07/REVIEW.zip` | 280,133 | D1 | `handoff/history/atgb_r1_07/REVIEW.zip` | UNREFERENCED | Second ignored copy of that same package. |
| `development/tmp/atgb_r2_04_prior_handoff/CURRENT_REVIEW.zip` | 296,696 | D1 | `handoff/history/atgb_r2_03/REVIEW.zip` | UNREFERENCED | Ignored exact copy of the ATGB-R2-03 history package. |
| `development/tmp/pr_play_02_previous_handoff/CURRENT_REVIEW.zip` | 268,300 | D1 | `handoff/CURRENT_REVIEW(20261019-181208).zip` | UNREFERENCED | Ignored exact copy. The timestamped handoff file is the only tracked copy and must remain. |
| `artifacts/pr_eg_r2c_r1/review_staging/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip` | 7,540,814 | D2 | `handoff/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip` | HISTORICAL | Tracked staging copy. Named by old git-status captures and cleanup audits. Needs confirmation that the staging tree is retired, then its own commit. |
| `artifacts/pr_eg_r2c_r2/predecessor_current_review/CURRENT_REVIEW.zip` | 7,540,814 | D2 | `handoff/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip` | HISTORICAL | Tracked predecessor copy. `artifacts/pr_eg_r2c_r2/build_review.py` creates this directory. Same confirmation and commit requirement. |
| `artifacts/pr_eg_r5/package_staging/CURRENT_REVIEW.zip` | 6,598,350 | D2 | `handoff/history/pr_eg_r5_conversational_architecture_reassessment_20261017/REVIEW.zip` | HISTORICAL | `artifacts/pr_eg_r5/build_reports.py` opens this path. Retire or retarget that script before deletion. |
| `artifacts/pr_eg_r6_r2/predecessor_review/CURRENT_REVIEW.zip` | 154,098 | D2 | `handoff/history/pr_eg_r6_r1_r1_provenance_20261017/REVIEW.zip` | HISTORICAL | Tracked predecessor copy named by historical status captures. |
| `development/tmp/pr_play_03/review_stage/CURRENT_REVIEW.zip` | 1,309,957 | D2 | `handoff/history/pr_play_03/REVIEW.zip` | HISTORICAL | `artifacts/pr_play_03/package.py` builds this directory and reads the ZIP. `build_result.json` records the path. |
| `development/tmp/atgb_r1_09_export/CURRENT_REVIEW.zip` | 514,815 | D2 | `handoff/CURRENT_REVIEW(20261019-070606).zip` | HISTORICAL | Staging output read by `artifacts/atgb/atgb_r1_09/package_review.py` after it writes the directory. |
| `development/tmp/atgb_r2_01/preexisting_handoff/CURRENT_REVIEW.zip` | 514,815 | D2 | `handoff/CURRENT_REVIEW(20261019-070606).zip` | HISTORICAL | Copy-if-absent backup in `finalize_review.py`. Deleting the file would change a rerun. |
| `development/tmp/atgb_r1_04_previous_review/CURRENT_REVIEW.zip` | 343,283 | D2 | `handoff/history/atgb_r1_03_controlled_live_validation/REVIEW.zip` | HISTORICAL | Copy-if-absent backup in `artifacts/atgb/atgb_r1_04/package_review.py`. |
| `handoff/CURRENT_REVIEW(20261018-215535).zip` | 266,925 | D2 | `handoff/history/atgb_r1_02_mechanical_revision_boundary/REVIEW.zip` | HISTORICAL | Timestamped handoff snapshot. Status captures list the filename. Confirm the history package replaces that citation. |
| `handoff/CURRENT_REVIEW(20261019-051157).zip` | 343,283 | D2 | `handoff/history/atgb_r1_03_controlled_live_validation/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-062339).zip` | 280,133 | D2 | `handoff/history/atgb_r1_07/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-064632).zip` | 243,817 | D2 | `handoff/history/atgb_r1_08/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-073308).zip` | 1,245,143 | D2 | `handoff/history/atgb_r2_01/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. `review_verification.json` names it. |
| `handoff/CURRENT_REVIEW(20261019-075507).zip` | 72,306 | D2 | `handoff/history/atgb_r2_02/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-173603).zip` | 296,696 | D2 | `handoff/history/atgb_r2_03/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-175928).zip` | 437,011 | D2 | `handoff/history/atgb_r2_04/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261019-182836).zip` | 590,583 | D2 | `handoff/history/pr_play_02/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261026-204131).zip` | 1,309,957 | D2 | `handoff/history/pr_play_03/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261026-211119).zip` | 139,024 | D2 | `handoff/history/pr_play_04_opening_failure_acceptance/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |
| `handoff/CURRENT_REVIEW(20261027-042122).zip` | 937,862 | D2 | `handoff/history/pr_play_05/REVIEW.zip` | HISTORICAL | Same timestamped-snapshot condition. |

D1 total: 1,125,262 bytes, all ignored. D2 total: 30,679,686 bytes, of which 27,996,816 are tracked and 2,682,870 are ignored.

## G. Storage Impact

| Metric | Bytes or count |
| --- | ---: |
| ZIP files in the repository | 431 |
| Logical bytes occupied by those ZIPs | 260,537,941 |
| Tracked ZIP bytes | 256,729,809 (423 files) |
| Ignored ZIP bytes | 3,808,132 (8 files) |
| Untracked ZIP files | 0 |
| Exact-duplicate groups | 34 |
| Excess exact copies | 70,680,001 |
| Logical-duplicate groups | 0 |
| D1 potential working-tree savings | 1,125,262 |
| D2 conditional working-tree savings | 30,679,686 |
| Bytes retained in D3 | 228,732,993 |
| Bytes retained in D4 | 0 |
| Exact excess that remains inside D3 copies | 38,875,053 |

D1 and D2 savings count each candidate once. Preservation copies are in D3 and are not also counted as savings. The 38,875,053 figure is duplicate excess that this audit keeps: history-to-history aliases, the PR-PLAY 10/11/12 snapshots, and other protected copies.

### Reconciliation with 66,621,016

Phase 2 measured 457 ZIPs, 264,262,393 bytes, 47 exact groups, and 74,214,968 excess bytes. The protected PR-PLAY-12 trio contributed 7,593,952 of that excess. 74,214,968 − 7,593,952 = 66,621,016.

Since that measurement, 26 ZIPs have left the worktree:

| Source | Files | Bytes | Effect on excess |
| --- | ---: | ---: | --- |
| Phase 2A, tracked `artifacts/pr_eg_r6_r4_r1/focused_tmp/` fixtures, commit `e86fd451` | 12 | 896,583 | Extra copies of hashes that still exist, plus four hashes that remain in Git history |
| Phase 2B-C3, ignored checkpoint checkout, now in the external C3 archive | 14 | 2,827,869 | Extra copies of hashes that still exist, plus the 6,286-byte file that matches commit `4320bcd` |

26 files and 3,724,452 bytes. Current inventory 431 files and 260,537,941 bytes. 264,262,393 − 3,724,452 = 260,537,941. The unexplained byte delta is 0.

Excess fell by 3,534,967, to 70,680,001. Current excess outside the still-present PR-PLAY-12 trio is 63,086,049. 66,621,016 − 63,086,049 = 3,534,967. The unexplained excess delta is 0.

The 88-copy group in the original storage-cleanup appendix (`4149ca96…`, 7,913,085 excess bytes, under `development/tmp/pr_play_11_export_atgb_1793413643850655500/`) is not part of this delta. Those directories exist and contain no files. They were already absent from the Phase 2 total, because that total reconciles without them.

### Working tree and Git storage

D1 savings are ignored working-tree bytes. Git has no blob under those paths. The bytes remain available from the tracked preservation copies.

D2 tracked savings would be a future checkout reduction after an ordinary commit. The blobs would remain reachable from the preservation paths and from history. GitHub object storage would not shrink. D2 ignored savings are local only.

No row above is a Git repository storage saving.

## H. Risks and Uncertainties

- `handoff/CURRENT_REVIEW(20261019-181208).zip` is the sole tracked preservation copy for one D1 file. Removing that timestamped file later would leave the ignored copy as the only worktree copy.
- D1 directories also contain the review markdown and manifest. Those files may be the convenient unpacked form of the package. This audit did not hash them against the preservation ZIP's members. Phase 2E must leave them in place.
- Historical packagers still name several D2 paths, including one script that opens the staging ZIP and two scripts whose backup step runs only when the file is missing.
- Timestamped `handoff/CURRENT_REVIEW(…).zip` files are cited by campaign status captures. Those captures are historical. They are still the filenames a person would have opened on that date.
- No corrupt ZIP was found.
- The bulk reference scan skipped six JSON files over 30 MB. Targeted search did not find the D1 or staging directory names there. A reference buried only inside one of those payloads would have been missed.
- External recovery archives are on drive `C:` with the repository. Losing the disk loses both.
- Campaign history aliases are exact duplicates and are still the package for that campaign directory. Deleting one would break that directory's review package even though the bytes exist elsewhere.
- `handoff/CURRENT_REVIEW(20261019-070553).zip` differs from the 070606 snapshot by one member. It is a different version and stays.

## I. Proposed Phase 2E

Do not start Phase 2E from this report. The proposal is the scope to authorize later, if at all.

### Exact deletion scope

Only these four ignored files:

- `development/tmp/atgb_r1_07_export/CURRENT_REVIEW.zip`
- `development/tmp/atgb_r1_07_export/history/atgb_r1_07/REVIEW.zip`
- `development/tmp/atgb_r2_04_prior_handoff/CURRENT_REVIEW.zip`
- `development/tmp/pr_play_02_previous_handoff/CURRENT_REVIEW.zip`

Expected working-tree reduction: 1,125,262 bytes. No other file, including sibling markdown and manifests, and no directory removal.

### Required preservation steps

- Recompute SHA-256 of each file and of its preservation copy immediately before deletion. Both must match this inventory.
- The preservation copies listed in the candidate table must still be present.
- `handoff/CURRENT_REVIEW(20261019-181208).zip` must remain. It is the only tracked copy of that package.
- Leave `CURRENT_REVIEW.md` and `REVIEW_MANIFEST.json` in those directories.
- Do not delete D2 files in that phase.

### Verification gates

- ZIP count falls by 4, from 431 to 427.
- Logical ZIP bytes fall by 1,125,262.
- The four preservation paths still exist and keep their recorded hashes.
- Sibling markdown and manifest files still exist.
- `git status` shows no tracked modification.
- No Git commit, garbage collection, or push.

### Tracked files

The four D1 paths are ignored. Phase 2E does not need a commit. Tracked D2 files, 27,996,816 bytes, need a later ordinary commit of their own, and only after the script and citation conditions in the table are accepted. That commit would not shrink existing Git object storage.

### Subdivision

Split any later cleanup:

1. Phase 2E, only the four ignored D1 ZIPs, if authorized.
2. A separate decision for ignored D2 backups whose scripts use a copy-if-absent guard (`atgb_r1_04`, `atgb_r1_09`, `atgb_r2_01`, and the PR-PLAY-03 stage).
3. A separate ordinary commit, if ever authorized, for tracked staging copies. `artifacts/pr_eg_r5/package_staging/CURRENT_REVIEW.zip` stays until `build_reports.py` no longer opens it.
4. Timestamped `handoff/CURRENT_REVIEW(…).zip` files stay out of those deletions. They are citation names, and the PR-PLAY 10, 11, and 12 snapshots are protected.

No deletion manifest was written.
