# AT-FG-04 — Final report

**Disposition: PASS.**

The remaining verified temporary cleanup is complete. No artifact directory and no campaign document was deleted. `handoff/CURRENT_REVIEW.*` was not replaced.

## 1. TMP cleanup verdict

The frozen allowlist `development/reports/AT-FG-02B_EXEC_ALLOWLIST.json` still has canonical SHA-256 `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`. It was not rewritten.

Subtracting the 7 Pilot A roots and the 45 Pilot B roots left exactly 815 candidates, 1,113,200 files, and 3,671,945,277 apparent bytes. That matches the Pilot B remaining-capacity report. Thirteen of those candidates are `EXACT` empty shells. The other 802 are `STRUCTURALLY_SUPPORTED`. All 815 were `PREFLIGHT-VERIFIED`. None were rejected, protected, or review-required.

Every selected root kept its frozen filesystem identity. Every file hash matched its frozen inventory. No operational or protected source referenced a selected path. All 815 were then deleted with the Pilot B mechanism: per-file SHA-256 on an exclusive no-follow handle, then `os.rmdir` only for empty directories. Producer-family parents were not removed.

Manifest SHA-256: `c4114e375c26e303ffef69ce9e8324031fe190c9c9b9e746493bcd221c4ec6a2`.

Frozen inventories are referenced by path and SHA-256. They were not copied into the manifest, because inlining 1,113,200 records would have duplicated the preflight inventories.

## 2. Storage actually recovered

| Measure | Bytes |
|---|---:|
| Candidate roots removed | 815 |
| Files removed | 1,113,200 |
| Directories removed, including roots | 56,724 |
| Apparent bytes removed | 3,671,945,277 |
| Allocated bytes accounted on the deleted-file handles | 4,110,533,056 |
| `development/tmp` census reduction | 1,113,200 files, 56,724 directories, 3,671,945,277 apparent bytes |
| Free-byte increase on the volume | 1,993,609,216 |
| Candidates skipped | 0 |

The census reduction matches the deletion totals exactly. Apparent size is the sum of file lengths. Allocated size is the allocation reported by each deleted handle. The free-byte increase is smaller than the allocated total. The run wrote a 525,913,707-byte file ledger, `development/reports/AT-FG-04_BULK_TMP_DELETED_FILES.jsonl`, and the volume was in use for about 58 minutes. Those two facts account for part of the gap. The free-byte number is the measured disk change. It is not a second copy of the apparent-byte total.

`development/tmp` after cleanup: 2,111,081 files, 207,778 directories, 8,427,432,212 apparent bytes. The three rejected roots are still present. The Pilot A and Pilot B roots are still absent.

## 3. Artifact audit

`artifacts/` contains 507 top-level entries, 419,549 files, 11,806,874,957 apparent bytes (11.00 GB), and about 12.29 GB when each file is rounded up to the 4096-byte cluster. That cluster figure is an estimate, not a handle allocation.

| Class | Apparent bytes | Meaning |
|---|---:|---|
| ACTIVE — RETAIN | 4,279,973,104 | Tests, tools, current handoff, or governance evidence. Includes `artifacts/atgb` (1.19 GB) and `artifacts/pr_play_72v` (760 MB), both referenced by tests. |
| BASELINE — RETAIN | 1,198,636 | `artifacts/at_opt_01` through `artifacts/at_opt_06`. |
| HISTORICAL — ARCHIVE CANDIDATE | 6,957,557,032 | Raw test output whose current tests and runtime do not read it. A historical mention does not keep the raw tree. |
| SUPERSEDED — DELETE CANDIDATE | 0 | Five empty pytest temporary directories. |
| UNKNOWN — REVIEW | 568,146,185 | No safe classification. Includes `artifacts/pr_play_79df` and `artifacts/pr_play_79df2`. |

`artifacts/pr_play_79df3` stays active because it contains `protected_entry.json` from the governance baseline. `artifacts/pr_play_79d` stays active because `tests/test_pr_play_79d_holdout.py` reads it.

Nothing under `artifacts/` was deleted.

## 4. Campaign documentation audit

`development/campaigns/` contains 116 inventoried entries, 11,787 files, and 6,216,381,400 apparent bytes (5.79 GB).

Cursor and Codex are not instructed to recursively load this tree. `docs/DEVELOPMENT_CONSTITUTION.md` says an agent reads the constitution, `docs/NEXT_SESSION.md`, and the authorities that handoff names for the current task. Historical campaign reports are opened when that handoff points at them, when a settled decision has to be reopened, or when an audit needs the comparison. The only Cursor rule in this repository does not read campaign notes. No Codex instruction file enumerates the historical directories. That is not a claim that an agent can never open an old note: search, a user request, or a link in `docs/NEXT_SESSION.md` can still cause a read.

The bulk of the bytes is JSON, XML, and log evidence stored beside the notes, not the markdown itself. The largest trees are recent Product Realization milestone folders named in the previous sections of `docs/NEXT_SESSION.md`.

| Class | Entries | Apparent bytes |
|---|---:|---:|
| ACTIVE | 11 | 36,772,948 |
| GOVERNANCE-REQUIRED | 3 | 2,750,997 |
| HISTORICAL-ARCHIVE | 102 | 6,176,857,455 |

The current live milestone and the constitution's named authorities stay. Completed milestone folders are consolidation candidates, not approved deletions.

## 5. Additional recoverable storage

These figures are proposals. They were not deleted.

| Proposal | Apparent bytes |
|---|---:|
| Historical artifact archive candidates | 6,957,557,032 |
| Superseded empty artifact directories | 0 |
| Historical campaign evidence | 6,176,857,455 |
| Unknown artifact storage, not recoverable until reviewed | 568,146,185 |
| Combined historical artifact and campaign proposal | 13,134,414,487 |

Remaining `development/tmp` storage, 8,427,432,212 apparent bytes, is outside this authorization. It still holds the rejected roots, protected campaign stores, and review-required scratch.

## 6. Proposed deletion candidates

Ranked artifact candidates begin with:

| Path | Apparent bytes | Files |
|---|---:|---:|
| `artifacts/pr_play_75` | 747,530,921 | 25,322 |
| `artifacts/pr_play_72` | 511,832,596 | 20,070 |
| `artifacts/pr_play_t05_composition` | 334,234,251 | 739 |
| `artifacts/pr_play_74` | 305,828,748 | 20,444 |
| `artifacts/pr_play_73` | 292,028,472 | 19,389 |

The exact ranking, byte counts, and reasons are in `development/reports/AT-FG-04_ARTIFACT_CLEANUP_PROPOSAL.json`. The campaign ranking is in `development/reports/AT-FG-04_CAMPAIGN_CLEANUP_PROPOSAL.json`. The largest campaign trees are the recent movement, purpose-tail, pending-intention, compound-admission, and disjunctive-destination milestone folders.

## 7. Protected evidence

Protected AT-OPT trees, the current fresh-live campaign, prior AT-FG review archives, the live campaign stores, social reconciliation, and the PR-PLAY 47 and 49 workspaces matched the Pilot B baseline before deletion and after deletion. The six PR-PLAY data files named by preflight still have the same SHA-256. The three incident paths under social reconciliation are still absent. The three rejected temporary roots are still present.

## 8. Git integrity

Branch `feature/product-realization`. HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. HEAD and the index match the Pilot B baseline and were unchanged by the deletion. Staged, modified, and missing tracked sets were unchanged. No pre-existing status line disappeared. New untracked paths are the AT-FG-04 reports and evidence. No commit and no push.

`docs/NEXT_SESSION.md` and `handoff/CURRENT_REVIEW.*` were left unchanged so the protected handoff baseline stays intact. The review package is `handoff/history/at_fg_04/`. It was written after the integrity snapshot. The 526 MB file-level deletion ledger stays in the repository and is omitted from the zip.

## 9. Recommended next action

Stop. Do not start another cleanup from this report.

The next large recovery, if a later instruction authorizes it, is the historical artifact archive of 6,957,557,032 apparent bytes, followed by historical campaign evidence of 6,176,857,455 apparent bytes. That later instruction needs its own manifest. It should keep tests that still open an artifact, the six AT-OPT trees, `artifacts/pr_play_79df3/protected_entry.json`, and every path the current section of `docs/NEXT_SESSION.md` names. Unknown artifact trees stay in review.

A retention rule for future scratch is proposed in `development/reports/AT-FG-04_RETENTION_POLICY_PROPOSAL.md`. It applies only to workspaces a process creates for itself. It does not reach backward into historical directories.
