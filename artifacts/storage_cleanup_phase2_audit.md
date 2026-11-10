# Ashen Thrones — Storage Cleanup Phase 2 Audit

**Audit only. No cleanup was performed.**

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`. Branch: `feature/product-realization`. HEAD: `c16d922865b7182d47b87d27ec633f9308f1ef4c`. This report is the only project file written for this phase. No file was deleted, moved, renamed, compressed, or edited. `.gitignore`, source, configuration, fixtures, and Git history were not changed. No commit, push, or provider call was made.

## 1. Executive summary

Category A from Phase 1 is still gone, and the working tree outside `.git` is the same size as the Phase 1 final measurement. The large Category C set is not safe to delete outright.

The tracked directories whose names contain `tmp` are pytest `--basetemp` case stores from completed PR-EG campaigns. They hold isolated `data/` trees (`campaign.json`, `session.json`, `session_log.jsonl`, and scene files), not application source. Current tests, ATGB loaders, golden-replay manifests, and PR-PLAY readers do not open them. Campaign review builders exclude the same names from review packages. SHA-256 comparison still shows **522,977,676 bytes (93.1%) of those trees are unique** across the set and are not copies of current `data/`, `tests/fixtures/`, or `game/*.py`. They are different historical test states. Byte-identical regeneration on today's source was not shown. They are **C2**: the current commit already preserves them, and a later ordinary deletion commit can shrink future checkouts. That commit would not shrink existing GitHub object storage.

Verified safe-to-delete storage is much smaller: **1,064 bytecode files, 35,207,113 bytes**, inside the ignored checkpoint checkout `development/tmp/github_checkpoint/baseline_4320bcd/`. Those `.pyc` files are not in commit `4320bcd`, and the snapshot still contains the corresponding `.py` files.

| Savings class | What it is | Bytes | What removal would change |
| --- | --- | ---: | --- |
| C1, local, verified | Checkpoint bytecode only | 35,207,113 | Local disk. Not tracked. |
| C2, local, archive first | Ignored pytest stores, checkpoint checkout minus that bytecode, maintenance venv, ignored half of `.venv-broken` | 449,234,232 | Local disk. Git history does not contain these bytes, so a zip or recorded package list is required first. |
| C2, tracked checkout | Tracked pytest basetemp trees plus the tracked half of `.venv-broken` | 547,968,123 | A future HEAD checkout. Existing GitHub history keeps the blobs. |
| C3, working-tree copies | Exact duplicate ZIP excess still on disk | 74,214,968 | Working-tree copies only. Identical bytes already share one Git blob. Current PR-PLAY-12 review copies are protected. |
| C4, not proposed | Legacy `venv/`, PR-PLAY-05 overlay, other `development/tmp` leftovers, `disposable_state/`, orphan bytecode | 144,053,732 | Needs a narrower pass. Not counted as recoverable yet. |

These rows do not overlap. C3 is not added to C2. `.git/cursor/` is reported separately and is not a deletion target.

Recommended next action: stop here. If a later pass is authorized, delete only the checkpoint bytecode first, then prepare an ordinary commit that removes the tracked pytest basetemp directories in Appendix A, using `c16d922865b7182d47b87d27ec633f9308f1ef4c` as the restore point. Do not rewrite history.

## 2. Current repository storage inventory

Measurements are sums of logical file lengths. They are not NTFS allocation. The walk included hidden files, virtual environments, ignored trees, and `.git`. This report is not included in the totals below.

| Class | Files | Bytes |
| --- | ---: | ---: |
| Tracked worktree files | 75,403 | 2,905,056,229 |
| Ignored files | 53,395 | 740,144,171 |
| Ordinary untracked files | 2 | 79,708 |
| Root `.git` | 220 | 732,207,649 |
| Total | 129,020 | 4,377,487,757 |

Ordinary untracked files are only `artifacts/storage_cleanup_audit.md` (71,109 bytes) and `artifacts/storage_cleanup_phase1_report.md` (8,599 bytes).

Working tree excluding `.git`: **3,645,280,108 bytes**.

### Top-level directories

| Directory | Files | Bytes |
| --- | ---: | ---: |
| `artifacts/` | 82,090 | 2,764,637,025 |
| `.git/` | 220 | 732,207,649 |
| `development/` | 27,317 | 461,951,461 |
| `handoff/` | 479 | 186,508,635 |
| `.venv/` | 5,951 | 56,291,644 |
| `.venv-broken/` | 5,207 | 54,357,446 |
| `venv/` | 5,390 | 49,494,117 |
| `history/` | 7 | 29,392,884 |
| `tests/` | 842 | 14,128,301 |
| `docs/` | 618 | 7,833,510 |
| `game/` | 219 | 6,736,556 |
| `audits/` | 63 | 6,426,772 |
| `tools/` | 274 | 3,963,830 |
| `data/` | 150 | 1,218,696 |
| `experiments/` | 108 | 1,203,075 |

`development/tmp/` itself is 40 children, 457,832,342 bytes. The rest of `development/` is about 4.1 MB of campaign and report files.

### `.git` components

| Path | Files | Bytes |
| --- | ---: | ---: |
| `.git/cursor/` | 7 | 407,712,529 |
| `.git/objects/` | 170 | 312,071,957 |
| `.git` root files, including the index | 7 | 12,392,497 |
| `.git/hooks/` | 14 | 25,827 |
| `.git/info/` | 2 | 2,201 |
| `.git/logs/` | 9 | 2,198 |
| `.git/refs/` | 11 | 440 |

`git count-objects -v` still reports 48,165 packed objects in 35 packs, size-pack 303,667 KiB, 62 loose objects, and **one garbage object**: `.git/objects/92/tmp_obj_xKdgkS` (56,498 bytes). It was left untouched.

## 3. Phase 1 savings verification

Phase 1 final project size was 4,377,470,981 bytes, with root `.git` at 732,190,873 bytes. This measurement is 4,377,487,757 bytes. The difference is **16,776 bytes, entirely inside `.git`**. The working tree excluding `.git` is still 3,645,280,108 bytes.

| Check | Result |
| --- | --- |
| Branch and HEAD | Unchanged: `feature/product-realization`, `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Tracked file count and tracked bytes | 75,403 files, 2,905,056,229 bytes, same as the original audit |
| All 44 Category A2 roots | Absent |
| Category A5 metrics files | Absent |
| 66 source-missing bytecode exceptions | All present, 2,664,536 bytes |
| Five bytecode files Phase 1 deliberately kept | All present |
| Seven files excluded from the Category B archive | All present and tracked, 524,136 bytes |
| Source-backed `__pycache__` outside environments and `development/tmp` | Not regenerated. The 71 remaining files are the 66 exceptions plus the five kept files (2,873,036 bytes) |
| `.pytest_cache/` | Directory exists and contains 0 files |
| `artifacts/pr_eg_r6_r5/snapshots/` | Present, 2,952 files, 147,800,156 bytes |

Category A remains complete. No new project-file accumulation was found after the Phase 1 report. `development/tmp/storage_cleanup_phase1_control/` (65 files, 17,652,087 bytes) was created during Phase 1 and is already inside that final size.

### `.git/cursor/` did not keep growing

Phase 1 reported `.git/cursor/` at 407,712,529 bytes, up 328,354,559 bytes from the original audit's 79,357,970 bytes. This phase measured the same **407,712,529 bytes at the start and at the end** of a 132-second read-only walk. The growth is one additional Cursor crepe index for the current commit, retained beside the previous commit's index:

| Crepe commit directory | Role | Bytes |
| --- | --- | ---: |
| `bc7fa3b8568e42f853434d8b1a4067b19289760f` | Previous index (`index.bin` 37,568,744 + `postings.bin` 41,789,194 + metadata) | 79,357,970 |
| `c16d922865b7182d47b87d27ec633f9308f1ef4c` | Current HEAD index (`index.bin` 72,342,516 + `postings.bin` 256,012,011 + metadata) | 328,354,559 |

Those two sums plus a zero-byte `build.lock` equal the directory total. This is local IDE metadata. It is not pushed project content. It was not modified. Whether Cursor later drops the older commit index was not tested. Manual deletion inside `.git` is not recommended.

The extra 16,776 bytes elsewhere in `.git` since the Phase 1 report were not attributed to a single file. They are not another crepe index.

## 4. Category C candidate inventory

Parent totals below overlap their children when noted. Savings in section 1 do not use these overlapping figures.

| Candidate | Files | Bytes | Git |
| --- | ---: | ---: | --- |
| Artifact directories whose own name contains `tmp` | 34,631 | 561,490,288 | 31,136 tracked files / 496,730,806 bytes; the rest ignored |
| Additional tracked scratch not named `tmp`: two `pytest_basetemp` trees, `pytest_local`, `pytest_representative` | 750 | 26,839,670 | Tracked |
| Ignored `pytest_reg` roots still present | 1,621 | 41,137,759 | Ignored |
| `development/tmp/github_checkpoint/` | 16,468 | 305,306,441 | Ignored |
| of which `baseline_4320bcd/` | 16,372 | 285,295,386 | Ignored nested checkout |
| `development/tmp/maintenance_ci_venv/` | 7,088 | 63,307,128 | Ignored |
| `.venv-broken/` | 5,207 | 54,357,446 | 2,663 tracked / 24,397,647 bytes; remainder ignored |
| `venv/` | 5,390 | 49,494,117 | Ignored |
| `development/tmp/pr_play_05/` after Category A1 | 2,267 | 38,888,302 | Ignored |
| Other `development/tmp` children outside the large roots above and outside the Phase 1 control directory | — | 32,678,384 | Ignored |
| `disposable_state/` trees under `artifacts/` | 531 | 20,310,198 | Tracked |
| Source snapshot directories (`sources/`, `before_sources/`, `source_snapshots/`) | 205 | 12,834,563 | Tracked campaign evidence |
| Orphan bytecode | 66 | 2,664,536 | Ignored |
| Seven Category B neighbors | 7 | 524,136 | Tracked |
| Duplicate ZIP excess | 47 groups | 74,214,968 excess | Mostly tracked; Git blob already shared |
| `.git/cursor/` | 7 | 407,712,529 | Local Git metadata |

The original audit's tracked temporary-looking total was 525,528,202 bytes. This phase measured 523,570,476 bytes of tracked pytest-scratch directories (the `tmp` set plus the four additional basetemp/local/representative directories). The remaining **1,957,726 bytes** were not tied to a directory of that shape. They stay unresolved rather than being assigned a cleanup class.

`development/tmp/` sum of all 40 children is 457,832,342 bytes. Named pieces: checkpoint 305,306,441; maintenance venv 63,307,128; `pr_play_05` 38,888,302; Phase 1 control 17,652,087; `pr_play_02_entry_surface` 12,436,235. The other children total 20,242,149 bytes. The 32,678,384 figure in the table is `pr_play_02_entry_surface` plus those other children.

## 5. Tracked temporary-artifact analysis

### What these directories are

Every non-empty `tmp` directory except one small isolation folder is a pytest case store. Its children are directories named `test_*`. A representative case, `artifacts/pr_eg_r4_r1/tmp_baseline/test_action_and_chat_investiga0/`, contains only:

- `data/campaign.json`, `character.json`, `combat.json`, `conditions.json`
- `data/session.json` (166,580 bytes) and `data/session_log.jsonl` (177,909 bytes)
- `data/world.json` and one scene file

Extension mass across the `tmp` roots is `.json` (about 412 MB) and `.jsonl` (about 148 MB). The exception with other types is `artifacts/pr_eg_r6_r4_r1/focused_tmp` (55 files, 1,571,820 bytes): 21 markdown files, 12 zip files, 16 JSON files, and 5 Python files, still under `test_*` children from review-bundle tests. One 14-byte untracked file sits in that tree; the other 54 files are tracked.

`artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` is the other shape exception: its only child is `prbr-session-isolation-1_wnyq47` (10 files, 18,195 bytes, ignored). It is not a `test_*` store.

### Which campaigns created them

| Trees | Campaign | How they were produced | Campaign state |
| --- | --- | --- | --- |
| `artifacts/pr_eg_r4_r1/tmp_*` | PR-EG-R4-R1 delivery integrity | `tools/qualify_pr_eg_r4_r1.py` passes `--basetemp=artifacts/pr_eg_r4_r1/tmp_{label}` while running a saved regression selection. Provider budget is set to 0. | Complete. Current tests read `failed_first_live/live_turns.json` and import `frozen` / `replay`. They do not read `tmp_*`. |
| `artifacts/pr_eg_r4/pytest_tmp` | PR-EG-R4 | `tools/qualify_pr_eg_r4.py` basetemp. Ignored by `artifacts/**/pytest_tmp*`. | Complete. Output left on disk. |
| `artifacts/pr_eg_r2c*/**/*tmp*` | PR-EG-R2C, R2C-R1, R2C-R2 | Runners such as `artifacts/pr_eg_r2c_r1/run_baseline.py` pass `--basetemp` at `baseline_verified_tmp`. `artifacts/pr_eg_r2c/build_review.py` excludes `baseline_tmp`, `baseline_local_tmp`, `post_tmp`, `post_final_tmp`, `final_tmp`, and `target_tmp` from the review package. | Complete. Live tests read `frozen_holdouts.json`, `freeze.json`, and the later holdout JSON files. They do not read these stores. |
| `artifacts/pr_eg_r2/pytest_tmp`, `pytest_local` | PR-EG-R2 | Package scripts exclude `pytest_tmp` and `pytest_local` from review inventories. | Complete. |
| `artifacts/pr_eg_r6_r4*/**/*tmp*` | PR-EG-R6-R4 / R4-R1 correspondence experiments | Pytest stores, including review-zip generation tests. | Complete as experiments. Runtime imports are the experiment modules, not these stores. |
| `artifacts/pr_bt_.../pytest_basetemp`, `artifacts/pr_ck_.../pytest_basetemp` | PR-BT and PR-CK | Names are pytest basetemp directories. `pytest_basetemp` is not covered by the current ignore rules, so the files were committed. | No current test reads these stores. Treated as the same scratch class, with less script-level documentation than the PR-EG trees. |

`artifacts/pr_eg_r5/investigate.py` defines `protected()` as a hash of every file under `game`, `data`, `tests`, `experiments`, `artifacts/pr_eg_r4`, and `artifacts/pr_eg_r4_r1`, skipping only `__pycache__` and `.pytest_cache`. `artifacts/pr_eg_r5/baseline.json` stores that map. It contains hashes for the `tmp_*` files because they lived inside `artifacts/pr_eg_r4_r1` when the snapshot was taken. `verify_bundle.py` and `build_reports.py` compare that map to a fresh walk. Those scripts are not imported by `tests/`. Re-running them today would already fail because `game/`, `data/`, and `tests/` have changed since 2026-10-17. Deleting the tmp trees would add those paths to an already stale check. The hash record remains inside `baseline.json` either way.

No reference in `tests/`, `game/`, `tools/` (except the basetemp writers), `experiments/`, `scripts/`, `docs/`, `.github/`, or `data/` opens these directory paths as inputs. Matches that do exist are `--basetemp` writers, review exclusion sets, the R5 hash walk, and this audit's predecessor report.

### Reproducibility and Git

Re-running the qualification scripts would create a new store. It would not recreate these bytes: the scripts copy or mutate whatever the tests do on the source tree that is current at run time, and several of them can spend provider budget if invoked as live qualification. The retained evidence of those campaigns is the sibling JUnit XML, consoles, `live_turns.json`, `live_qualification.json`, freeze files, and review ZIPs. Those siblings were not classified for deletion.

Index blob ids show limited Git-level duplication inside the tmp set: 77 blobs are shared by multiple tmp paths (22,473 extra paths, 33,932,155 excess logical bytes). 55 of the tmp blobs also exist at another index path, covering 30,991,450 tmp bytes. Those two observations overlap. They mean Git already stores one blob. They are not an additional savings line.

No non-empty tmp tree is an exact structural duplicate of another. The only exact group is five empty directories.

## 6. Duplicate-content findings

SHA-256 was computed for every regular file in the 61 `tmp` roots, for `data/`, `tests/fixtures/`, `game/*.py`, and for every `.zip` outside `.git` and the three virtual environments.

### A. Exact duplicates

| Set | Result |
| --- | --- |
| Non-empty tmp trees | No exact tree match. Shared files are repeated canonical seeds, not whole-tree copies. |
| Unique tmp content | 9,588 files, 522,977,676 bytes appear once in the tmp set and do not match current `data/`, fixtures, or `game/*.py`. |
| ZIP files | 457 files, 264,262,393 bytes, 47 duplicate-content groups, **74,214,968 excess logical bytes**. |

Largest ZIP groups:

| Copies | Excess bytes | Tracked copies | Paths |
| --- | ---: | ---: | --- |
| 3 | 15,081,628 | 3 | `handoff/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip`; `artifacts/pr_eg_r2c_r2/predecessor_current_review/CURRENT_REVIEW.zip`; `artifacts/pr_eg_r2c_r1/review_staging/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip` |
| 2 | 8,229,096 | 2 | `handoff/history/pr_eg_r4_r1_final_delivery_integrity_20261017/REVIEW.zip`; `handoff/history/pr_eg_r5_predecessor_before_reassessment/CURRENT_REVIEW.zip` |
| 3 | 7,593,952 | 3 | `handoff/CURRENT_REVIEW.zip`; `handoff/CURRENT_REVIEW(20261031-141539).zip`; `handoff/history/pr_play_12/REVIEW.zip` |
| 2 | 6,598,350 | 2 | `handoff/history/pr_eg_r5_conversational_architecture_reassessment_20261017/REVIEW.zip`; `artifacts/pr_eg_r5/package_staging/CURRENT_REVIEW.zip` |
| 2 | 5,289,542 | 2 | `handoff/history/pr_eg_r4_conversational_playability_20261017/REVIEW.zip`; `handoff/history/pr_eg_r4_before_r1/CURRENT_REVIEW.zip` |

The third group is the current PR-PLAY-12 review package. It stays. The other groups are historical aliases: a canonical `handoff/history/` package plus a staging copy under `artifacts/`. Working-tree deletion of a staging copy would save the excess bytes. GitHub would not gain a new object-store reduction, because the identical blob is already shared. Path consumers inside older review markdown cite `support/` members and canonical source paths. A later consolidation still has to check those citations before removing a specific path. That is C3, and it is a separate migration from the pytest stores.

### B. Semantically similar, not duplicates

`tmp_baseline` (37,718,667 bytes) and `artifacts/pr_eg_r4/pytest_tmp` (37,718,668 bytes) are one byte apart and both have 640 globally unique files. They are not copies of each other. Before-fix and after-fix stores (`tmp_baseline` vs `tmp_repaired`, `baseline_tmp` vs `final_tmp`) differ in the mutated session files. Similarity of directory shape is not redundancy.

### C. Different historical states

Each large store's unique tens of megabytes are per-test `session.json` and `session_log.jsonl` contents from that run. They are not interchangeable.

### D. Unique evidence kept out of the duplicate claim

`artifacts/pr_eg_r6_r5/snapshots/` (147,800,156 bytes) was hashed only as a protected control, not as a duplicate candidate. `experiments/pr_eg_r6_r5/run.py` restores those pre-turn snapshots. Source snapshots that differ from current `game/` are unique historical source, even when the directory name looks like a copy.

Source snapshot comparison against the current tree:

| Outcome | Python files |
| --- | ---: |
| Byte-identical to the current counterpart | 107 |
| Different from the current counterpart | 79 |
| No current counterpart | 4 |

Identical files include the current PR-PLAY-10, PR-PLAY-11, and PR-PLAY-12 snapshots. They still document the reviewed source if the working tree changes later. They are C5. Total snapshot bytes are 12,834,563, which is not a meaningful storage win beside the pytest stores.

## 7. Historical environment findings

### `development/tmp/github_checkpoint/`

`docs/maintenance/protected_replay_ci_20261018.md` says command output, JUnit, and baseline comparisons stay here. Golden-replay reports cite `development/tmp/github_checkpoint/golden_after.xml` as the JUnit path of a recorded command.

The directory splits:

| Piece | Files | Bytes | Finding |
| --- | ---: | ---: | --- |
| `baseline_4320bcd/` | 16,372 | 285,295,386 | Working-tree checkout of commit `4320bcdd50471c744746811f213a60b1893496d2`. No `.git` directory inside it. Every path in that commit is present (15,241 files). |
| Bytecode only in the checkout | 1,064 | 35,207,113 | Not in the commit. C1. |
| Other files only in the checkout | 67 | 1,532,640 | Pytest case stores and `.pytest_cache`, also absent from the commit. |
| Sibling diagnostics | — | 20,011,055 | Diffs, CI JSON, JUnit, payloads. This is the material the maintenance note names. C5. |

Length-matched sample: 80/80 files matched the commit blob id. Four text files that differed in length (`.gitignore`, `Makefile`, `game/api.py`, `data/session.json`) matched after CRLF-to-LF normalization. `.github/workflows/convergence-checks.yml` did not: the checkout has a local workflow edit that is already present in current HEAD (`ASHEN_PROTECTED_REPLAY_REPORT_PATH`). The committed form of that file remains available from `4320bcd`. A full normalized diff of all 15,070 length-mismatched paths was not run. Restoration of the commit is `git checkout 4320bcdd50471c744746811f213a60b1893496d2` or `git archive`. Restoration of the exact CRLF checkout is not that command. Classification of the checkout, after the bytecode is set aside, is C2.

### `development/tmp/maintenance_ci_venv/`

Ignored. 7,088 files, 63,307,128 bytes. Python environment with a newer resolution than active `.venv`: FastAPI 0.146.0, OpenAI 3.35.1, pytest 9.1.1, plus `opentelemetry_api`, `truststore`, `httpx2`, and `httpcore2`. Active `.venv` has FastAPI 0.140.0 and OpenAI 2.48.0. `requirements.txt` is not a lockfile, so deleting this tree loses a concrete install unless the dist-info names in Appendix C are kept. No runtime script was found that points at this interpreter. C2 after that list is accepted as the record.

### `.venv-broken/`

5,207 files, 54,357,446 bytes. `pyvenv.cfg` says Python 3.12.0 and records the create command as `python -m venv` of `.venv`. This is a renamed earlier `.venv`, not a second interpreter. Installed distributions are the same libraries as `.venv` at older versions (FastAPI 0.135.3, OpenAI 2.30.0, pytest 9.0.2). See Appendix C.

`.gitignore` ignores `.venv-broken/`, but **2,663 files / 24,397,647 bytes remain tracked**. Ignore rules do not remove index entries. Those tracked files should eventually leave the index with `git rm -r --cached .venv-broken` in an ordinary commit. That was not done here. History will still contain the blobs. The ignored remainder is 29,959,799 bytes and can leave the working tree only after the package list is accepted. Do not touch active `.venv` (5,951 files, 56,291,644 bytes, Python 3.12, the interpreter documented in `docs/README.md` and selected by `scripts/run_live_playtest.ps1`).

### `venv/`

Ignored. 5,390 files, 49,494,117 bytes. Python 3.9.13, virtualenv 20.24.5. FastAPI 0.128.8, pytest 8.4.2, OpenAI 2.28.0. `.idea/misc.xml` still sets the project SDK to `Python 3.9 (ashen_thrones_ai_gm)`. `.idea/` is ignored, but the SDK name is a live local dependency. C4 until that SDK is pointed at `.venv`. Removing `venv/` would not change GitHub.

### Referenced ignored pytest roots

Phase 1 removed 44 unreferenced ignored pytest roots. These cited roots remain:

| Path | Files | Bytes | Why it was not in Category A |
| --- | ---: | ---: | --- |
| `artifacts/prar_pytest_reg1/` | 1,117 | 27,617,175 | `development/campaigns/product_realization/PR-AR_perception_narration_authority_audible_non_invention.md` cites it as the passing run location |
| `artifacts/praq_pytest_reg2/` | 503 | 13,519,683 | `PR-AQ_physical_action_typing_compound_perception_realization.md` cites it the same way |
| `artifacts/prar_pytest_reg2/` | 1 | 901 | Ignored sibling; not separately cited in this pass |

They are pytest case stores, ignored, and not read by current tests. The campaign sentences are pointers, not loaders. C2: zip them before deletion so the cited path can be restored. They are not C1, because the reports name the directories and the case contents are not byte-identical to another retained tree.

Other ignored `pytest_tmp` directories of the same shape (including `artifacts/pr_eg_r4/pytest_tmp` at 37,718,668 bytes) are included in the C2 local pytest total. `artifacts/pr_cf_regression_triage/pytest_representative/` is tracked (8 files, 11,021 bytes) and is in the tracked scratch total.

### Source-missing bytecode

All 66 Appendix C paths from the original audit still exist (2,664,536 bytes). They stay C4. Deleting a `__pycache__` directory wholesale would remove them. The checkpoint bytecode in C1 is a different tree.

## 8. Protected dependency findings

These Category C paths are inputs or explicit retention targets. They are C5.

| Protected material | Category C overlap | Why it stays |
| --- | --- | --- |
| `game/`, `static/`, `scripts/`, `tools/`, `experiments/` modules imported at runtime | None of the tmp stores | `game/live_chat_interpretation.py` imports `experiments.pr_do`, `pr_dp`, and `pr_dr`. |
| `data/` canonical campaign | None | Tests seed copies; they do not read the tmp stores as the canonical save. |
| `data/validation/atgb/` and `artifacts/atgb/` | None deleted or proposed | Phase 1 preservation check still applies. This phase did not reclassify ATGB. |
| `artifacts/pr_eg_r6_r5/snapshots/` | Not a tmp directory | `experiments/pr_eg_r6_r5/run.py` restores `OUT/snapshots`. 2,952 files, 147,800,156 bytes. |
| Golden replay manifests and fixtures | None | Only the two local metrics files were Category A, and they are still absent. |
| PR-EG tests that read artifact JSON | Sibling evidence, not the tmp stores | `tests/test_pr_eg_r2c_speech_adoption.py` reads `frozen_holdouts.json` and `freeze.json`. `tests/test_pr_eg_r2c_r2_reference_eligibility.py` reads the holdout and freeze files. `tests/test_pr_eg_r4_r1_delivery_integrity.py` reads `failed_first_live/live_turns.json`. |
| Current PR-PLAY evidence and `handoff/CURRENT_REVIEW.zip` | The duplicate ZIP group of three | Same hash as the timestamped copy and `handoff/history/pr_play_12/REVIEW.zip`. Keep all three while that review stands. |
| Source snapshots for PR-EG and PR-PLAY | 12,834,563 bytes | 79 Python files differ from current source. Review-time attestation. |
| Seven files missing from the R2C-R2 review ZIP | 524,136 bytes | Usage logs, `clarification_probe.json`, and `conversational_continuity.py` are not in `handoff/history/pr_eg_r2c_r2_reference_eligibility_20261017/REVIEW.zip`. |
| Phase 1 control directory | 17,652,087 bytes | The Phase 1 report says it is retained for review. |
| Checkpoint diagnostics beside the nested checkout | 20,011,055 bytes | Named by the maintenance note. |
| Active `.venv` | 56,291,644 bytes | Documented runtime. |
| `docs/NEXT_SESSION.md` and standing docs | Not in the candidate byte totals | Not modified. |

`disposable_state/` (20,310,198 tracked bytes under the PR-EG artifact trees) is excluded from review ZIPs by the campaign packagers and is also the directory those live runners write. This phase did not prove the live JSON transcripts fully replace those session directories. C4, not C5 and not C2.

`development/tmp/pr_play_05/pre04/` is 38,673,558 of the 38,888,302 bytes left under `pr_play_05` after Category A1. `artifacts/pr_play_05/prepare_comparison.py` builds that overlay by copying the current `game/`, `tests/`, `static/`, `data/`, and `docs/` trees and then patching `game/api.py` from PR-PLAY-02 sources. A rerun today would not reproduce the saved overlay. `comparison_provenance.json` records the API hash. The overlay itself is C4.

No Category C candidate in the C1 or C2 lists is consumed by ATGB human-review tests, golden replay fixtures, or the PR-PLAY regression paths identified in the original audit.

## 9. Artifact-generation and retention analysis

Current intended sink: `pytest.ini` sets `--basetemp=development/tmp/pytest`, and `development/tmp/` is ignored. CI creates that parent because a fresh checkout does not contain it. That path is temporary.

Historical generators wrote the same kind of store under `artifacts/`, using names the ignore rules do not cover (`tmp_baseline`, `final_tmp`, `baseline_local_tmp`, `pytest_basetemp`, `pytest_local`, `pytest_representative`). Review builders then excluded those names from ZIPs, but a broad add of the artifact directory still committed the stores. Ignore rules added later did not untrack them.

| Output | Role | Retention today |
| --- | --- | --- |
| Pytest case stores under `development/tmp/pytest` | Disposable execution | Temporary. Category A1 already cleared older `test_*` files there. |
| Pytest case stores committed under `artifacts/**/tmp*` and `pytest_basetemp` | Same mechanism, wrong directory, then committed | C2. History is the archive for tracked copies. |
| JUnit, consoles, freeze files, `live_turns.json`, `live_qualification.json` | Campaign result | Pinned or review evidence. Not in the C2 scope. |
| `disposable_state/` | Live-run data directory, excluded from ZIPs | C4 until compared with the live transcripts. |
| `artifacts/pr_eg_r6_r5/snapshots/` | Counterfactual replay input | Pinned. |
| Review ZIPs and `handoff/history/` | Human review packages | Current package is current. Older staging copies are C3. |
| `sources/` and `source_snapshots/` | Source at review time | Pinned. |
| Failed-test diagnostics and Phase 1 control output | Investigation record | Review until accepted. |
| `__pycache__` next to source | Import cache | Temporary, except the 66 source-missing files. |
| Virtual environments | Local installs | Current `.venv` is current. Others are archival or IDE-dependent. |
| Provider usage JSONL beside live runs | Accounting for a real call | Pinned with the live evidence. Not regenerable. |

## 10. Proposed retention policy

Do not implement automatic deletion. Introduce the policy by placement and by explicit pin lists.

| Class | Meaning | Rule that does not break current contracts |
| --- | --- | --- |
| Temporary | Regenerated by pytest, import, or a documented script from pinned inputs | New runs use `development/tmp/` only. Do not add a broad `artifacts/` or `*.json` ignore. After the tracked stores leave the index, narrow ignore names can cover `pytest_basetemp`, `pytest_local`, and `pytest_representative`. |
| Review | Needed until a campaign's review is accepted | Keep JUnit, consoles, live transcripts, usage logs, and the current `handoff/CURRENT_REVIEW.*` set. A ZIP counts as coverage only when every member hash has been compared, which is how Category B was limited to 33 files. |
| Archived | Still historically real, not needed in the working tree | For tracked files, the deletion commit's parent is the archive. Record that SHA in the commit message. For ignored files, zip first. Restoration is `git checkout <sha> -- <path>` or unzip. |
| Pinned | Current tests, replay, ATGB, or canonical state | Path stays. Moving it is a migration with tests, not a cleanup commit. Includes `snapshots/`, freeze and holdout JSON, `failed_first_live/`, golden replay fixtures, `data/validation/atgb/`, and referenced `automated_playtests` runs. |
| Current | Active campaign and the documented environment | PR-PLAY-12 evidence, `docs/NEXT_SESSION.md`, `data/`, `.venv`. |

Historical scripts that still pass `--basetemp` under `artifacts/` should be left alone until someone intends to rerun them. Changing those paths is a migration. Rerunning them is not required to delete old stores, because the scripts create the directory rather than reading the old one.

A soft size warning on `development/tmp/` can be added later. It must not delete pinned evidence, the Phase 1 control directory, or the checkpoint diagnostics.

## 11. Cleanup classification table

| Path | Files | Bytes | Git | Class | Evidence | Dependencies | Savings | Consequence | Confidence |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| `development/tmp/github_checkpoint/baseline_4320bcd/**/__pycache__` and `*.pyc` | 1,064 | 35,207,113 | Ignored | C1 | Not in commit `4320bcd`. Snapshot still has the `.py` files. | None. Distinct from the 66 repo-root orphan bytecode files. | 35,207,113 local | Cold import if Python is run inside the snapshot | High |
| Empty ignored dirs `artifacts/prak_pytest_tmp`, `artifacts/prao_pytest_tmp` | 0 | 0 | Ignored | C1 | No files | None found | 0 | None | High |
| Tracked `tmp` directories in Appendix A with `tracked_bytes` > 0 | 31,136 | 496,730,806 | Tracked | C2 | Pytest `test_*` stores. Writers and review exclusions found. No current test reader. 93% unique bytes, so not C3. | R5 `protected()` hashes the R4-R1 subset. That check is already stale and is not in `tests/`. | 496,730,806 future checkout. History retains blobs. | Loses on-disk post-test session copies. JUnit and live JSON siblings remain. `git checkout c16d922 -- <path>` restores. | Medium-high |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp` | 393 | 21,144,219 | Tracked | C2 | Pytest basetemp. Ignore rules missed the name. | No reader found in tests or experiments. Less campaign documentation than PR-EG. | Included in the tracked scratch total | Same restore rule | Medium |
| `artifacts/pr_ck_resolver_selection/pytest_basetemp` | 88 | 2,230,424 | Tracked | C2 | Same | No reader found | Same | Same | Medium |
| `artifacts/pr_eg_r2/pytest_local` | 261 | 3,454,006 | Tracked | C2 | Review packager excludes `pytest_local` | No reader found | Same | Same | Medium-high |
| `artifacts/pr_cf_regression_triage/pytest_representative` | 8 | 11,021 | Tracked | C2 | Small pytest output, name not ignored | No reader found | Same | Same | Medium |
| Ignored `pytest_tmp` / `pytest_reg` stores of `test_*` files, including `artifacts/pr_eg_r4/pytest_tmp`, `artifacts/prar_pytest_reg1`, `artifacts/praq_pytest_reg2` | — | 105,879,032 | Ignored | C2 | Same case-store shape. PR-AR and PR-AQ docs cite two reg directories as where a run passed. | Citations are documentary. Git does not have the bytes. | 105,879,032 local after a zip | Cited paths 404 until restored from the zip | Medium-high |
| `baseline_4320bcd/` excluding its bytecode | 15,308 | 250,088,273 | Ignored | C2 | Superset of commit `4320bcd` plus small pytest debris. Sampled text matches after newline normalization, with one workflow delta already in HEAD. | Maintenance note retains the sibling diagnostics, not this second checkout. | 250,088,273 local | Exact CRLF bytes are not what `git checkout` writes. Commit content remains. | Medium |
| `development/tmp/maintenance_ci_venv/` | 7,088 | 63,307,128 | Ignored | C2 | Newer than `.venv`. Package names recorded in Appendix C. | No launcher reference found | 63,307,128 local | Cannot reproduce the install if those package versions leave PyPI and no wheelhouse was saved | Medium |
| `.venv-broken/` ignored files | — | 29,959,799 | Ignored | C2 | Older pins of the same 3.12 stack. Appendix C. | Not the documented interpreter | 29,959,799 local | Same PyPI caveat | Medium |
| `.venv-broken/` tracked files | 2,663 | 24,397,647 | Tracked | C2 | Committed before the ignore rule | Index only. Active `.venv` is separate. | 24,397,647 future checkout | `git rm --cached` plus deletion. History keeps blobs. | High for the index action |
| Duplicate ZIPs outside the current PR-PLAY-12 trio | 47 groups total | 66,621,016 excess outside that trio | Mostly tracked | C3 | SHA-256 equality | History paths and staging paths are different citation targets. Current trio is C5. | Working tree only. Git blob already shared. | Broken links if a staging path is cited | Medium |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` | 10 | 18,195 | Ignored | C4 | Child is `prbr-session-isolation-1_wnyq47`, not `test_*` | Not fully traced | — | — | Low |
| `development/tmp/pr_play_05/` | 2,267 | 38,888,302 | Ignored | C4 | `pre04/` is a historical source overlay. `prepare_comparison.py` would rebuild it from today's tree. | Provenance JSON is separate and stays. | — | A rerun is not a restore | Medium |
| `development/tmp/pr_play_02_entry_surface/` | 391 | 12,436,235 | Ignored | C4 | Left after A1 because it is not under `test_*` | Not traced file by file | — | — | Low |
| Other smaller `development/tmp` children | — | 20,242,149 | Ignored | C4 | Profiles, export copies, isolation runtimes, suite logs | Mixed | — | May include the only local copy of a diagnostic log | Low |
| `disposable_state/` under PR-EG artifacts | 531 | 20,310,198 | Tracked | C4 | Live runners write it; review ZIPs exclude it | Not hash-compared to `live_qualification.json` | — | Might be the only raw session directory for a live run | Low |
| `venv/` | 5,390 | 49,494,117 | Ignored | C4 | Python 3.9 env | `.idea/misc.xml` SDK name | 49,494,117 local if the SDK is retargeted | IDE launch break until retargeted | Medium |
| 66 orphan bytecode files | 66 | 2,664,536 | Ignored | C4 | No matching `.py` | Possible sole local copy of a removed module | — | Irreversible without a decompiler | Medium |
| `.git/cursor/` | 7 | 407,712,529 | Git metadata | C4 | Two crepe indexes. Stable since Phase 1. | Cursor-owned | Unknown. Do not delete by hand. | Index or object corruption if `.git` is edited | High that it must not be hand-deleted |
| `.git/objects/92/tmp_obj_xKdgkS` | 1 | 56,498 | Git garbage | C4 | `git count-objects` garbage | Unknown lock or prune state | — | Object store damage if removed casually | High that it must not be hand-deleted |
| Checkpoint sibling diagnostics | — | 20,011,055 | Ignored | C5 | Maintenance note and golden-replay command records | Explicit retention | None | — | High |
| `development/tmp/storage_cleanup_phase1_control/` | 65 | 17,652,087 | Ignored | C5 | Phase 1 validation evidence | Phase 1 report points at it | None until that report is accepted as sufficient | — | High |
| `artifacts/pr_eg_r6_r5/snapshots/` | 2,952 | 147,800,156 | Tracked | C5 | Replay restore | `experiments/pr_eg_r6_r5/run.py` | None | Replay breakage | High |
| Source snapshots | 205 | 12,834,563 | Tracked | C5 | 79 Python files differ from current source | Review attestation | None | Lost preimage of a reviewed change | High |
| Seven B-neighbor files | 7 | 524,136 | Tracked | C5 | Absent from the verified ZIP | Unique usage and probe content | None | Evidence loss | High |
| Current PR-PLAY-12 ZIP trio | 3 | 7,593,952 excess | Tracked | C5 | Identical bytes, three required paths | Current handoff | None | Review surface loss | High |
| Active `.venv/` | 5,951 | 56,291,644 | Ignored | C5 | Documented runtime | README and playtest script | None | Broken local launch | High |

C2 tracked checkout total: 496,730,806 + 21,144,219 + 2,230,424 + 3,454,006 + 11,021 + 24,397,647 = **547,968,123**.

C2 local total: 105,879,032 + 250,088,273 + 63,307,128 + 29,959,799 = **449,234,232**.

C4 byte total in section 1 (144,053,732) is `venv` + `pr_play_05` + `pr_play_02_entry_surface` + other `development/tmp` children + `disposable_state` + orphan bytecode + the 18,195-byte isolation directory. It excludes `.git/cursor/` and the garbage object so IDE metadata is not presented as project-file waste.

## 12. Estimated recoverable storage

| Bucket | Bytes | Verified or estimated | Counts toward |
| --- | ---: | --- | --- |
| Immediately removable local | 35,207,113 | Verified file count and size | C1 |
| Conditionally archivable local | 449,234,232 | Verified sizes. Archive step not done. Checkpoint newline identity is sampled, not exhaustive. | C2 local |
| Tracked working-tree reduction | 547,968,123 | Verified tracked sizes. Requires a later commit. | Future checkout only |
| Existing GitHub object storage | 0 from the actions above | History, packs, and reflogs keep current blobs | Not claimed |
| Further investigation | 144,053,732 project files, plus 407,712,529 `.git/cursor` | Sizes verified. Safety not verified. | C4 |
| ZIP working-tree excess outside the current review trio | 66,621,016 | SHA-256 verified. Not added to the rows above. | C3 |

No row is included in another row. Removing C1 bytecode and then removing the rest of `baseline_4320bcd` is 35,207,113 + 250,088,273 = 285,295,386, which is the whole nested checkout. Tracked C2 does not include ignored C2.

If C1 and all C2 local and the tracked deletion commit were later done, local logical bytes would drop by 35,207,113 + 449,234,232 + 547,968,123 = **1,032,409,468** (about 984.6 MiB). About 548.0 MiB of that is tracked checkout size. About 484.4 MiB is ignored local files. GitHub's stored history would be unchanged.

## 13. Recommended cleanup sequence

Do not run this sequence as part of the current task.

1. **Local bytecode inside the checkpoint (C1).** Delete only `*.pyc` and `__pycache__` files under `development/tmp/github_checkpoint/baseline_4320bcd/`. Expected release: 35,207,113 bytes, 1,064 files. No Git change. Preservation: do not delete `.py` files there, and do not delete the 66 orphan bytecode files elsewhere. Validation: recount files; confirm `game/api.py` still exists in the snapshot. Rollback: not available from Git, because these files are untracked bytecode. Skip this step if that irreversibility is unacceptable; the files are only an import cache.

2. **Tracked pytest basetemp directories (C2, ordinary commit).** Scope is Appendix A where `tracked_bytes` > 0, plus:
   - `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp/`
   - `artifacts/pr_ck_resolver_selection/pytest_basetemp/`
   - `artifacts/pr_eg_r2/pytest_local/`
   - `artifacts/pr_cf_regression_triage/pytest_representative/`
   Expected checkout reduction: 523,570,476 bytes. Git: one new commit on the current branch. Parent `c16d922865b7182d47b87d27ec633f9308f1ef4c` is the archive. No `git filter-repo`, no force-push. Preservation: leave JUnit, live JSON, freeze files, `snapshots/`, and `disposable_state/` in place. Validation: `git diff --stat` limited to those directories; import `game.api`; run `tests/test_pr_eg_r2c_speech_adoption.py`, `tests/test_pr_eg_r2c_r2_reference_eligibility.py`, `tests/test_pr_eg_r4_r1_delivery_integrity.py`, `tests/test_golden_replay_artifact_manifest.py`, and `tests/test_atgb_readiness.py::test_incompatible_baseline_refused_before_store_creation` with provider calls disabled. Do not run `artifacts/pr_eg_r5/verify_bundle.py` or `build_reports.py`. Rollback: `git checkout c16d922865b7182d47b87d27ec633f9308f1ef4c -- <paths>` before the deletion commit is the only history, or `git revert` the deletion commit afterward.

3. **Ignored pytest stores (C2 local).** Zip the ignored `test_*` stores, including `artifacts/pr_eg_r4/pytest_tmp`, `artifacts/prar_pytest_reg1`, and `artifacts/praq_pytest_reg2`, to a location outside the repository or to a designated archive. Verify member paths and hashes, then delete the working copies. Expected release: 105,879,032 bytes. No Git change. Rollback: unzip to the original paths.

4. **Checkpoint checkout (C2 local).** After step 1, remove `baseline_4320bcd/` if the maintainers accept commit `4320bcdd50471c744746811f213a60b1893496d2` as the restore source. Keep the sibling diagnostic files. Expected additional release: 250,088,273 bytes. Rollback of commit content: `git archive` or checkout of that commit. Rollback of the exact CRLF tree: only from a zip taken before deletion.

5. **Maintenance venv and ignored `.venv-broken` files (C2 local).** Appendix C is the package record. Delete the environments only after that record is accepted. Do not delete `.venv`. Expected release: 63,307,128 + 29,959,799 bytes.

6. **Untrack `.venv-broken` (separate ordinary commit).** `git rm -r --cached .venv-broken`. Expected future checkout reduction: 24,397,647 bytes. History unchanged. Rollback: `git checkout c16d922 -- .venv-broken` from the parent, understanding the ignore rule will not by itself restore a cached removal once committed; the checkout command from the parent commit will.

7. **Leave C3, C4, and C5 for later passes.** ZIP staging copies, `venv/`, `pre04/`, `disposable_state/`, orphan bytecode, and `.git/cursor/` are not part of steps 1–6.

Steps 1, 3, 4, and 5 change only ignored or untracked local files. Steps 2 and 6 change tracked content and need their own commits. None of them should rewrite history.

## 14. Validation and restoration requirements

A later cleanup must abort if, immediately before deletion, the file count or byte total of a scoped directory differs from Appendix A. Generators must not be running.

Restoration:

| Scope | Procedure |
| --- | --- |
| Tracked pytest stores and tracked `.venv-broken` | `git checkout c16d922865b7182d47b87d27ec633f9308f1ef4c -- <path>` while that commit is still reachable. After a later history rewrite, which is not recommended, this stops working. |
| Ignored pytest stores | Unzip the archive created in step 3 onto the original paths. |
| Checkpoint checkout | `git checkout 4320bcdd50471c744746811f213a60b1893496d2` in a separate worktree, or a pre-deletion zip if CRLF bytes matter. |
| Checkpoint bytecode | Not in Git. Only a pre-deletion copy restores those exact `.pyc` files. Source `.py` files do not require them. |
| Maintenance venv and `.venv-broken` | Recreate with the Appendix C versions if those releases are still installable. Wheels were not saved. |

Tests listed in step 2 are the minimum regression net. They avoid full suites that write fixed artifact sinks. Provider calls stay disabled. This phase did not run those tests, because running them was not required for the audit and several suites write evidence.

## 15. Unresolved risks and questions

- The 1,957,726-byte gap between this phase's tracked scratch directories (523,570,476) and the original temporary-looking total (525,528,202) was not identified as a directory. It is not in the cleanup scope.
- CRLF normalization was sampled, not applied to all 15,070 length-mismatched checkpoint files. One known delta is already in HEAD. Other dirty files in that checkout could still be unique.
- `disposable_state/` was not compared byte-for-byte with `live_qualification.json` or `live_turns.json`.
- `development/tmp/pr_play_02_entry_surface/` and the 20,242,149 bytes of smaller `development/tmp` children were sized and not opened one by one.
- `artifacts/pr_eg_r5/baseline.json` will disagree with a fresh `protected()` walk if the R4-R1 tmp trees disappear. That walk already disagrees because production source moved on. Confirm no external process still runs `verify_bundle.py`.
- Duplicate ZIP consolidation can break a historical citation even when the bytes exist at the canonical `handoff/history/` path.
- `.idea/misc.xml` ties a local SDK name to Python 3.9. This audit did not launch the IDE.
- `.git/cursor/` stability was observed across Phase 1's final number and this phase's start and end. It was not observed across a new commit or an IDE restart. The older crepe index may be reclaimable by Cursor. That was not tested.
- `git count-objects` garbage at `.git/objects/92/tmp_obj_xKdgkS` remains. Do not remove it by hand.
- Package reinstall depends on PyPI still serving the versions in Appendix C. This phase did not download anything.
- Category B (33 archive-backed files, 113,878,270 bytes) was not reopened. The seven neighboring files stay.

## Appendix A — tmp directory inventory

Scope for a later tracked deletion is every regular file in a row whose tracked-byte column is greater than zero, plus the four additional directories in section 13 step 2. Ignored rows are the local zip-then-delete scope when their children are `test_*` stores. Empty rows save nothing. `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` is C4 and is excluded from the C2 byte total even though it appears here.

`Unique files` counts files whose SHA-256 appears once in this set and does not match current `data/`, `tests/fixtures/`, or `game/*.py`.

| Path | Files | Bytes | Tracked files | Tracked bytes | Ignored | test_* children | Unique files | Unique bytes |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `artifacts/pr_eg_r4/pytest_tmp` | 2363 | 37718668 | 0 | 0 | yes | 297/297 | 640 | 35140279 |
| `artifacts/pr_eg_r4_r1/tmp_baseline` | 2363 | 37718667 | 2363 | 37718667 | no | 297/297 | 640 | 35140278 |
| `artifacts/pr_eg_r4_r1/tmp_repaired` | 2363 | 37366234 | 2363 | 37366234 | no | 297/297 | 640 | 34787845 |
| `artifacts/pr_eg_r2c_r2/final_tmp` | 2327 | 36571752 | 2327 | 36571752 | no | 293/293 | 630 | 34026872 |
| `artifacts/pr_eg_r2c_r1/complete_final_tmp` | 1967 | 32946215 | 1967 | 32946215 | no | 253/253 | 563 | 30762329 |
| `artifacts/pr_eg_r2c_r2/baseline_tmp` | 1985 | 32946012 | 1985 | 32946012 | no | 255/255 | 565 | 30748572 |
| `artifacts/pr_eg_r2c_r1/qualification_final_tmp` | 1985 | 32945706 | 1985 | 32945706 | no | 255/255 | 565 | 30748266 |
| `artifacts/pr_eg_r2c/baseline_local_tmp` | 1778 | 30400549 | 1778 | 30400549 | no | 213/213 | 513 | 28503174 |
| `artifacts/pr_eg_r2c_r1/final_verified_tmp` | 1805 | 29269081 | 1805 | 29269081 | no | 242/242 | 518 | 27349447 |
| `artifacts/pr_eg_r2c_r1/final_tmp` | 1805 | 29268025 | 1805 | 29268025 | no | 242/242 | 518 | 27348391 |
| `artifacts/pr_eg_r2c_r1/post_tmp` | 1787 | 29217453 | 1787 | 29217453 | no | 214/214 | 516 | 27311755 |
| `artifacts/pr_eg_r2c_r1/baseline_verified_tmp` | 1787 | 29149459 | 1787 | 29149459 | no | 214/214 | 516 | 27243761 |
| `artifacts/pr_eg_r2c/final_tmp` | 1787 | 29149428 | 1787 | 29149428 | no | 214/214 | 516 | 27243730 |
| `artifacts/pr_eg_r2c/post_tmp` | 1778 | 28660684 | 1778 | 28660684 | no | 213/213 | 513 | 26763309 |
| `artifacts/pr_eg_r2c/post_final_tmp` | 1778 | 28375433 | 1778 | 28375433 | no | 213/213 | 507 | 26478173 |
| `artifacts/pram_pytest_tmp` | 330 | 7885288 | 0 | 0 | yes | 33/33 | 103 | 7329182 |
| `artifacts/prar_pytest_tmp` | 218 | 4831626 | 0 | 0 | yes | 21/21 | 64 | 4483743 |
| `artifacts/pr_eg_r2c_r1/target_final_tmp` | 450 | 4375751 | 450 | 4375751 | no | 76/76 | 93 | 3989784 |
| `artifacts/pr_eg_r2c_r1/target_verified_tmp` | 450 | 4374637 | 450 | 4374637 | no | 76/76 | 93 | 3988670 |
| `artifacts/pr_eg_r4_r1/tmp_focus4` | 306 | 3791286 | 306 | 3791286 | no | 35/35 | 80 | 3525620 |
| `artifacts/pr_eg_r2c_r1/supplementary_final_tmp` | 162 | 3677207 | 162 | 3677207 | no | 11/11 | 45 | 3412955 |
| `artifacts/pr_eg_r2c_r1/supplementary_baseline_tmp` | 162 | 3652740 | 162 | 3652740 | no | 11/11 | 45 | 3388488 |
| `artifacts/pr_eg_r2c_r2/targeted_qualified_tmp` | 342 | 3563076 | 342 | 3563076 | no | 38/38 | 65 | 3215636 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final5` | 134 | 3113147 | 134 | 3113147 | no | 16/16 | 39 | 2996684 |
| `artifacts/pr_eg_r2c_r2/targeted_status_tmp` | 324 | 3018140 | 324 | 3018140 | no | 36/36 | 59 | 2689604 |
| `artifacts/pral_pytest_tmp` | 110 | 2868262 | 0 | 0 | yes | 12/12 | 37 | 2684463 |
| `artifacts/pran_pytest_tmp` | 110 | 2848726 | 0 | 0 | yes | 12/12 | 40 | 2675316 |
| `artifacts/prap_pytest_tmp` | 90 | 2708935 | 0 | 0 | yes | 10/10 | 38 | 2575157 |
| `artifacts/pr_eg_r2c_r1/recall_bypass_tmp` | 161 | 2595505 | 161 | 2595505 | no | 44/44 | 37 | 2420564 |
| `artifacts/pr_eg_r2c_r2/targeted_final_tmp` | 297 | 2198653 | 297 | 2198653 | no | 33/33 | 50 | 1898473 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final4` | 90 | 2102257 | 90 | 2102257 | no | 11/11 | 26 | 2027316 |
| `artifacts/praq_pytest_tmp` | 89 | 2083255 | 0 | 0 | yes | 9/9 | 27 | 1944510 |
| `artifacts/pr_eg_r5/pytest_tmp` | 81 | 1879397 | 0 | 0 | yes | 10/10 | 23 | 1807434 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final2` | 72 | 1839597 | 72 | 1839597 | no | 9/9 | 20 | 1778778 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final` | 72 | 1839024 | 72 | 1839024 | no | 9/9 | 20 | 1778205 |
| `artifacts/pr_eg_r4_r1/tmp_targeted_final3` | 82 | 1838113 | 82 | 1838113 | no | 10/10 | 23 | 1769618 |
| `artifacts/pr_eg_r2c_r1/target_tmp` | 117 | 1750913 | 117 | 1750913 | no | 39/39 | 26 | 1654385 |
| `artifacts/pr_eg_r2c_r1/owners_verified_tmp` | 99 | 1716915 | 99 | 1716915 | no | 11/11 | 24 | 1634323 |
| `artifacts/pr_eg_r6_r4_r1/focused_tmp` | 55 | 1571820 | 54 | 1571806 | no | 11/11 | 31 | 634316 |
| `artifacts/pr_eg_r2c_r2/targeted_tmp` | 270 | 1365009 | 270 | 1365009 | no | 30/30 | 41 | 1093185 |
| `artifacts/prar_pytest_tmp2` | 66 | 1304467 | 0 | 0 | yes | 6/6 | 18 | 1201260 |
| `artifacts/pr_eg_r4_r1/tmp_other_new` | 17 | 820994 | 17 | 820994 | no | 2/2 | 6 | 803141 |
| `artifacts/pr_eg_r2c_r1/owner_tmp` | 36 | 776084 | 36 | 776084 | no | 4/4 | 10 | 745200 |
| `artifacts/pr_eg_r2/pytest_tmp` | 27 | 612649 | 0 | 0 | yes | 3/3 | 7 | 590088 |
| `artifacts/pr_eg_r4_r1/tmp_targeted3` | 18 | 540993 | 18 | 540993 | no | 3/3 | 6 | 526961 |
| `artifacts/pr_eg_r4_r1/tmp_fact6` | 9 | 521465 | 9 | 521465 | no | 1/1 | 3 | 513390 |
| `artifacts/pr_eg_r4_r1/tmp_fact5` | 9 | 508405 | 9 | 508405 | no | 1/1 | 3 | 500330 |
| `artifacts/pr_eg_r2c/target_tmp` | 9 | 292885 | 9 | 292885 | no | 1/1 | 3 | 284562 |
| `artifacts/pr_eg_r2c_r1/focused_tmp` | 9 | 292885 | 9 | 292885 | no | 1/1 | 3 | 284562 |
| `artifacts/pr_eg_r4_r1/tmp_targeted` | 18 | 270801 | 18 | 270801 | no | 3/3 | 5 | 257670 |
| `artifacts/pr_eg_r4_r1/tmp_targeted2` | 18 | 270801 | 18 | 270801 | no | 3/3 | 5 | 257670 |
| `artifacts/pr_eg_r6_r4/test_tmp_workspace` | 18 | 29058 | 18 | 29058 | no | 2/2 | 4 | 11916 |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp` | 10 | 18195 | 0 | 0 | yes | 0/1 | 2 | 4374 |
| `artifacts/pr_eg_r6_r4_r1/regression_tmp` | 18 | 16729 | 18 | 16729 | no | 2/2 | 2 | 1634 |
| `artifacts/pr_eg_r2c/baseline_tmp` | 9 | 10616 | 9 | 10616 | no | 1/1 | 1 | 1164 |
| `artifacts/pr_eg_r2c_r1/baseline_tmp` | 9 | 10616 | 9 | 10616 | no | 1/1 | 1 | 1164 |
| `artifacts/praf_arrival_destination/debug_tmp` | 0 | 0 | 0 | 0 | no | 0/0 | 0 | 0 |
| `artifacts/prak_pytest_tmp` | 0 | 0 | 0 | 0 | yes | 0/0 | 0 | 0 |
| `artifacts/prao_pytest_tmp` | 0 | 0 | 0 | 0 | yes | 0/0 | 0 | 0 |
| `artifacts/test_realization_layer_audit_tmp` | 0 | 0 | 0 | 0 | no | 0/0 | 0 | 0 |
| `artifacts/test_realization_provenance_audit_tmp` | 0 | 0 | 0 | 0 | no | 0/0 | 0 | 0 |

Sum of this table: 34,631 files, 561,490,288 bytes, of which 31,136 files and 496,730,806 bytes are tracked. The operational deletion unit is the directory. A later executor must recount before deleting. Individual file paths are the regular files currently inside these directories; pasting all 34,631 paths into this report would not add a safer scope than the directory boundary plus the recount check.

Additional tracked directories outside this table, included in step 2:

| Path | Files | Bytes |
| --- | ---: | ---: |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp` | 393 | 21,144,219 |
| `artifacts/pr_ck_resolver_selection/pytest_basetemp` | 88 | 2,230,424 |
| `artifacts/pr_eg_r2/pytest_local` | 261 | 3,454,006 |
| `artifacts/pr_cf_regression_triage/pytest_representative` | 8 | 11,021 |

## Appendix B — ignored pytest_reg roots in the C2 local zip

| Path | Files | Bytes |
| --- | ---: | ---: |
| `artifacts/prar_pytest_reg1/` | 1,117 | 27,617,175 |
| `artifacts/praq_pytest_reg2/` | 503 | 13,519,683 |
| `artifacts/prar_pytest_reg2/` | 1 | 901 |

## Appendix C — installed distribution names

These lists are the archive record for the non-active environments. They are directory names under `site-packages`, not a `pip freeze` file, and they were not used to contact any package index.

Active `.venv` (retain): annotated_doc-0.0.4, annotated_types-0.8.0, anyio-4.14.2, certifi-2026.7.22, click-8.4.2, colorama-0.4.6, distro-1.9.0, fastapi-0.140.0, h11-0.16.0, httpcore-1.0.9, httpx-0.28.1, idna-3.18, iniconfig-2.3.0, jiter-0.16.0, openai-2.48.0, packaging-26.2, pip-26.2.1, pluggy-1.6.0, pydantic-2.13.4, pydantic_core-2.46.4, pygments-2.20.0, pytest-9.1.1, python_dotenv-1.2.2, python_multipart-0.0.32, sniffio-1.3.1, starlette-1.3.1, tqdm-4.69.1, typing_extensions-4.16.0, typing_inspection-0.4.2, uvicorn-0.51.0.

`.venv-broken`: annotated_doc-0.0.4, annotated_types-0.7.0, anyio-4.13.0, certifi-2026.2.25, click-8.3.1, colorama-0.4.6, distro-1.9.0, fastapi-0.135.3, h11-0.16.0, httpcore-1.0.9, httpx-0.28.1, idna-3.11, iniconfig-2.3.0, jiter-0.13.0, openai-2.30.0, packaging-26.0, pip-26.1.2, pluggy-1.6.0, pydantic-2.12.5, pydantic_core-2.41.5, pygments-2.20.0, pytest-9.0.2, python_dotenv-1.2.2, python_multipart-0.0.22, sniffio-1.3.1, starlette-1.0.0, tqdm-4.67.3, typing_extensions-4.15.0, typing_inspection-0.4.2, uvicorn-0.42.0.

`development/tmp/maintenance_ci_venv`: annotated_doc-0.0.5, annotated_types-0.8.0, anyio-4.15.1, certifi-2026.10.18, click-8.5.0, colorama-0.4.6, fastapi-0.146.0, h11-0.16.0, httpcore-1.0.9, httpcore2-2.14.0, httpx-0.28.1, httpx2-2.14.0, idna-3.20, iniconfig-2.3.1, jiter-0.17.0, openai-3.35.1, opentelemetry_api-1.45.1, packaging-26.3, pip-25.0.1, pluggy-1.7.0, pydantic-2.14.1, pydantic_core-2.50.1, pygments-2.21.0, pytest-9.1.1, python_dotenv-1.2.4, python_multipart-0.0.32, sniffio-1.3.1, starlette-1.9.0, truststore-0.10.5, typing_extensions-4.16.0, typing_inspection-0.4.4, uvicorn-0.54.0.

`venv` (Python 3.9, C4): annotated_doc-0.0.4, annotated_types-0.7.0, anyio-4.12.1, certifi-2026.2.25, click-8.1.8, colorama-0.4.6, distro-1.9.0, exceptiongroup-1.3.1, fastapi-0.128.8, h11-0.16.0, httpcore-1.0.9, httpx-0.28.1, idna-3.11, iniconfig-2.1.0, jiter-0.13.0, openai-2.28.0, packaging-26.0, pip-26.0.1, pluggy-1.6.0, pydantic-2.12.5, pydantic_core-2.41.5, pygments-2.19.2, pytest-8.4.2, python_dotenv-1.2.1, python_multipart-0.0.20, setuptools-68.2.0, sniffio-1.3.1, starlette-0.49.3, tomli-2.4.0, tqdm-4.67.3, typing_extensions-4.15.0, typing_inspection-0.4.2, uvicorn-0.39.0, wheel-0.41.2.

## Appendix D — checkpoint commit identity

Commit `4320bcdd50471c744746811f213a60b1893496d2` is present in this repository (`git cat-file -t` returned `commit`). The nested directory contains all 15,241 paths from that commit and 1,131 extra paths. Of the extra paths, 1,064 are bytecode (35,207,113 bytes) and the rest are pytest stores and pytest cache (1,532,640 bytes). Sibling files under `development/tmp/github_checkpoint/` outside `baseline_4320bcd/` total 20,011,055 bytes and are C5.

## Audit closeout

Only `artifacts/storage_cleanup_phase2_audit.md` is written for this task. No candidate was deleted, moved, renamed, compressed, or edited. Git history was read, not changed. No cleanup command ran. No provider call was made. Phase 2 cleanup was not started.
