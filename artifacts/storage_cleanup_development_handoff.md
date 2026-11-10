# Ashen Thrones — Storage Cleanup Development Handoff

Date: November 1, 2026.

This is the short handoff for the next Product Realization session. The full ledger is `artifacts/storage_cleanup_final_closeout.md`. Do not start another storage-cleanup phase from this note.

## 1. Why the cleanup was undertaken

On October 31, 2026 the repository measured **5,919,390,899** logical bytes and 225,086 files. Most of that was generated evidence, historical pytest stores, a nested checkpoint checkout, and local virtual environments. Application source and Git packs were the smaller part. The campaign removed regenerable local output and two classes of tracked scratch, after archives or Git history could restore them.

## 2. What was removed

161,801 files, **2,920,457,092** logical bytes. The rows do not overlap.

| What | Files | Logical bytes | Git |
| --- | ---: | ---: | --- |
| Category A pytest stores, unreferenced artifact runs, source-backed bytecode, pytest cache, two local replay metrics | 96,143 | 1,888,047,624 | Ignored. No commit |
| Historical pytest working stores | 31,886 | 523,570,476 | Commit `e86fd4512028af4ce698090d48c1b672dd68600c` |
| Checkpoint `.pyc` files whose `.py` sources remained | 1,064 | 35,207,113 | Ignored. No archive |
| Ignored pytest `test_*` stores | 5,105 | 105,879,032 | External archive, then deleted |
| Historical `baseline_4320bcd` checkout | 15,308 | 250,088,273 | External archive, then deleted |
| Maintenance virtual environment and ignored `.venv-broken` files | 9,632 | 93,266,927 | External archive, then deleted |
| Tracked `.venv-broken` files | 2,663 | 24,397,647 | External archive, then commit `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |

The repository measured **3,336,646,861** logical bytes and 64,114 files before the final closeout documents. Net reduction versus the original audit: **2,582,744,038** bytes (43.63%). Pack files are unchanged. Historical Git blobs for the tracked deletions are still in the parent commits. GitHub object storage was not reduced by those commits.

## 3. What was deliberately preserved

- `game/`, `data/`, `tests/`, `tools/`, `scripts/`, `static/`, and `experiments/`.
- ATGB baselines and `artifacts/atgb/` (14,421 files, 786,400,864 bytes).
- Golden-replay evidence, PR-PLAY 10, 11, and 12, the current review package, historical campaign packages, `artifacts/pr_eg_r6_r5/snapshots/`, and source snapshots.
- Phase 1 control evidence and the checkpoint diagnostics beside the removed checkout.
- Active `.venv/` (5,951 files, 56,291,644 bytes).
- Separate `venv/` (5,390 files, 49,494,117 bytes), because `.idea/` still selects the Python 3.9 SDK.
- Every repository ZIP. Phase 2D found 431 files and 260,537,941 bytes. D1 (4 files, 1,125,262 bytes), D2 (20 files, 30,679,686 bytes), and D3 (407 files) all stay. The savings were too small, or the files still need a citation decision.
- Git history, including the pre-existing garbage object under `.git/objects/`. No history rewrite and no garbage collection.

## 4. Current Git HEAD and branch

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Remote-tracking HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Ahead / behind | 0 / 0 |
| Tracked worktree | Clean |
| Cleanup reports and manifests | Untracked, including this handoff |

The closeout did not fetch, commit, or push. The remote-tracking ref is the ref recorded after the Phase 2D fast-forward push.

## 5. Final closeout report

`artifacts/storage_cleanup_final_closeout.md`

## 6. Recovery archives

`C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_storage_archives\`

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `ashen_thrones_phase2b_c2_pytest_stores_20261031.zip` | 19,722,751 | `7df6f3a68feba8e3130de20ae98505601290327ffcac532a4a72d21a5ffd7740` |
| `ashen_thrones_phase2b_c3_checkpoint_4320bcd_20261031.zip` | 75,223,700 | `1f87961a5dca24047b8188c095dbcd01edbf6fc9fa7b035da9275f07796fb894` |
| `ashen_thrones_phase2b_c4_maintenance_envs_20261031.zip` | 37,865,504 | `fde74bd409eccc806e48db825c80b29e398c15c8a182638fc771f4b80eb3c858` |
| `ashen_thrones_phase2c_tracked_venv_broken_20261031.zip` | 7,535,019 | `9e98d345d5e6495afcb581b180526b3ecfcc788d1f2381df239b479b2881fd45` |

This closeout recomputed those hashes and they match. The archives are on the same disk as the repository. They are verified recovery copies, not an independent backup. Phase 2A investigation notes also remain at `C:\p2a_inv\` and `C:\p2a_pytest_*` (69,937 bytes).

## 7. Known unresolved development-validation issues

- **Content lint.** The GitHub Actions `Content lint` workflow was reported failed for `9f6a008837438b6a9b3128b31e2cd178c7f19e90`. Root cause not established. Do not assume the cleanup caused it.
- **Conversational continuity.** `test_independent_clarification_holdout` cases C01, C02, and C03 fail on the original baseline and on the cleaned tree. The Phase 2A investigation called this **PASS WITH CAVEATS**. The full regression suite is not a passing suite. Repair belongs to product work.

## 8. No further storage cleanup is planned

Phase 2E will not start. D1, D2, and D3 ZIPs stay. `venv/` stays. Git history stays. Empty directory shells from removed trees have no file bytes and were left in place.

## 9. Return to Product Realization and ATGB

Housekeeping is complete. The next session can return to Product Realization and ATGB work on `feature/product-realization` at `9f6a008837438b6a9b3128b31e2cd178c7f19e90`.

That is a repository-state recommendation. It does not certify gameplay, and it does not mean the regression suite is green.
