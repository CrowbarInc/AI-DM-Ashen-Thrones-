# Ashen Thrones — Storage Cleanup Final Closeout

**STORAGE CLEANUP CAMPAIGN — CLOSED**

Date: November 1, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`. Branch: `feature/product-realization`. HEAD: `9f6a008837438b6a9b3128b31e2cd178c7f19e90`.

This closeout is documentation only. No file was deleted. No application code, test, workflow, evidence archive, or ZIP was modified. No commit, push, fetch, garbage collection, or history rewrite was run. The only files created are this report and `artifacts/storage_cleanup_development_handoff.md`. Both are untracked.

The size figures in sections A and E were measured before these two documents existed. Their own sizes are recorded at the end of section E.

## A. Executive Summary

The storage-cleanup campaign is closed. The repository was reduced from **5,919,390,899** logical bytes (225,086 files) to **3,336,646,861** logical bytes (64,114 files), measured before this closeout's two documents.

| Result | Value |
| --- | ---: |
| Campaign status | Closed. Phase 2E was not started |
| Original logical footprint | 5,919,390,899 bytes |
| Final logical footprint, before these two documents | 3,336,646,861 bytes |
| Net logical reduction | 2,582,744,038 bytes (43.63%) |
| Gross working-tree bytes deleted | 2,920,457,092 bytes across 161,801 files |
| External recovery archives, same disk | 140,346,974 bytes |
| Same-disk logical recovery | 2,442,397,064 bytes |

Same-disk recovery is the repository reduction minus the four recovery archives, which remain on drive `C:`. It is a sum of logical file lengths, not an NTFS free-space measurement.

The reduction is real in the working tree and in future checkouts of the two cleanup commits. It is not a reduction of historical Git blobs, and it is not a measured reduction of GitHub repository storage. Pack files are the same size as in the original audit.

Remaining caveats, separated from the cleanup result:

- The GitHub Actions `Content lint` workflow was reported failed for `9f6a008837438b6a9b3128b31e2cd178c7f19e90`. No local evidence establishes the cause.
- Three conversational-continuity tests (C01–C03) fail on the original baseline and on the cleaned tree. The full regression suite is not a passing suite.
- Recovery archives sit on the same physical disk as the repository.
- All ZIP archives, including the four small D1 candidates, were retained on purpose.
- The separate `venv/` tree was retained because its IDE relationship is unresolved.

## B. Chronological Phase Summary

Bytes below are logical file lengths. Each deletion row is disjoint. The Phase 2A closeout committed the same 523,570,476 bytes already removed from the worktree in Phase 2A. The first Phase 2C attempt removed nothing. ZIP duplicate estimates were never deletions.

| Phase | Kind | Objective and initial scope | Files removed | Logical bytes removed | Recovery | Verification | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Initial audit | Audit only | Inventory the repository at `c16d922865b7182d47b87d27ec633f9308f1ef4c` and classify cleanup candidates. Scope: the whole tree, including ignored files and `.git`. | 0 | 0 | None required | Report only. Baseline **5,919,390,899** bytes, 225,086 files | None | None |
| Phase 1 | Ignored-file deletion | Remove Category A reproducible local output: pytest case stores under `development/tmp`, 44 unreferenced artifact pytest roots, source-backed bytecode, `.pytest_cache`, and two local golden-replay metrics files. Planned 96,148 files / 1,888,256,124 bytes. Five evidence-tree bytecode files were kept. | 96,143 | 1,888,047,624 | None. The outputs were regenerable local files. Git never stored them | Preservation hashes unchanged. 63 selected non-provider tests passed. HEAD stayed `c16d922` | None | None |
| Phase 2 audit | Audit only | Re-measure after Phase 1 and classify Category C. No deletion. | 0 | 0 | None required | Category A still absent. Tracked payload still 75,403 files / 2,905,056,229 bytes | None | None |
| Phase 2A | Tracked deletion | Remove 49 historical pytest working-store directories. Scope matched the Phase 2 tracked-scratch total. | 31,886 | 523,570,476 | Parent commit `c16d922865b7182d47b87d27ec633f9308f1ef4c` | Investigation: **PASS WITH CAVEATS**. C01–C03 fail on the baseline and on the cleaned tree. T05 passed on a fresh temporary directory | `e86fd4512028af4ce698090d48c1b672dd68600c` | Not during this phase. Pushed in Phase 2B-C1 |
| Phase 2B-C1 | Ignored-file deletion | Remove `.pyc` files inside `development/tmp/github_checkpoint/baseline_4320bcd/` whose `.py` sources remained. | 1,064 | 35,207,113 | The `.py` sources and commit `4320bcdd50471c744746811f213a60b1893496d2`. The `.pyc` bytes themselves were not archived | Sources remained. No other file changed size during the deletion. NTFS allocation released was 37,432,720 bytes | None | This phase pushed Phase 2A: `c16d9228..e86fd451`. Ahead/behind then 0/0 |
| Phase 2B-C2 | Ignored-file deletion | Archive, verify, then remove 13 ignored `test_*` pytest roots, including the cited `pytest_reg` directories. | 5,105 | 105,879,032 | `ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` | Full extract matched path, length, and SHA-256 before deletion | None | None |
| Phase 2B-C3 | Ignored-file deletion | Archive, verify, then remove the remaining `baseline_4320bcd/` checkout. Sibling checkpoint diagnostics stayed. | 15,308 | 250,088,273 | `ashen_thrones_phase2b_c3_checkpoint_4320bcd_20261031.zip`, plus Git for the historical blobs | **PASS WITH CAVEATS**. The archive holds the working-tree bytes. The commit does not reproduce 15,039 CRLF checkouts, 31 local edits, or 67 paths that were never in the commit | None | None |
| Phase 2B-C4 | Ignored-file deletion | Archive, verify, then remove `development/tmp/maintenance_ci_venv/` and the ignored half of `.venv-broken/`. Tracked `.venv-broken` files stayed. | 9,632 | 93,266,927 | `ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` | **PASS WITH CAVEATS**. Extract matched before deletion. Active `.venv` fingerprint unchanged. Same-disk archive | None | None |
| Phase 2C | Tracked deletion, after a stopped attempt | Remove the 2,663 tracked `.venv-broken/` files. The first attempt stopped because two mixed-line-ending `METADATA` files could not be rebuilt from Git. The recovery attempt archived the working-tree bytes, checked the extract, and then deleted. | 2,663 | 24,397,647 | `ashen_thrones_phase2c_tracked_venv_broken_20261031.zip`. Git still has the LF blobs in the parent commit | **PASS WITH CAVEATS**. 2,663 of 2,663 extracted hashes matched, including both mixed `METADATA` files. Commit contains only those deletions | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` | Not during this phase. Pushed in Phase 2D |
| Phase 2D | Audit only | Push the Phase 2C commit and audit remaining ZIP archives. Decide whether any further deletion is worth doing. | 0 | 0 | None required. Four external archives were re-opened read-only | ZIP census: 431 files, 260,537,941 bytes. The earlier 66,621,016 excess figure reconciles exactly and is not a deletion budget | None | Fast-forward `e86fd451..9f6a0088`. Local and remote-tracking HEAD then matched |

### Tracked deletions and ignored cleanup

| Class | Files | Logical bytes | Where the bytes went |
| --- | ---: | ---: | --- |
| Ignored or untracked working-tree cleanup (Phase 1, 2B-C1, 2B-C2, 2B-C3, 2B-C4) | 127,252 | 2,372,488,969 | Local disk. Phase 1 and the checkpoint bytecode had no archive. The other three phases have external ZIPs |
| Tracked deletions (Phase 2A and Phase 2C recovery) | 34,549 | 547,968,123 | Removed from HEAD and from future checkouts. Blobs remain in the parent commits |
| **Gross removed** | **161,801** | **2,920,457,092** | Do not add the audit rows or the ZIP-excess estimates to this total |

The tracked total is the Phase 2 audit's entire C2 tracked-checkout figure. Both cleanup commits are ordinary commits on `feature/product-realization`.

### Phase caveats that still matter

- Phase 1's own net, measured from a preflight of 5,919,528,374 bytes, was 1,542,057,393 bytes. That preflight was 137,475 bytes above the original audit because the audit report and local metadata already existed. This closeout uses the original audit total as the campaign baseline.
- During Phase 1, `.git/cursor/` grew by one crepe index (328,354,559 bytes). Phase 2A later dropped the previous index (79,357,970 bytes). Those IDE files were never cleanup targets.
- Phase 2A left `artifacts/pr_eg_r4_r1/replay_state/data/session.json` 32 bytes larger on disk after `git restore`, because `core.autocrlf` is true. Git reports the file clean. Newline-normalized content matches HEAD.
- Phase 2B-C3's exact CRLF checkout and 31 local edits exist in the external archive. `git checkout 4320bcdd` restores Git content, not those exact working-tree bytes.
- Phase 2C's two mixed `METADATA` files exist as working-tree bytes only in the Phase 2C archive. The parent commit stores LF blobs.
- Empty directory shells remain for removed pytest roots, `maintenance_ci_venv/`, `baseline_4320bcd/`, and `.venv-broken/`. They contribute no file bytes.
- Category B from the original audit (33 archive-backed files, 113,878,270 bytes) was never deleted.

## C. Git State

Checked read-only on November 1, 2026. This closeout did not fetch. The remote-tracking ref is the ref Phase 2D recorded after the push.

| Check | Result |
| --- | --- |
| Repository | `ashen_thrones_ai_gm` |
| Branch | `feature/product-realization` |
| HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| HEAD parent | `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Parent of that commit | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Remote-tracking ref | `origin/feature/product-realization` |
| Remote-tracking SHA | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Ahead / behind | 0 / 0 |
| Staged changes | None |
| Unstaged tracked changes | None |
| Merge, rebase, cherry-pick, or bisect | None |
| Worktrees | The active repository only |
| Unexpected tracked modifications | None |

HEAD subjects:

- `9f6a008837438b6a9b3128b31e2cd178c7f19e90` — `chore: remove tracked obsolete virtual environment` (2026-11-01). 2,663 deletions, all under `.venv-broken/`.
- `e86fd4512028af4ce698090d48c1b672dd68600c` — `chore: remove historical pytest working stores` (2026-10-31). 31,886 deletions, all inside the Phase 2A manifest.

`git ls-files` now lists **40,854** paths. That is the original 75,403 tracked files minus 31,886 minus 2,663. No tracked path remains under `.venv-broken/`.

Untracked files at the start of this closeout were the twenty earlier cleanup reports and manifests, 40,696,221 bytes. They are still untracked. This closeout adds two more untracked markdown files and does not stage them.

`git count-objects -v` still reports **35 packs, size-pack 303,667 KiB**, and **one garbage object** (`.git/objects/92/tmp_obj_xKdgkS`, 55 KiB in Git's units, 56,498 bytes on disk in the original audit). The garbage object was left in place. No pack was rewritten.

## D. Recovery and Preservation

### Recovery archives

Directory: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\`

This closeout recomputed SHA-256 for each archive. All four match the phase reports. They were not extracted again. The creating phase already extracted each archive and matched every member before deletion.

| Archive | Bytes | SHA-256 | Restores |
| --- | ---: | --- | --- |
| `ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` | 19,722,751 | `7df6f3a68feba8e3130de20ae98505601290327ffcac532a4a72d21a5ffd7740` | 5,105 ignored pytest-store files, 105,879,032 bytes |
| `ashen_thrones_phase2b_c3_checkpoint_4320bcd_20261031.zip` | 75,223,700 | `1f87961a5dca24047b8188c095dbcd01edbf6fc9fa7b035da9275f07796fb894` | 15,308 checkpoint files, 250,088,273 bytes |
| `ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` | 37,865,504 | `fde74bd409eccc806e48db825c80b29e398c15c8a182638fc771f4b80eb3c858` | 9,632 maintenance-environment and ignored `.venv-broken` files, 93,266,927 bytes |
| `ashen_thrones_phase2c_tracked_venv_broken_20261031.zip` | 7,535,019 | `9e98d345d5e6495afcb581b180526b3ecfcc788d1f2381df239b479b2881fd45` | 2,663 tracked `.venv-broken` files, 24,397,647 bytes, including both mixed `METADATA` files |

Total archive bytes: **140,346,974**.

These are verified local recovery copies. They are on the same physical disk as the repository. They are not an independent backup. A failure of that disk loses the archives and the repository together.

Phase 2A also left investigation output outside the repository. It is still present and was not part of the recovery-archive set:

| Path | Files | Bytes |
| --- | ---: | ---: |
| `C:\p2a_inv\` | 17 | 50,265 |
| `C:\p2a_pytest_baseline` | 9 | 9,836 |
| `C:\p2a_pytest_postclean` | 9 | 9,836 |
| `C:\p2a_pytest_replay1` | 0 | 0 |
| `C:\p2a_pytest_replay2` | 0 | 0 |

Those five paths total 69,937 bytes. They were retained when Phase 2A closed. This closeout did not remove them.

### Git recoverability

History is intact. No commit was rewritten and no object was pruned.

| Deleted tracked set | Restore point |
| --- | --- |
| Historical pytest stores | `c16d922865b7182d47b87d27ec633f9308f1ef4c` or `git revert e86fd4512028af4ce698090d48c1b672dd68600c` |
| Tracked `.venv-broken` blobs | `e86fd4512028af4ce698090d48c1b672dd68600c`. That checkout restores LF blob bytes. The two mixed-line-ending files require the Phase 2C archive |
| Checkpoint Git content | `4320bcdd50471c744746811f213a60b1893496d2`. Exact CRLF and local-edit bytes require the Phase 2B-C3 archive |
| Ignored pytest stores and removed environments | The matching external archive. Git never stored those files |

### Protected project material

Checked by presence, by published size where a prior phase recorded one, and by the clean tracked diff. This closeout did not rehash the repository.

| Material | This closeout |
| --- | --- |
| `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, `experiments/` | Present. Tracked diff against HEAD is empty, so tracked source matches `9f6a008` |
| `data/` | 150 files, 1,218,696 bytes, the original audit figure |
| `data/validation/atgb/` | 20 files, 85,698 bytes |
| `artifacts/atgb/` | 14,421 files, 786,400,864 bytes, the original audit figure |
| `artifacts/golden_replay/` | Present. 116 files, 2,371,988 bytes, matching the Phase 1 protected-replay file count after the two approved metrics files were removed |
| `artifacts/pr_eg_r6_r5/snapshots/` | 2,952 files, 147,800,156 bytes, the original audit figure |
| `artifacts/pr_play_10/`, `artifacts/pr_play_11/`, `artifacts/pr_play_12/` | Present. 261 / 152 / 325 files. Neither cleanup commit touched `artifacts/pr_play` |
| `handoff/CURRENT_REVIEW.zip` | Present, 3,796,976 bytes. `handoff/history/pr_play_10`, `pr_play_11`, and `pr_play_12` are present |
| `handoff/` | 479 files, 186,508,635 bytes, the original audit figure |
| `history/` | 7 files, 29,392,884 bytes, the original audit figure |
| `development/tmp/storage_cleanup_phase1_control/` | 65 files, 17,652,087 bytes |
| `development/tmp/github_checkpoint/` sibling diagnostics | 96 files, 20,011,055 bytes, the Phase 2 C5 figure. The nested checkout files are gone; the archive holds them |
| `disposable_state/` trees | 11 directories, 531 files, 20,310,198 bytes, the Phase 2 figure |
| Active `.venv/` | 5,951 files, 56,291,644 bytes, unchanged since the original audit |
| Separate `venv/` | 5,390 files, 49,494,117 bytes, unchanged since the original audit |
| `.idea/` | 7 files, 4,338 bytes, the original audit total. Earlier phases found the Python 3.9 SDK selection that is why `venv/` stayed |
| ZIP census | 431 files, 260,537,941 bytes, identical to Phase 2D. The four D1 files are present at the audited sizes (280,133, 280,133, 296,696, and 268,300) |
| Earlier cleanup reports and manifests | All 20 files present, 40,696,221 bytes, still untracked |
| `.venv-broken/` | Directory remains. 0 files |

`game/` is 405 files and 13,077,996 bytes, and `tests/` is 896 files and 15,544,183 bytes. Both are larger than the Phase 2 audit because the Phase 2A investigation regenerated ignored bytecode. That bytecode is the 6,341,440 bytes under `game/`, the 1,415,882 bytes under `tests/`, and 4,153 bytes under `experiments/` in the ledger below. The tracked diff is empty, so those extra bytes are ignored cache, not source edits made during this closeout.

`tools/` matches the Phase 2 audit exactly (274 files, 3,963,830 bytes). `docs/`, `audits/`, `static/`, `.github/`, and the loose repository-root files match the original audit totals.

## E. Storage Accounting

Method: sum of regular-file lengths, including `.git`, without following reparse points. The walk found no reparse points and no unreadable files. These are not NTFS allocated clusters. The two documents created by this closeout are excluded until the last table in this section.

### Original and final footprint

| Measurement | Files | Logical bytes |
| --- | ---: | ---: |
| Original audit, 2026-10-31 | 225,086 | 5,919,390,899 |
| Working tree excluding `.git`, original | — | 5,515,595,937 |
| Root `.git`, original | 210 | 403,794,962 |
| This closeout, before these two documents | 64,114 | 3,336,646,861 |
| Working tree excluding `.git` | 63,882 | 2,689,594,715 |
| Root `.git` | 232 | 647,052,146 |
| **Net repository reduction** | — | **2,582,744,038** |

2,582,744,038 / 5,919,390,899 = **43.63%**.

Working-tree logical reduction: 2,826,001,222 bytes. `.git` grew by 243,257,184 bytes. The difference is the net repository reduction.

### Current major categories

Overlaps are marked. Do not add overlapping rows.

| Category | Files | Logical bytes | Notes |
| --- | ---: | ---: | --- |
| Whole repository, before these two documents | 64,114 | 3,336,646,861 | Disjoint total |
| `.git/` | 232 | 647,052,146 | Included in the total |
| `.git/objects/` | 185 | 312,108,741 | Included in `.git/` |
| `.git/objects/pack/` | 105 | 311,150,216 | Included in objects. Same byte total as the original audit |
| `.git/cursor/` | 4 | 328,354,559 | Included in `.git/`. Local IDE index for `c16d922`, not pushed project content |
| Working tree excluding `.git/` | 63,882 | 2,689,594,715 | Disjoint from `.git/` |
| ZIP files | 431 | 260,537,941 | Included in the working tree. 423 tracked, 8 ignored |
| Active `.venv/` | 5,951 | 56,291,644 | Included in the working tree |
| Separate `venv/` | 5,390 | 49,494,117 | Included in the working tree |
| `artifacts/` | 45,117 | 2,175,804,062 | Includes ATGB, snapshots, PR-PLAY evidence, and the cleanup reports |
| `artifacts/atgb/` | 14,421 | 786,400,864 | Included in `artifacts/` |
| `handoff/` | 479 | 186,508,635 | Review packages |
| `development/` | 4,334 | 141,694,206 | Includes Phase 1 control, checkpoint diagnostics, Phase 2A scratch, and retained C4 leftovers |
| `history/` | 7 | 29,392,884 | Development logs preserved by the product-realization portfolio note |

### Gross removals, additions, and the net

Gross bytes deleted: **2,920,457,092**.

If nothing else had changed, the repository would be 5,919,390,899 − 2,920,457,092 = 2,998,933,807 bytes. The measured repository is 3,336,646,861. The difference is **337,713,054** bytes of growth during the campaign. That growth splits cleanly.

Working-tree additions, **94,455,870** bytes:

| Addition | Bytes |
| --- | ---: |
| Cleanup reports and manifests now on disk, 20 files | 40,696,221 |
| Phase 1 control directory | 17,652,087 |
| Phase 2A scratch kept under `development/tmp/` (`phase2a_preflight` 23,496,405, `phase2a_pytest` 4,847,617, `phase2a_netblock` 1,237) | 28,345,259 |
| Bytecode regenerated by the Phase 2A investigation (`game/` 6,341,440, `tests/` 1,415,882, `experiments/` 4,153, `.pytest_cache/` 796) | 7,762,271 |
| `session.json` CRLF presentation after restore | 32 |
| **Worktree additions** | **94,455,870** |

`.git` growth, **243,257,184** bytes:

| Component | Original | Current | Change |
| --- | ---: | ---: | ---: |
| `.git/cursor/` | 79,357,970 | 328,354,559 | +248,996,589 |
| `.git/objects/` | 312,013,829 | 312,108,741 | +94,912 |
| Rest of `.git/` | 12,423,163 | 6,588,846 | −5,834,317 |
| **Root `.git/`** | **403,794,962** | **647,052,146** | **+243,257,184** |

Object growth of 94,912 bytes is the sum of three already reported steps: +58,128 by the Phase 2 audit measurement (312,071,957), +33,776 for the Phase 2A commit (312,105,733), and +3,008 for the Phase 2C commit (312,108,741). Pack bytes did not change.

94,455,870 + 243,257,184 = 337,713,054. Gross deletions minus that growth equal the net reduction:

2,920,457,092 − 337,713,054 = **2,582,744,038**.

File count closes the same way:

225,086 − 161,801 + 22 additional `.git` files + 562 report, control, and Phase 2A scratch files + 245 regenerated bytecode and pytest-cache files = **64,114**.

### External archives and same-disk recovery

| Quantity | Logical bytes |
| --- | ---: |
| Gross working-tree bytes deleted | 2,920,457,092 |
| New report and manifest bytes inside the repository | 40,696,221 |
| External recovery archive bytes | 140,346,974 |
| Net repository-size reduction | 2,582,744,038 |
| Net same-disk logical recovery (repository reduction minus the four archives) | 2,442,397,064 |

The 69,937 bytes of Phase 2A investigation directories are an additional same-disk cost outside the repository. They are not included in the 2,442,397,064 figure.

Phase-level disk notes, for the record, are not a second campaign total:

- Phase 2B-C1 released 37,432,720 bytes of NTFS allocation for 35,207,113 logical bytes. That is the only phase that measured cluster slack (2,225,607 bytes).
- Later archived phases reported logical recovery of deleted bytes minus the new archive: 86,156,281, 174,864,573, 55,401,423, and 16,862,628. Those figures were correct at the time. They omit Phase 1, Phase 2A, report growth, and the `.git/cursor/` change, so they are not added here as the campaign result.

### Git object storage

| Item | Result |
| --- | --- |
| Pack directory | 311,150,216 bytes, 105 files, identical to the original audit |
| `size-pack` | 303,667 KiB, identical to the original audit |
| Object directory | 312,108,741 bytes, up 94,912 from the audit |
| Loose objects | 77, up from 56 at the audit |
| Garbage object | Still present. Not removed |
| Historical blobs for deleted tracked files | Still reachable from `c16d922` and `e86fd451` |
| GitHub stored history | Not measured. The two cleanup commits do not delete historical objects. A smaller checkout is not a smaller GitHub object store |

No history rewrite or `git gc` was authorized or run.

### These two closeout documents

Measured after the files were written. Add them to the pre-document footprint. They do not change the deletion ledger.

| Document | Bytes |
| --- | ---: |
| `artifacts/storage_cleanup_final_closeout.md` | 32,251 |
| `artifacts/storage_cleanup_development_handoff.md` | 5,792 |
| Both documents | 38,043 |
| Repository including both documents | 3,336,684,904 |

## F. Intentionally Retained Material

Retention is the closeout decision. These items are not unfinished cleanup work.

### ZIP archives

Phase 2D inventoried every repository ZIP. This closeout's ZIP census still matches that inventory, so the classes are unchanged.

| Class | Files | Bytes | Decision |
| --- | ---: | ---: | --- |
| Inventoried ZIPs | 431 | 260,537,941 | Keep the whole set |
| Exact-duplicate groups | 34 | 70,680,001 excess | Explained surplus, not a deletion budget |
| D1, strong candidates | 4 | 1,125,262 | **Retain.** The savings are too small for another cleanup operation |
| D2, conditional candidates | 20 | 30,679,686 | **Retain.** They need dependency or historical-citation decisions that this campaign will not make |
| D3, preserved archives | 407 | 228,732,993 | **Retain.** Protected campaign history, current review copies, ATGB, and PR-PLAY packages |
| D4, uncertain | 0 | 0 | None |

The four D1 files, all ignored, all still present:

- `development/tmp/atgb_r1_07_export/CURRENT_REVIEW.zip` (280,133)
- `development/tmp/atgb_r1_07_export/history/atgb_r1_07/REVIEW.zip` (280,133)
- `development/tmp/atgb_r2_04_prior_handoff/CURRENT_REVIEW.zip` (296,696)
- `development/tmp/pr_play_02_previous_handoff/CURRENT_REVIEW.zip` (268,300)

`handoff/CURRENT_REVIEW(20261019-181208).zip` remains the only tracked copy of the fourth D1 hash. D1 sibling `CURRENT_REVIEW.md` and `REVIEW_MANIFEST.json` files were never classified for deletion and stay.

The earlier 66,621,016-byte duplicate estimate is the Phase 2 excess after removing the protected PR-PLAY-12 trio (74,214,968 − 7,593,952). Phase 2D showed where those bytes went: copies removed with the pytest stores and the checkpoint, plus excess that remains inside protected D3 aliases. Current excess is 70,680,001. Current excess outside the PR-PLAY-12 trio is 63,086,049. The arithmetic closes with a zero unexplained delta. It does not authorize deletion.

### Environments

| Tree | Files | Bytes | Why it stays |
| --- | ---: | ---: | --- |
| Active `.venv/` | 5,951 | 56,291,644 | Documented interpreter. `scripts/run_live_playtest.ps1` selects it |
| Separate `venv/` | 5,390 | 49,494,117 | Python 3.9 environment. `.idea/` still names that SDK. The relationship was not resolved, so the tree stays |
| `.venv-broken/` directory shell | 0 | 0 | Files were removed in Phase 2C. The empty directories are harmless |

### Protected historical evidence

Kept because current tests, replay, review, or an explicit retention note depend on them, or because a later audit could not prove them disposable:

- Frozen ATGB inputs and `artifacts/atgb/`.
- Golden-replay evidence, other than the two local metrics files removed in Phase 1.
- PR-PLAY 10, 11, and 12 evidence and their history packages, including the current review trio.
- `artifacts/pr_eg_r6_r5/snapshots/`, which counterfactual replay restores.
- Source snapshots and the seven Category B neighbor files that were absent from the R2C-R2 review ZIP.
- `disposable_state/` (531 files, 20,310,198 bytes), which Phase 2 left in class C4.
- Checkpoint sibling diagnostics (20,011,055 bytes) and the Phase 1 control directory.
- `development/tmp/pr_play_05/` (38,888,302 bytes), `development/tmp/pr_play_02_entry_surface/` (12,436,235 bytes), and the other smaller `development/tmp` leftovers Phase 2 classified as C4.
- `history/development_logs/`.
- The 66 source-missing bytecode exceptions from the original audit. The one root `__pycache__` file still present is 2,601 bytes, the listed `_probe_routes` cache.
- Git history, packs, the pre-existing garbage object, and `.git/cursor/`.

Phase 2's C4 project-file ceiling was 144,053,732 bytes, dominated by `venv/`, the PR-PLAY-05 overlay, other `development/tmp` leftovers, `disposable_state/`, and orphan bytecode. Those bytes are still in the tree on purpose.

### Other retained local material

- Phase 2A scratch under `development/tmp/phase2a_preflight/`, `phase2a_pytest/`, and `phase2a_netblock` (28,345,259 bytes). It is the validation record of that phase.
- The external `C:\p2a_*` investigation directories (69,937 bytes).
- All prior cleanup reports and manifests.

## G. Outstanding Development Issues

These are not storage-cleanup defects. This closeout did not try to fix them.

### GitHub Content lint failure

A GitHub Actions notification reported that the `Content lint` workflow failed for commit `9f6a008837438b6a9b3128b31e2cd178c7f19e90`.

**Open development-validation issue — root cause not established.**

No local log of that run was found in the cleanup reports or elsewhere in the working tree. This closeout did not fetch GitHub and did not rerun the workflow. Existing documentation describes older content-lint behavior, including a non-blocking Phase-1 step. That history does not identify why this commit's workflow failed, and it is not evidence that the cleanup caused the failure or that the failure predated the cleanup.

### Historical conversational-continuity regressions

Phase 2A's required selection finished **189 passed, 3 failed, 1 error**. The investigation then compared the original commit with the cleaned tree.

| Test | On the original baseline | On the cleaned tree | Status |
| --- | --- | --- | --- |
| `test_independent_clarification_holdout[C01]` | Failed | Failed, same line | Pre-existing |
| `test_independent_clarification_holdout[C02]` | Failed | Failed, same line | Pre-existing |
| `test_independent_clarification_holdout[C03]` | Failed | Failed, same line | Pre-existing |
| `test_targeted_reference_matrix` T05 | Passed on a fresh temporary directory | Passed on a fresh temporary directory | The Phase 2A `PermissionError` was not reproduced. It was basetemp reuse, not a missing store |

The investigation's conclusion remains **PASS WITH CAVEATS**. No cleanup-introduced regression was demonstrated. The full regression suite was not re-run, and this closeout does not describe it as passing.

C01–C03 call `continuity_directive` and expect a frozen clarification line. The observed line is the absent-NPC sentence. The holdout fixtures and `game/conversational_continuity.py` were not part of any deletion. Repair is product work, outside this campaign.

### Additional issues already established by the cleanup reports

- `core.autocrlf` is true and there is no `.gitattributes` file. That is why some historical checkouts and the two `.venv-broken` metadata files differ from Git blobs. It is a standing repository setting, not a new defect found by this closeout.
- `.git/objects/92/tmp_obj_xKdgkS` remains a Git garbage object. It was already present at the original audit. It was not removed.
- T05 can hit a Windows file-lock or basetemp-reuse error if a later run reuses `development/tmp/phase2a_pytest` or `development/tmp/pytest`. That behavior is independent of the deleted trees.

No other failure was established by the existing reports. This closeout does not add speculative defects.

## H. Final Recommendation

The repository is ready to return to Product Realization work as a housekeeping matter.

The branch is `feature/product-realization`. Local HEAD and the remote-tracking ref are both `9f6a008837438b6a9b3128b31e2cd178c7f19e90`, ahead/behind 0/0. The tracked worktree is clean. Protected evidence used by ATGB, golden replay, and PR-PLAY 10, 11, and 12 is present. Active `.venv/` is intact.

That readiness is repository housekeeping. It is not a claim that gameplay is certified or that the regression suite is green. C01–C03 still fail. The Content lint workflow failure on this HEAD is unresolved. This closeout did not run the suite, did not start a play session, and did not open a new development task.

No further storage cleanup is planned. Phase 2E will not start. D1, D2, and D3 ZIPs stay. `venv/` stays until a separate IDE decision is made. Git history stays as it is.

## Closeout checks

| Criterion | Result |
| --- | --- |
| Existing phase evidence reviewed | Yes |
| Git state matches the expected branch, HEAD, and remote-tracking SHA | Yes. Ahead/behind 0/0. No fetch performed |
| Protected project material intact | Yes, on the checks in section D |
| Final storage measurements recorded | Yes |
| Phase 2D retention decision recorded | Yes. D1, D2, and D3 retained |
| Development issues separated from cleanup results | Yes |
| This closeout report exists | Yes |
| Development handoff exists | Yes |
| Unauthorized file changes | None. Tracked diff empty aside from the two new untracked documents |
| Additional cleanup performed | None |
