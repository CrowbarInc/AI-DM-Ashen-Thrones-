# Ashen Thrones — Repository Storage & Cleanup Audit

**Audit only — no cleanup performed.**

Date: October 31, 2026 at 3:00:23 PM EDT. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`. Branch: `feature/product-realization`. Revision: `c16d922865b7182d47b87d27ec633f9308f1ef4c`. The worktree was clean at entry; there were no ordinary untracked files. The only authorized write for this audit is this report.

## 1. Findings and recommended priorities

The project contains **5.51 GiB (5,919,390,899 bytes)**, equivalent to 5.919 decimal GB. Most storage is generated evidence and local test stores, rather than application code or Git history.

1. **A — reproducible local output:** 1.76 GiB (1,888,256,124 bytes) across 96,148 ignored files. These are selected pytest case stores, 44 unreferenced ignored artifact test-run directories, bytecode with source files still present, pytest cache, and two explicitly local-regenerable replay metrics files. This is 31.9% of the inventory. No identified persistent runtime or regression-baseline dependency was found for these selected outputs. Delete eligibility assumes their generating jobs are finished.
2. **B — archive-backed cold evidence:** 108.60 MiB (113,878,270 bytes) across 33 tracked files. Their existing historical review ZIP contains byte-identical copies, verified in memory. They are candidates to retire from the unpacked working tree after preserving the archive, source-path index and restore procedure. Seven adjacent files are NOT covered and are excluded.
3. **C — review before any cleanup:** a further 501.18 MiB of tracked temporary-looking files, 420.18 MiB of other local development scratch, old environments, duplicate ZIP exports, and additional historical state. These figures overlap some parent directory and category totals; they are not an additive savings claim.
4. **D — retain:** application sources/assets/configuration, current campaign state, active experiment modules, frozen ATGB materials, protected replay baselines, fixtures, specifically referenced historical captures, current PR-PLAY evidence and session/review handoffs.

If the A set were later removed, logical directory contents would fall to **3.75 GiB (4,031,134,775 bytes)**. This is a forecast only. The A set is ignored/local-only, so its removal would not shrink GitHub storage. No deletion, move, rename, compression, Git-history change, ignore-rule edit, installation, build, test run or provider call occurred during this audit.

## 2. Measurement method and boundaries

The inventory walked every regular file below the repository, including hidden directories, virtual environments, ignored scratch trees, nested checkout contents and the root .git directory. It found **225,086 regular files** in **55,401 directories including the root** (55,400 subdirectories), with zero traversal errors, zero skipped links and no observed multiply-linked regular files. Empty directory entry sizes are not counted.

Sizes are sums of logical file lengths, not NTFS allocated clusters or a volume-level allocation measurement. Small-file overhead, compression, sparse allocation and filesystem metadata can make actual space reclaimed differ. Measurements were taken over a traversal interval, not a locked filesystem snapshot. The new report itself is excluded from the inventory totals.

Read-only Git queries used --no-optional-locks for status, file classifications, object metadata and tree enumeration. The first ignored-file listing returned 141,913 paths; a nested ignored checkout was not fully enumerated by that Git listing. A filesystem walk plus git check-ignore on the extra 7,560 paths classified those as ignored as well, yielding the reconciled count below. No ordinary untracked source or evidence file was discovered.

Reference review covered **4,545 source, configuration, documentation, artifact-generator and review-manifest files**, including 1,387 files under the runtime/test/tool/script/experiment/CI roots. Searches distinguished readers, generators and documentary citations; constructed paths and nested ZIP members were checked where relevant. Negative text matches alone were not treated as proof of obsolescence. No tests or artifact-producing audit generators were run: those could modify evidence or temporary stores. External IDE configuration and running-process file handles were not exhaustively audited, so live stores must not be cleaned while their jobs are active.

### Git ownership of measured bytes

| Class | Files | Logical bytes | Size | Meaning |
| --- | --- | --- | --- | --- |
| Tracked worktree files | 75403 | 2,905,056,229 | 2.71 GiB | Current versioned payload; not compressed Git pack size |
| Ignored/local-only files | 149473 | 2,610,539,708 | 2.43 GiB | Includes nested ignored checkout contents and caches |
| Ordinary untracked files at entry | 0 | 0 | 0 B | None before this report |
| Root .git objects and metadata | 210 | 403,794,962 | 385.09 MiB | Local object database, index, refs and IDE metadata |
| TOTAL | 225086 | 5,919,390,899 | 5.51 GiB | No category overlap in this table |


The working directory excluding root .git is **5.14 GiB (5,515,595,937 bytes)**. Root .git is 6.8% of the total; deleting historical evidence is not a direct substitute for managing the much larger local temporary-store footprint.


## 3. Largest storage consumers

### Top-level directories (disjoint)

| Directory | Size | Bytes | Files |
| --- | --- | --- | --- |
| `artifacts/` | 2.87 GiB | 3,079,878,313 | 95,621 |
| `development/` | 1.77 GiB | 1,899,035,442 | 106,277 |
| `.git/` | 385.09 MiB | 403,794,962 | 210 |
| `handoff/` | 177.87 MiB | 186,508,635 | 479 |
| `tests/` | 103.54 MiB | 108,568,313 | 3,627 |
| `.venv/` | 53.68 MiB | 56,291,644 | 5,951 |
| `.venv-broken/` | 51.84 MiB | 54,357,446 | 5,207 |
| `venv/` | 47.20 MiB | 49,494,117 | 5,390 |
| `history/` | 28.03 MiB | 29,392,884 | 7 |
| `game/` | 20.84 MiB | 21,855,450 | 641 |
| `tools/` | 8.07 MiB | 8,464,679 | 456 |
| `docs/` | 7.47 MiB | 7,833,510 | 618 |
| `audits/` | 6.13 MiB | 6,426,772 | 63 |
| `experiments/` | 3.55 MiB | 3,721,561 | 287 |
| `.pytest_cache/` | 1.25 MiB | 1,307,087 | 5 |
| `data/` | 1.16 MiB | 1,218,696 | 150 |
| `scripts/` | 205.63 KiB | 210,562 | 18 |
| `static/` | 56.38 KiB | 57,735 | 3 |
| `__pycache__/` | 8.33 KiB | 8,527 | 5 |
| `.github/` | 7.91 KiB | 8,099 | 2 |
| `.idea/` | 4.24 KiB | 4,338 | 7 |
| `.cursor/` | 1.11 KiB | 1,140 | 1 |
| `.vscode/` | 327 B | 327 | 1 |
| Loose repository-root files | 928.38 KiB | 950,660 | 60 |


### Large nested consumers (overlap their parent rows)

| Directory | Size | Files |
| --- | --- | --- |
| `development/tmp/` | 1.77 GiB (1,895,322,394 bytes) | 105,900 |
| `artifacts/atgb/` | 749.97 MiB (786,400,864 bytes) | 14,421 |
| `artifacts/atgb/automated_playtests/` | 716.09 MiB (750,875,911 bytes) | 13,447 |
| `.git/objects/` | 297.56 MiB (312,013,829 bytes) | 164 |
| `.git/objects/pack/` | 296.74 MiB (311,150,216 bytes) | 105 |
| `development/tmp/github_checkpoint/` | 291.16 MiB (305,306,441 bytes) | 16,468 |
| `artifacts/pr_eg_r2c_r1/` | 264.81 MiB (277,674,472 bytes) | 13,368 |
| `artifacts/pr_eg_r2c_r2/` | 243.87 MiB (255,711,250 bytes) | 5,784 |
| `artifacts/pr_eg_r6_r5/` | 160.55 MiB (168,352,294 bytes) | 3,153 |
| `artifacts/pr_eg_r4_r1/` | 150.86 MiB (158,188,432 bytes) | 5,704 |
| `handoff/history/` | 146.36 MiB (153,468,157 bytes) | 301 |
| `artifacts/pr_eg_r6_r5/snapshots/` | 140.95 MiB (147,800,156 bytes) | 2,952 |
| `development/tmp/pr_play_05/` | 134.21 MiB (140,732,447 bytes) | 7,039 |
| `artifacts/pr_eg_r2c/` | 130.91 MiB (137,274,083 bytes) | 7,346 |
| `development/tmp/pr_play_07/` | 91.87 MiB (96,335,896 bytes) | 4,344 |
| `tests/__pycache__/` | 86.73 MiB (90,940,764 bytes) | 2,552 |
| `artifacts/pr_ef_r2/` | 80.18 MiB (84,075,059 bytes) | 294 |
| `.git/cursor/` | 75.68 MiB (79,357,970 bytes) | 3 |
| `.git/cursor/crepe/` | 75.68 MiB (79,357,970 bytes) | 3 |
| `artifacts/pr_eg_r4/` | 72.68 MiB (76,213,174 bytes) | 2,649 |
| `artifacts/pr_ef_r1/` | 65.32 MiB (68,493,682 bytes) | 80 |
| `artifacts/pr_eg_r6_r2_r2/` | 61.91 MiB (64,913,107 bytes) | 521 |
| `development/tmp/maintenance_ci_venv/` | 60.37 MiB (63,307,128 bytes) | 7,088 |
| `development/tmp/pr_play_06/` | 58.58 MiB (61,425,945 bytes) | 2,833 |
| `.venv/Lib/` | 51.81 MiB (54,321,728 bytes) | 5,931 |


These nested rows must not be added to the top-level table. For example, development/tmp is already inside development, and automated_playtests is already inside artifacts/atgb.

### Largest individual files

| File | Size | Git class |
| --- | --- | --- |
| `.git/objects/pack/pack-fd736d0b1a30867536dcbd075fcdc5a9825a779a.pack` | 240.72 MiB (252,413,241 bytes) | git_objects_and_metadata |
| `.git/cursor/crepe/bc7fa3b8568e42f853434d8b1a4067b19289760f/postings.bin` | 39.85 MiB (41,789,194 bytes) | git_objects_and_metadata |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_qualification.json` | 37.92 MiB (39,761,114 bytes) | tracked |
| `artifacts/pr_eg_r2c_r2/live_qualification.json` | 37.73 MiB (39,562,515 bytes) | tracked |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_qualification.json` | 35.99 MiB (37,733,582 bytes) | tracked |
| `.git/cursor/crepe/bc7fa3b8568e42f853434d8b1a4067b19289760f/index.bin` | 35.83 MiB (37,568,744 bytes) | git_objects_and_metadata |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_qualification.json` | 34.00 MiB (35,653,522 bytes) | tracked |
| `artifacts/atgb/automated_playtests/20261030T185006Z-921c62eb130e/reports/result.json` | 31.22 MiB (32,734,148 bytes) | tracked |
| `artifacts/atgb/automated_playtests/20261030T185021Z-d40083f66cbf/reports/result.json` | 31.22 MiB (32,733,934 bytes) | tracked |
| `artifacts/atgb/automated_playtests/20261030T185013Z-fc31c2f9bd5f/reports/result.json` | 27.76 MiB (29,108,199 bytes) | tracked |
| `.git/objects/pack/pack-1dff479d653b7638834eff5ace76362854428e95.pack` | 22.71 MiB (23,812,453 bytes) | git_objects_and_metadata |
| `artifacts/pr_eg_r6_r1/live_turns.jsonl` | 20.68 MiB (21,684,281 bytes) | tracked |
| `artifacts/pr_eg_r4_r1/live_before_final_fact_audit/live_turns.json` | 20.19 MiB (21,175,626 bytes) | tracked |
| `artifacts/pr_eg_r4_r1/live_turns.json` | 20.18 MiB (21,164,195 bytes) | tracked |
| `artifacts/atgb/automated_playtests/20261030T184726Z-404cbae39300/reports/result.json` | 19.80 MiB (20,758,451 bytes) | tracked |
| `handoff/history/pr_eg_r2c_r2_reference_eligibility_20261017/REVIEW.zip` | 19.30 MiB (20,238,655 bytes) | tracked |
| `development/tmp/github_checkpoint/baseline_4320bcd/artifacts/pr_eg_r4_r1/failed_first_live/live_turns.json` | 16.54 MiB (17,338,687 bytes) | ignored |
| `artifacts/pr_eg_r4_r1/failed_first_live/live_turns.json` | 16.54 MiB (17,338,687 bytes) | tracked |
| `artifacts/pr_eg_r4/turns.jsonl` | 16.39 MiB (17,190,545 bytes) | tracked |
| `.git/objects/pack/pack-07f33174f679da5c3e862ecb9c4fdff9a61e08a4.pack` | 15.64 MiB (16,402,152 bytes) | git_objects_and_metadata |
| `artifacts/pr_ef_r2/transcript_audit.json` | 14.10 MiB (14,785,789 bytes) | tracked |
| `history/development_logs/AI DM Development [I].pdf` | 13.67 MiB (14,337,761 bytes) | tracked |


The largest file is a local Git pack, not a tracked project payload. Similar names such as live_qualification.json do not establish identical contents or dispensability; before-fix runs can preserve materially different historical outcomes.


## 4. Storage by requested category

These are **overlapping location/extension inventories**, not a partition and not automatically cleanup candidates. A single captured JSONL under a temporary test store can appear as a log, evidence, temporary file and generated artifact.

| Category / definition | Files | Total size | Tracked bytes | Ignored bytes |
| --- | --- | --- | --- | --- |
| Logs / line-oriented records (.log and .jsonl) | 16,925 | 957.03 MiB (1,003,516,213 bytes) | 510,820,743 | 492,695,470 |
| Image-file proxy, not confirmed screenshots | 34 | 7.98 MiB (8,362,419 bytes) | 3,865,731 | 4,496,688 |
| ZIP archives | 601 | 262.34 MiB (275,084,819 bytes) | 257,626,592 | 17,458,227 |
| Test/evidence location proxy | 170,236 | 4.17 GiB (4,481,073,073 bytes) | 2,531,895,216 | 1,949,177,857 |
| Generated/evidence artifacts/ tree | 95,621 | 2.87 GiB (3,079,878,313 bytes) | 2,621,064,887 | 458,813,426 |
| Documentation/text proxy (.md/.rst or docs/) | 7,333 | 77.55 MiB (81,317,428 bytes) | 42,441,193 | 38,876,235 |
| Temporary-looking paths/files | 156,679 | 2.65 GiB (2,842,328,033 bytes) | 525,528,202 | 2,316,799,831 |
| Build-named subdirectories anywhere | 58 | 119.38 KiB (122,241 bytes) | 10,315 | 111,926 |
| Virtual environments, dependency and cache paths | 25,435 | 349.53 MiB (366,510,468 bytes) | 24,397,647 | 342,112,821 |


- Conventional .log files alone: 241 files / 225,731 bytes. JSONL files account for 16,684 files / 1,003,290,482 bytes. JSONL includes saved session transcripts, provider accounting and historical evidence, not just expendable console logging. A further 152 .txt filenames resembling output/log/regression captures total 645.11 KiB (660,597 bytes); that is a filename proxy, not a content-level classification. Other text may also contain logs.
- No regular files were found beneath literal screenshots/ directories. The 34 image files total 7.98 MiB and are mostly DOCX page renders and dependency images; this is not a confirmed UI-screenshot total. Screenshots embedded in ZIPs were not independently attributed, and remain counted in ZIP size.
- ZIPs: 601 files, 397 unique SHA-256 contents, 53 duplicate-content groups and 204 excess copies. Exact duplicate-copy bytes total 80.62 MiB (84,536,791 bytes). This upper bound overlaps A temporary stores and current handoffs. Outside A, the duplicate-copy upper bound is 70.78 MiB (74,214,968 bytes); it still includes protected/linked copies and is not an approved deletion total.
- No root build/, dist/, node_modules/ or .next/ tree exists. The 119.38 KiB build-name proxy is only 58 files in nested fixtures/dependencies; it is not a substantial build-output opportunity.
- Dependencies and caches include three root virtual environments plus bytecode elsewhere. User-level pip caches or interpreters outside this project are out of scope and were not measured.
- artifacts/ consumes 2.87 GiB, including **2.44 GiB (2,621,064,887 bytes) tracked**. Artifacts are 90.2% of all tracked working-file bytes. Much of this is generated, but a significant part is now an active test input or frozen evidence.

### File counts by extension (complete inventory)

All 58 observed extension classes are included. This includes ignored dependencies and .git internals. Counts below sum to 225,086.

| Extension | File count | Size | Tracked / ignored / root Git counts |
| --- | --- | --- | --- |
| `.json` | 147,891 | 2.83 GiB (3,040,848,127 bytes) | 58,695 / 89,195 / 1 |
| `.py` | 32,090 | 601.70 MiB (630,923,540 bytes) | 5,007 / 27,083 / 0 |
| `.jsonl` | 16,684 | 956.81 MiB (1,003,290,482 bytes) | 5,644 / 11,040 / 0 |
| `.pyc` | 16,665 | 254.77 MiB (267,147,782 bytes) | 0 / 16,665 / 0 |
| `.md` | 7,301 | 76.36 MiB (80,067,404 bytes) | 3,535 / 3,766 / 0 |
| `[no extension]` | 1,384 | 22.42 MiB (23,512,505 bytes) | 477 / 820 / 87 |
| `.txt` | 968 | 38.41 MiB (40,272,740 bytes) | 753 / 215 / 0 |
| `.zip` | 601 | 262.34 MiB (275,084,819 bytes) | 435 / 166 / 0 |
| `.xml` | 440 | 43.66 MiB (45,785,931 bytes) | 365 / 75 / 0 |
| `.log` | 241 | 220.44 KiB (225,731 bytes) | 239 / 2 / 0 |
| `.typed` | 226 | 2.19 KiB (2,243 bytes) | 47 / 179 / 0 |
| `.exe` | 117 | 13.99 MiB (14,669,413 bytes) | 23 / 94 / 0 |
| `.csv` | 79 | 2.49 MiB (2,605,983 bytes) | 55 / 24 / 0 |
| `.diff` | 40 | 2.09 MiB (2,194,490 bytes) | 40 / 0 / 0 |
| `.rev` | 35 | 189.92 KiB (194,480 bytes) | 0 / 0 / 35 |
| `.pack` | 35 | 295.23 MiB (309,569,596 bytes) | 0 / 0 / 35 |
| `.idx` | 35 | 1.32 MiB (1,386,140 bytes) | 0 / 0 / 35 |
| `.png` | 32 | 7.37 MiB (7,731,462 bytes) | 16 / 16 / 0 |
| `.pyi` | 16 | 288.91 KiB (295,843 bytes) | 3 / 13 / 0 |
| `.patch` | 15 | 1.26 MiB (1,316,323 bytes) | 15 / 0 / 0 |
| `.sample` | 14 | 25.22 KiB (25,827 bytes) | 0 / 0 / 14 |
| `.bsd` | 13 | 17.13 KiB (17,541 bytes) | 3 / 10 / 0 |
| `.apache` | 13 | 129.68 KiB (132,793 bytes) | 3 / 10 / 0 |
| `.pyd` | 12 | 25.73 MiB (26,975,232 bytes) | 0 / 12 / 0 |
| `.pem` | 11 | 2.76 MiB (2,890,432 bytes) | 3 / 8 / 0 |
| `.pdf` | 10 | 56.07 MiB (58,796,918 bytes) | 5 / 5 / 0 |
| `.bat` | 9 | 5.91 KiB (6,050 bytes) | 2 / 7 / 0 |
| `.ps1` | 9 | 87.95 KiB (90,056 bytes) | 6 / 3 / 0 |
| `.bak` | 9 | 1.78 MiB (1,868,391 bytes) | 3 / 6 / 0 |
| `.js` | 9 | 225.84 KiB (231,260 bytes) | 5 / 4 / 0 |
| `.html` | 7 | 630.03 KiB (645,151 bytes) | 3 / 4 / 0 |
| `.docx` | 7 | 279.33 KiB (286,035 bytes) | 4 / 3 / 0 |
| `.cfg` | 5 | 2.15 KiB (2,205 bytes) | 1 / 4 / 0 |
| `.mit` | 5 | 5.13 KiB (5,250 bytes) | 1 / 4 / 0 |
| `.apache2` | 5 | 55.66 KiB (56,992 bytes) | 1 / 4 / 0 |
| `.1` | 4 | 29.81 KiB (30,524 bytes) | 1 / 3 / 0 |
| `.sh` | 4 | 3.71 KiB (3,803 bytes) | 1 / 3 / 0 |
| `.rst` | 4 | 36.37 KiB (37,238 bytes) | 1 / 3 / 0 |
| `.cjs` | 4 | 13.37 KiB (13,688 bytes) | 2 / 2 / 0 |
| `.css` | 4 | 17.71 KiB (18,136 bytes) | 2 / 2 / 0 |
| `.yml` | 4 | 15.67 KiB (16,048 bytes) | 2 / 2 / 0 |
| `.ini` | 3 | 5.48 KiB (5,607 bytes) | 1 / 2 / 0 |
| `.tag` | 3 | 573 B (573 bytes) | 0 / 3 / 0 |
| `.pth` | 2 | 169 B (169 bytes) | 0 / 2 / 0 |
| `.virtualenv` | 2 | 0 B (0 bytes) | 0 / 2 / 0 |
| `.tmpl` | 2 | 356 B (356 bytes) | 0 / 2 / 0 |
| `.example` | 2 | 1.01 KiB (1,038 bytes) | 1 / 1 / 0 |
| `.mdc` | 2 | 2.23 KiB (2,280 bytes) | 1 / 1 / 0 |
| `.before` | 2 | 48.56 KiB (49,723 bytes) | 2 / 0 / 0 |
| `.gif` | 2 | 616.17 KiB (630,957 bytes) | 0 / 2 / 0 |
| `.bin` | 2 | 75.68 MiB (79,357,938 bytes) | 0 / 0 / 2 |
| `.nu` | 1 | 2.75 KiB (2,817 bytes) | 0 / 1 / 0 |
| `.fish` | 1 | 3.06 KiB (3,132 bytes) | 0 / 1 / 0 |
| `.13488` | 1 | 8.58 KiB (8,783 bytes) | 0 / 1 / 0 |
| `.5104` | 1 | 37.64 KiB (38,543 bytes) | 0 / 1 / 0 |
| `.12828` | 1 | 13.60 KiB (13,922 bytes) | 0 / 1 / 0 |
| `.iml` | 1 | 416 B (416 bytes) | 0 / 1 / 0 |
| `.0` | 1 | 41 B (41 bytes) | 0 / 0 / 1 |



## 5. Development dependency review — retain the actual inputs

| Area | Required material / observed dependency | Cleanup consequence |
| --- | --- | --- |
| Application runtime and UI | run.py:5,44 starts Uvicorn; game/ owns application logic; static/ contains served UI assets. | Removing source/assets breaks startup or the player interface. Source-backed bytecode is a separate A exception, not permission to remove these directories. |
| Campaign initialization | game/campaign_reset.py:38 onward orchestrates reset; game/storage.py:53–69 resolves data and document paths; tests/helpers/turn_pipeline_http_fixtures.py:36–52 seeds isolated campaign files. | Canonical campaign/world/character/conditions and authored scenes must remain. Existing temporary test copies are not canonical seeds. |
| AI-DM / provider integration | game/gm.py and provider/interpretation/planning modules; game/live_chat_interpretation.py:149–152 imports experiments.pr_do, pr_dp and pr_dr; :424 also imports the pr_dp prompt utility. | experiments/ is NOT uniformly disposable experimental output. Deleting it broadly can break production imports. No model or provider operation was invoked. |
| State persistence | game/storage.py, docs/runtime_persistence_envelope.md:34–43, current data/session.json, combat.json, world.json, character.json, session_log.jsonl and any save slots. | A small JSON or JSONL file can be the user's current campaign. Keep all canonical state; an old timestamp or log extension is not a deletion criterion. |
| Frozen ATGB initialization | tools/atgb/baseline.py:8,22–26 pins frontier-gate-v1, its manifest hash and bootstrap files under data/validation/atgb/. | Missing/edited files invalidate deterministic baseline loading; this 83.69 KiB dataset is not a storage problem. |
| ATGB evaluation and human review | tests/test_atgb_human_review.py:11–28 reads artifacts/atgb/atgb_04/review_index.json, blank_judgments.json and each source_result. Revision/correction/grounding suites read atgb_03c, atgb_r1_03/r1_05, atgb_r2_01 and atgb_r2_03 captures. | Preserve frozen judgments AND their source result/log/context files. A summary or ZIP alone does not replace path-bound fixtures without an explicit migration. |
| Historical opening regressions | tests/test_pr_play_11_claim_authority.py:13–30,51 reads automated_playtests/20261031T015747Z-5a6c03c902e3, 20261030T191257Z-ecc1b6062bdc and 20261030T183848Z-5fe421902485 baseline/documents.json and opening_response_evidence. PR-PLAY-10 overlay tests also use historical captures. | These historical run directories are D at the referenced paths, not bulk archive/delete candidates. PR-PLAY-12 additionally uses 20261031T170523Z-92cd9d058c92 and its copied evidence. |
| Other authority/envelope regression fixtures | tests/test_pr_br_continuation18_immutable_boundary.py:45–46 reads C16 and independent-smoke turns.json. tests/test_pr_bw_narration_only_envelope.py:23 and test_pr_by_narration_only_retry_contract.py:26 read pr_bv_turn_operation_projection_micro_live/evidence. tests/test_pr_bu_narration_claim_composition.py:26 reads pr_bt_selective_epistemic_restoration_final_micro_live/evidence, plus PR-BU_validator_semantic_matrix.json. | Old campaign evidence is a live test dependency. Preserve these files and their needed context; do not infer that a completed campaign means unused inputs. |
| Counterfactual replay snapshots | experiments/pr_eg_r6_r5/run.py:389–394 constructs OUT/snapshots paths and calls _restore(after, data_dir). The corresponding report describes replaying cached proposals against pre-turn state. | 140.95 MiB under artifacts/pr_eg_r6_r5/snapshots is genuine replay input, not a disposable directory merely because it is called snapshots. |
| Protected replay / governance | tests/helpers/golden_replay_artifact_manifest.py:35–95 distinguishes canonical, frozen, local-regenerable and paired outputs; data/validation, protected manifests and trend windows are governed inputs. | Only the explicitly local-regenerable metrics subset is A. Keep protected manifests, frozen history and acceptance-critical artifacts. |
| Current development / continuity | docs/NEXT_SESSION.md names PR-PLAY-12 plus earlier authority work; retain docs/DEVELOPMENT_CONSTITUTION.md, state/validation contracts, current PR-PLAY reports/evidence and handoff/CURRENT_REVIEW.*. | The next development pass needs these findings and raw provenance. Do not archive current review material solely because the investigation has ended. |
| Builds and CI | .github/workflows/content-lint.yml, convergence-checks.yml, requirements.txt, Makefile, pytest.ini, tools/test_audit.py and split-owner/protected-manifest checkers. CI installs Python 3.12 dependencies and creates development/tmp before pytest. | Keep workflows, source registries, schemas and fixture inputs. Generated CI reports may be reproducible, but generator ownership and read dependencies still determine retention. |
| Local Python tooling | scripts/run_live_playtest.ps1:17 selects .venv/Scripts/python.exe; docs/README.md:21–34 documents that environment. .idea/misc.xml still selects a Python 3.9 SDK. | Keep the documented .venv. The legacy venv and .venv-broken require review rather than automatic deletion. |

No ASHEN_DATA_DIR override was found in the repository .env or the inspected command environment; default storage is data/. This does not prove that no independently running process has its own override.

**PR-2 terminology:** no uniquely named PR-2 or PR2 development owner was found in the reviewed source/documentation. It may be shorthand for Chapter II, PR-PLAY-02 or an R2 investigation; this audit does not invent that mapping. The conservative retention set includes current PR-PLAY-12, PR-PLAY-02 provider-budget controls, R2/frozen ATGB material and the source/fixtures required by their consumers. Clarifying the label would be necessary before removing any possibly related evidence.


## 6. Cleanup classification

Classification is based on reproducibility, dependency evidence, explicit retention contracts and exact hashes—not age. These are proposals only. None has been executed.

### A — SAFE TO DELETE: selected reproducible/local output

The following sets are disjoint. All are ignored, with zero tracked files in this A set. Eligibility assumes no associated server, benchmark or test job is still using a store. Preserve wanted failure diagnostics first; this report does not authorize stopping processes or removing live stores.

| Priority / exact scope | Files | Recoverable logical space | Confidence / evidence | Consequence |
| --- | --- | --- | --- | --- |
| A1: pytest case-store files under development/tmp, excluding github_checkpoint and maintenance_ci_venv | 79,025 | 1.35 GiB (1,454,736,068 bytes) | High for selected generated stores: pytest.ini:4–6/14 and tests/helpers/turn_pipeline_http_fixtures.py:36–52 seed fresh stores; validation tools direct --basetemp here. No persistent read of these selected prior case paths identified. | Loses temporary test copies/transcripts; tests recreate fresh stores. Does not touch canonical data or retained artifacts evidence. |
| A2: 44 ignored artifact pytest run roots listed in Appendix A | 13,216 | 291.27 MiB (305,416,574 bytes) | High: explicit disposable-output .gitignore patterns; no inbound literal path OR directory-name reference found in the reviewed readers/docs/manifests. Referenced scratch roots are excluded into C. | Loses disposable case stores and local rerun diagnostics; test sources/fixtures remain. |
| A3: individual bytecode files with their corresponding .py source present; outside root environments and development/tmp | 3,900 | 120.86 MiB (126,727,351 bytes) | High: 3,900 cache files matched an existing source module. Tools already exclude __pycache__ from source/evidence hashes. Orphan cache exceptions are C. | Cold imports/recompilation and lost acceleration only; no source deletion. Never delete a whole cache directory without checking orphan exceptions. |
| A4: local .pytest_cache files outside the other A scopes | 5 | 1.25 MiB (1,307,087 bytes) | High: ignored pytest cache; not a frozen regression result. | Loses lastfailed/nodeid convenience; testing remains possible. |
| A5: artifacts/golden_replay/replay_maintenance_metrics.json and .md | 2 | 67.43 KiB (69,044 bytes) | High: LOCAL_REGENERABLE_ARTIFACT_PATHS / local_only retention contract and explicit ignore entries. | Recompute the advisory metrics when needed; protected evidence files remain. |
| TOTAL A | 96,148 | 1.76 GiB (1,888,256,124 bytes) | No overlap between A1–A5 | Local-only reduction; zero GitHub-history reduction |


A1 is a file-set selector, NOT permission to wipe development/tmp wholesale: a path must be under development/tmp, outside the two named exclusions, and beneath a pytest leaf component named test_*. The remaining 420.18 MiB (440,586,326 bytes) is C. Appendix A lists the largest selected campaigns for review.

A3 maps __pycache__/<module>.cpython-<version>[pytest/optimization suffix].pyc to the corresponding .py in its parent source directory. It includes multiple Python/pytest cache variants of the same module. The audit did not mark the 66 source-missing cache files as safe. Recompute source presence before any later cleanup; this is not a blanket '*.pyc' recommendation.

Largest A3 contributions: `tests/__pycache__` 84.88 MiB; `game/__pycache__` 14.29 MiB; `artifacts/pr_eg_r2c_r1/baseline_overlay/game/__pycache__` 6.06 MiB; `tests/helpers/__pycache__` 5.19 MiB.

### B — SAFE TO ARCHIVE: verified cold historical copies

**33 tracked files totaling 108.60 MiB (113,878,270 bytes)** in these completed PR-EG-R2C-R2 before-fix bundles have byte-identical archive members. No direct current runtime/test/tool consumer of these particular bundle names was found. Historical review manifests do cite them, so retain their identity and restore capability rather than discard the evidence.

| Historical bundle | Verified archive-backed files | Eligible unpacked bytes | Uncovered neighboring files / bytes |
| --- | --- | --- | --- |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/` | 15 | 38.29 MiB (40,152,553 bytes) | 3 / 6.88 KiB (7,050 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/` | 8 | 36.13 MiB (37,885,138 bytes) | 2 / 465.40 KiB (476,573 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/` | 10 | 34.18 MiB (35,840,579 bytes) | 2 / 39.56 KiB (40,513 bytes) |


Existing retained archive: `handoff/history/pr_eg_r2c_r2_reference_eligibility_20261017/REVIEW.zip`. SHA-256: `98bc8629363fcd955fb0498f4db2601f51b44df4448d5317ea927ec155963f16`. Its associated REVIEW_MANIFEST.json records the historical campaign. The audit opened the ZIP read-only, read members into memory, and compared SHA-256 with all 40 files in the three source directories: 33 matched; seven are missing from that archive. No files were extracted, compressed or modified.

Appendix B enumerates the exact 33 B files and hashes. Only that list is eligible for archive-based retirement of unpacked copies. Keep the ZIP and manifest plus a restore mapping from member support/<repository-relative-path> back to the original path. Historical links or regenerating an old review package may require restoring those paths first. The remaining seven files are explicitly C; **do not remove the entire parent directories**. The archive's presence alone did not prove complete coverage.

Potential local working-tree savings are 108.60 MiB while retaining the already-existing ZIP. If a later reviewed commit removes these unpacked tracked copies, future HEAD checkouts get smaller. Their content remains in Git history; server object storage is not reduced merely by that commit. Historical live responses are not reproducible by asking the provider again.

### C — REQUIRES REVIEW

Parent and child rows in this table overlap. Figures are ceilings for inspection, not an additive reclaim forecast.

| Candidate | Size / ownership | Why review is required | Possible consequence |
| --- | --- | --- | --- |
| Other development/tmp files not selected by A1 | 420.18 MiB (440,586,326 bytes); ignored | Includes the historical checkpoint and maintenance environment below, plus unclassified scratch. A temp path is insufficient evidence. | May contain the only local baseline, environment, or old diagnostic source needed for continuity. |
| development/tmp/github_checkpoint/ | 291.16 MiB (305,306,441 bytes); ignored | docs/maintenance/protected_replay_ci_20261018.md:109–111 explicitly retains command output, JUnit and baseline comparisons there. Includes an ignored nested checkout; no archival coverage was proved. | Loses maintenance provenance and local historical checkout. Not part of A. |
| development/tmp/maintenance_ci_venv/ | 60.37 MiB (63,307,128 bytes); ignored | No specific active reference found, but installed versions and historical CI reproduction were not proved equivalent elsewhere. | Could lose a distinct diagnostic environment; requirements are not an exact lockfile. |
| Tracked temporary-looking files across artifacts/ | 501.18 MiB (525,528,202 bytes); 31,972 tracked files | Names such as baseline_tmp/final_tmp/qualification_final_tmp escaped current ignore patterns; some folders can be causal evidence or snapshots. No blanket active-dependency clearance. | Would shrink a future HEAD if removed, but may destroy baseline/replay inputs; Git history would still retain bytes. |
| Ten referenced ignored artifact pytest run roots | 62.63 MiB (65,668,318 bytes); ignored | Documentary citations were found, even where they appear to describe past --basetemp outputs. Keep separate from the unreferenced A2 roots until outputs/results ownership is confirmed. | Might remove the only retained local evidence behind an old result. |
| .venv-broken/ | 51.84 MiB (54,357,446 bytes) total; 23.27 MiB (24,397,647 bytes) tracked in 2,663 files | Despite the ignore rule, previously tracked environment files remain versioned. pyvenv.cfg points to Python 3.12; historical documentation says prior work was preserved. No inventory of unique installed versions or external interpreter references was proved. | Removing it might lose a unique environment; future untracking is a separate authorized Git change. |
| venv/ | 47.20 MiB (49,494,117 bytes); ignored | Python 3.9 environment. .idea/misc.xml still names a Python 3.9 project SDK, so assuming this is unused would be unsafe. | Could break an IDE launch configuration or preserve different dependency versions. |
| Seven uncovered files beside the B set | 511.85 KiB (524,136 bytes); tracked | The verified ZIP does not contain these source/usage/status/probe members. Exact paths are below. | Deleting the parent bundle would lose evidence not represented in the checked archive. |
| Duplicate ZIP copies | 80.62 MiB (84,536,791 bytes) overall theoretical excess; 70.78 MiB (74,214,968 bytes) outside A | Exact content equality is proved, but canonical handoff/history paths, published citations and active review copies can require separate path identities. Overlaps A/B/D. | Consolidation can break links or package provenance; Git already deduplicates identical blob content. |
| history/development_logs/ | 28.03 MiB (29,392,884 bytes); tracked | PR-AA_product_realization_portfolio_bootstrap.md:600 explicitly preserves this historical material. Informational value and backup completeness need owner review. | Continuity loss even if no runtime import exists. |
| Orphan / source-missing bytecode cache files | 2.54 MiB (2,664,536 bytes); 66 ignored files | Current matching .py source was not found; do not assume every cache has a regenerable source. Examples include obsolete debugging/probe modules. | Could lose the only remaining local version of an old module. See Appendix C. |
| Root .git/cursor/ cache | 75.68 MiB (79,357,970 bytes); local Git-directory IDE metadata | Contains Cursor crepe index/postings, not normal pushed Git objects. App ownership, rebuild behavior and current locks were not validated. | Potential local-only saving; do not manually remove inside .git during this audit. |
| Root .git/objects/92/tmp_obj_xKdgkS | 55.17 KiB (56,498 bytes); Git reports one garbage entry (55 KiB rounded) | Read-only git count-objects reports it, but this is not proof that a manual delete is safe or that another process is not using it. | Possible object-store corruption if .git entries are removed casually. No cleanup proposed for execution. |


Largest tracked temporary-looking subsets (not cleared for removal):

| Tracked subset | Bytes / size | Files |
| --- | --- | --- |
| `artifacts/pr_eg_r4_r1/tmp_baseline` | 35.97 MiB (37,718,667 bytes) | 2363 |
| `artifacts/pr_eg_r4_r1/tmp_repaired` | 35.64 MiB (37,366,234 bytes) | 2363 |
| `artifacts/pr_eg_r2c_r2/final_tmp` | 34.88 MiB (36,571,752 bytes) | 2327 |
| `artifacts/pr_eg_r2c_r1/complete_final_tmp` | 31.42 MiB (32,946,215 bytes) | 1967 |
| `artifacts/pr_eg_r2c_r2/baseline_tmp` | 31.42 MiB (32,946,012 bytes) | 1985 |
| `artifacts/pr_eg_r2c_r1/qualification_final_tmp` | 31.42 MiB (32,945,706 bytes) | 1985 |
| `artifacts/pr_eg_r2c/baseline_local_tmp` | 28.99 MiB (30,400,549 bytes) | 1778 |
| `artifacts/pr_eg_r2c_r1/final_verified_tmp` | 27.91 MiB (29,269,081 bytes) | 1805 |
| `artifacts/pr_eg_r2c_r1/final_tmp` | 27.91 MiB (29,268,025 bytes) | 1805 |
| `artifacts/pr_eg_r2c_r1/post_tmp` | 27.86 MiB (29,217,453 bytes) | 1787 |


The seven uncovered neighboring files are:

| Excluded path — NOT in B | Size |
| --- | --- |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/conversational_continuity.py` | 33.17 KiB (33,961 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final_live_usage.jsonl` | 6.40 KiB (6,552 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/qualification_live_usage.jsonl` | 6.39 KiB (6,548 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_status.json` | 151 B (151 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/acceptance_gates.json` | 351 B (351 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_usage.jsonl` | 6.40 KiB (6,552 bytes) |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/clarification_probe.json` | 459.00 KiB (470,021 bytes) |


### D — MUST RETAIN

- Source/config/assets under game/, static/, scripts/, tools/, .github/, run.py, requirements.txt, Makefile and pytest.ini; associated source registries and validation contracts. Reproducible A caches are the narrowly defined exception.
- Canonical data/ (1.16 MiB), current campaign documents and `data/session_log.jsonl` (204.61 KiB), plus save slots if present. Do not treat a player transcript as ordinary disposable logging.
- Frozen data/validation/atgb/ (83.69 KiB), tests/fixtures/ (126.55 KiB), ATGB human judgments and the original result/context files they reference; retain baseline/hash manifests.
- Path-bound historical regression inputs listed in section 5, including the three accepted/rejected opening runs and the latest PR-PLAY-12 capture. Other automated_playtests runs remain C until individually classified; no wholesale deletion of that 716.09 MiB tree is authorized by the audit.
- `artifacts/pr_eg_r6_r5/snapshots/` (140.95 MiB), because the diagnostic restores it. This is an explicit counterexample to treating every snapshot as scratch.
- Active experiment source modules, including runtime-imported pr_do/pr_dp/pr_dr and the corpus/gold/score modules used by tests. The directory name experiments does not determine retention.
- Protected golden replay canonical/frozen evidence and trend-window manifests; preserve the retention registry itself. Only the two named local metrics files are A.
- Current PR-PLAY-10/11/12 reports, source/authority evidence and captured responses; docs/NEXT_SESSION.md and standing architecture/state/validation authorities. User-generated human-play evidence under artifacts/human_playtests (8.72 MiB) retains informational and regression value.
- handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip, plus the current timestamped PR-PLAY-12 package and current history copy while external review remains pending. Their duplicate bytes are not immediate cleanup permission.
- The documented active .venv (53.68 MiB), .env and configuration required by the active launch path. No secret values are reproduced in this report.
- Git commits, refs, object packs, index, reflogs/configuration and repository integrity. A .git directory is not a disposable build cache. Cursor metadata is separately C rather than assumed safe.


## 7. Git storage, tracking and GitHub consequences

Root .git occupies **385.09 MiB (403,794,962 bytes)**. The measured major components are:

| Local .git component | Measured bytes / size | Interpretation |
| --- | --- | --- |
| objects/ | 297.56 MiB (312,013,829 bytes) | Actual object database, including pack files and loose entries |
| objects/pack/ | 296.74 MiB (311,150,216 bytes) | Already included in objects/; do not add both rows |
| cursor/ | 75.68 MiB (79,357,970 bytes) | Local Cursor search/index metadata; not pushed as project content |
| index | 11.82 MiB (12,391,126 bytes) | Current local Git index; not a disposable application cache |


Read-only object accounting reports 56 loose objects, 48,165 packed objects in 35 packs, and size-pack 303,667 KiB (Git-reported units). Pack/index/reverse-index file totals and the filesystem object-directory total are the authoritative local bytes; these are not equivalent to uncompressed source payload sizes.

Reachability enumeration found 48,060 objects reachable through local refs. Their 32,986 unique blob objects contain 2.48 GiB (2,659,309,178 bytes) of uncompressed content. 3,891 of those blobs, totaling 271.64 MiB (284,837,962 bytes) uncompressed, are not file blobs in the current HEAD tree. That historical-only raw amount is NOT an estimate of space safely reclaimable from packs. Compression, delta bases, duplicate paths, retained refs/tags and reflogs make that inference invalid. Counts of packed/loose objects minus reachable objects are not a safe deletion list.

### Does each action reduce GitHub storage?

| Potential later action | Local working directory | Future HEAD checkout | Existing GitHub history/object storage |
| --- | --- | --- | --- |
| Remove the selected ignored A set | About 1.76 GiB of logical file contents | No change: these files are not tracked | No change |
| Retire the 33 archive-backed tracked B copies in a reviewed commit | About 108.60 MiB of unpacked files, while retaining ZIP/manifest | Smaller checked-out payload | Old blobs remain reachable through earlier commits; no guaranteed reduction |
| Review/remove tracked scratch or tracked environment files in a later commit | Potentially smaller after dependency clearance | Smaller for future checkouts | Historical content remains |
| Consolidate identical ZIP paths | Saves redundant working-file copies if path consumers allow it | Can reduce checkout duplication | Identical bytes already reuse the same Git blob; path deletion alone usually saves little object content |
| Relocate an artifact while leaving a copy in the project | No net saving, possibly increased use | Depends on what is committed | No history reduction |
| Deal with .git/cursor through its owning app after review | Potential local-only effect | No change | No change |
| Rewrite repository history | Not assessed or authorized | Can change available history and clone payloads | Could remove some old content only after a separately planned coordinated operation; actual server retention must be verified |


**History rewriting is not the recommended first step.** It changes commit identities and can disrupt other clones, branches/tags, review links, provenance and frozen source attestations; coordinated remote replacement and recovery backups would be necessary. Server-side cached/ref/object retention can still delay or prevent expected savings. No history rewrite, forced push, object pruning, garbage collection, checkout reset or cleanup command was performed. This audit did not query GitHub's server storage/billing or fetch additional refs, so it does not claim an exact remote size.

### Generated files already tracked, and ignore-rule gaps

- Generated/evidence artifacts/ files occupy 2.44 GiB (2,621,064,887 bytes) of the tracked checkout. Some should remain tracked as fixtures or authoritative evidence, while 501.18 MiB (525,528,202 bytes) of temporary-looking tracked paths warrant owner review.
- .venv-broken is explicitly ignored, yet **2,663 files / 23.27 MiB (24,397,647 bytes)** there remain tracked. Ignore rules do not retroactively remove files already in the index/history. Any approved future untracking or removal is a separate Git change; this audit did neither.
- Existing rules already cover development/tmp, Python/pytest caches and several artifact pytest naming patterns. The accumulation in A is therefore mostly a retention/lifecycle problem, not absence of ignore rules.
- Names such as final_tmp/, baseline_tmp/, baseline_local_tmp/, qualification_final_tmp/, tmp_baseline/ and tmp_repaired/ are not uniformly covered by the existing artifact ignore rules. These account for substantial tracked scratch. After reference review, standardize disposable output under the existing development/tmp ownership or add narrowly scoped, owner-approved patterns for proven disposable leaves. Do not broadly ignore artifacts/, *.json, *.jsonl, all snapshots, or every ZIP: that would hide active fixtures, state and review evidence.
- Keep source/fixture/evidence allowlists explicit when staging large generated updates. Ignore-rule changes would prevent future untracked accumulation; they would not by themselves remove the current ignored files, reduce old Git objects or repair already tracked disposable content.

## 8. Recommended cleanup sequence — planning only

1. **Protect the current state and dependency map.** Retain current campaign data, frozen ATGB manifests/judgments, the path-bound capture/fixture sets in section 5 and the current handoff. Confirm no test/benchmark/server holds an intended cleanup store. Preserve any unresolved failure investigation before eviction. Do not run a baseline reset as cleanup.
2. **Start with A1/A2 for the largest local benefit.** The exact eligible test-store scopes provide 1.64 GiB without changing tracked files or GitHub history. Do not widen this to all development/tmp or artifacts. Referenced and unclassified stores stay C.
3. **Handle A3–A5 separately.** Source-backed bytecode, pytest convenience cache and explicitly local replay metrics add 122.17 MiB. Keep orphan bytecode exceptions, current environments and protected replay inputs.
4. **Review the B archive-backed copies.** Preserve the verified ZIP, SHA-256, manifest and canonical path-to-member mapping. Confirm any historical report-regeneration workflow will restore paths first. Only the 33 listed matched files are covered; retain all seven uncovered neighbors. Any tracked-file deletion/commit requires a later authorized cleanup pass.
5. **Inspect C by owner, starting with tracked scratch and other development/tmp.** Reconcile the checkpoint's documented evidence, legacy environment/IDE use and replay snapshot restoration. Obtain an exact dependency-cleared file list. Do not infer irrelevance from directory age or names.
6. **Apply a future retention/ignore policy before generating more outputs.** This is how to prevent the same local growth and accidental addition of disposable state. Keep history/fixture exceptions explicit and reversible.
7. **Only then reconsider Git object size if still necessary.** Local ignored output offers much more immediate benefit. A later history/storage project would need separate authority, multi-clone coordination and actual remote size measurements; no such operation is proposed for execution here.
8. **Validate an eventual approved cleanup.** Compare the intended changed-path list with source/fixture references, verify startup/campaign seed and save/restore behavior, run the established protected replay/ATGB infrastructure and relevant PR-PLAY regression selections, and inspect remaining artifacts. This audit deliberately did not run tests, because many write evidence into fixed sinks.

## 9. Suggested future artifact-retention policy

| Material | Suggested future policy | Required exception/control |
| --- | --- | --- |
| Pytest case stores, source-backed bytecode and convenience caches | Keep current job plus a small recent run window; a seven-day or workspace-size threshold can trigger review after jobs finish. Recreate from source/fixtures. | Age is a trigger for classification, never sole proof of safety. Preserve unresolved failures, source-missing caches and externally referenced evidence. |
| Successful synthetic diagnostics | Keep a final summary, exact command, source revision/hash, fixture version, result identities and one representative complete run per scenario/policy version. | A consumed capture becomes a pinned fixture; it cannot expire as routine output. |
| Failed or architecturally important runs | Retain the original response, relevant context/baseline, native reasons, state before/after, usage record and source lineage. | Close the investigation or establish a verified complete archive before reducing working copies. No provider re-call can recreate historical evidence exactly. |
| Live captures / human-play / ATGB judgments | Immutable, versioned originals with their source contexts and clear canonical manifest. Keep current frozen benchmarks online at the paths tests require. | Never substitute generated judgments, rewrite attestations, or discard unique wire/parsed captures as logs. |
| Repeated API/state payloads | Store each large raw item once and reference it by path/hash in summaries, after reviewing consumer contracts. | Existing results often duplicate response/context state. Format changes need tests and migration, not silent payload trimming. |
| Handoff ZIPs | Retain one immutable complete package per completed campaign and the current stable review surface; catalog aliases/citations explicitly. Verify full contents before retiring unpacked copies. | The audit found seven files absent from an apparently relevant ZIP. A ZIP name or manifest alone is not coverage verification. |
| Baseline/source snapshots and experiments | Retain until no active test, counterfactual replay, source attestation or current development contract consumes them; otherwise archive complete and restorable bundles. | A snapshot or experiments directory can contain runtime/test inputs. |
| Dependency environments | Keep the documented active environment; retire others only after interpreter/IDE use, installed-version inventory and recreation are established. | requirements.txt uses minimum-version ranges, not an exact environment lock. |
| Generated artifact tracking | Use explicit owner-reviewed manifests and stable retained fixture locations; keep disposable stores under the existing temporary root. | No broad artifacts or data-type ignore rule. Untracking later does not erase history. |

A soft local scratch budget (for example 1 GiB with a review notification) could make accumulation visible; it must not automatically evict protected evidence, active jobs or current failures. No such budget or automatic cleanup was configured.


## Appendix A — exact A2 roots and representative A1 contributions

The following **44 entire ignored roots** are the A2 scope. No inbound literal full-path or basename reference was found in the reviewed source/config/documentation/manifests. The ten cited scratch roots are excluded into C. Recheck for new consumers before any future removal.

| A2 root | Files | Eligible bytes / size |
| --- | --- | --- |
| `artifacts/praq_pytest_verify2/` | 1,215 | 27.70 MiB (29,050,155 bytes) |
| `artifacts/prap_pytest_tmp2/` | 962 | 23.11 MiB (24,228,144 bytes) |
| `artifacts/prao_pytest_reg5/` | 1,017 | 22.92 MiB (24,030,224 bytes) |
| `artifacts/prao_pytest_reg1/` | 679 | 15.96 MiB (16,733,810 bytes) |
| `artifacts/prak_pytest_tmp4/` | 640 | 13.98 MiB (14,655,053 bytes) |
| `artifacts/prao_pytest_reg3/` | 603 | 13.50 MiB (14,154,495 bytes) |
| `artifacts/pran_pytest_tmp2/` | 574 | 13.15 MiB (13,787,733 bytes) |
| `artifacts/praq_pytest_reg1/` | 548 | 12.20 MiB (12,792,710 bytes) |
| `artifacts/pran_pytest_tmp8/` | 511 | 11.53 MiB (12,085,311 bytes) |
| `artifacts/pral_pytest_tmp3/` | 474 | 11.18 MiB (11,722,250 bytes) |
| `artifacts/pran_pytest_tmp4/` | 475 | 10.57 MiB (11,087,308 bytes) |
| `artifacts/prak_pytest_tmp7/` | 480 | 10.41 MiB (10,916,057 bytes) |
| `artifacts/praj_pytest_tmp3/` | 388 | 9.40 MiB (9,853,067 bytes) |
| `artifacts/pram_pytest_tmp2/` | 582 | 8.69 MiB (9,116,578 bytes) |
| `artifacts/prao_pytest_reg2/` | 336 | 7.36 MiB (7,716,750 bytes) |
| `artifacts/prao_pytest_reg4/` | 362 | 7.32 MiB (7,680,760 bytes) |
| `artifacts/prak_pytest_tmp6/` | 345 | 6.56 MiB (6,879,685 bytes) |
| `artifacts/prai_pytest_tmp3/` | 284 | 6.31 MiB (6,612,048 bytes) |
| `artifacts/pran_pytest_tmp3/` | 209 | 5.61 MiB (5,882,468 bytes) |
| `artifacts/pram_pytest_tmp4/` | 216 | 4.72 MiB (4,951,946 bytes) |
| `artifacts/prar_pytest_verify/` | 218 | 4.61 MiB (4,832,020 bytes) |
| `artifacts/prao_pytest_tmp3/` | 179 | 4.12 MiB (4,315,470 bytes) |
| `artifacts/praj_pytest_tmp4/` | 73 | 3.68 MiB (3,854,140 bytes) |
| `artifacts/praj_pytest_tmp/` | 99 | 2.90 MiB (3,042,231 bytes) |
| `artifacts/praj_pytest_tmp6/` | 99 | 2.89 MiB (3,034,360 bytes) |
| `artifacts/praj_pytest_tmp2/` | 99 | 2.89 MiB (3,034,356 bytes) |
| `artifacts/pral_pytest_tmp2/` | 110 | 2.74 MiB (2,869,136 bytes) |
| `artifacts/pram_pytest_tmp3/` | 145 | 2.39 MiB (2,510,196 bytes) |
| `artifacts/praq_pytest_reg3/` | 144 | 2.39 MiB (2,509,273 bytes) |
| `artifacts/prai_pytest_tmp8/` | 145 | 2.38 MiB (2,495,983 bytes) |
| `artifacts/prak_pytest_tmp3/` | 108 | 2.18 MiB (2,289,925 bytes) |
| `artifacts/prak_pytest_tmp8/` | 108 | 2.18 MiB (2,289,911 bytes) |
| `artifacts/prak_pytest_tmp2/` | 108 | 2.08 MiB (2,176,117 bytes) |
| `artifacts/praq_pytest_verify1/` | 89 | 1.99 MiB (2,083,242 bytes) |
| `artifacts/praj_pytest_tmp5/` | 110 | 1.91 MiB (2,004,603 bytes) |
| `artifacts/prai_pytest_tmp5/` | 70 | 1.62 MiB (1,702,516 bytes) |
| `artifacts/prai_pytest_tmp/` | 61 | 1.37 MiB (1,439,056 bytes) |
| `artifacts/pral_pytest_tmp6/` | 44 | 1.17 MiB (1,230,756 bytes) |
| `artifacts/pral_pytest_tmp5/` | 44 | 1.17 MiB (1,230,736 bytes) |
| `artifacts/prai_pytest_tmp2/` | 46 | 1.15 MiB (1,207,086 bytes) |
| `artifacts/prai_pytest_tmp6/` | 36 | 978.49 KiB (1,001,977 bytes) |
| `artifacts/prao_pytest_tmp2/` | 179 | 317.51 KiB (325,130 bytes) |
| `artifacts/prap_pytest_tmp3/` | 1 | 901 B (901 bytes) |
| `artifacts/pran_pytest_tmp7/` | 1 | 901 B (901 bytes) |


Largest A1 campaign contributions below show only the selected pytest case-store files, not permission to remove each whole campaign directory:

| Campaign prefix | Selected files | Selected bytes / size |
| --- | --- | --- |
| `development/tmp/pr_play_05/` | 4,772 | 97.13 MiB (101,844,145 bytes) |
| `development/tmp/pr_play_07/` | 4,344 | 91.87 MiB (96,335,896 bytes) |
| `development/tmp/pr_play_06/` | 2,833 | 58.58 MiB (61,425,945 bytes) |
| `development/tmp/pr_play_09/` | 2,370 | 49.80 MiB (52,215,959 bytes) |
| `development/tmp/pr_play_08/` | 2,289 | 49.36 MiB (51,758,775 bytes) |
| `development/tmp/pr_play_02_nonhttp/` | 1,311 | 32.57 MiB (34,150,248 bytes) |
| `development/tmp/pr_play_02_regression/` | 1,257 | 32.22 MiB (33,786,856 bytes) |
| `development/tmp/pr_play_11_provider_1793413368647344400/` | 1,159 | 31.60 MiB (33,138,823 bytes) |
| `development/tmp/pr_play_10_provider_1793409609823938200/` | 1,159 | 31.60 MiB (33,133,521 bytes) |
| `development/tmp/atgb03b_surface/` | 1,119 | 31.23 MiB (32,748,957 bytes) |
| `development/tmp/pr_eg_final3/` | 1,760 | 28.31 MiB (29,689,168 bytes) |
| `development/tmp/pr_eg_final2/` | 1,760 | 28.31 MiB (29,688,837 bytes) |
| `development/tmp/pr_eg_baseline/` | 1,760 | 28.05 MiB (29,415,004 bytes) |
| `development/tmp/pr_ef_r4_regression3/` | 1,760 | 28.05 MiB (29,414,997 bytes) |
| `development/tmp/pr_ef_r4_regression/` | 1,751 | 28.03 MiB (29,395,086 bytes) |
| `development/tmp/pr_ef_r4_regression2/` | 1,746 | 28.03 MiB (29,389,096 bytes) |
| `development/tmp/pr_eg_final/` | 1,517 | 25.37 MiB (26,607,298 bytes) |
| `development/tmp/pr_ef_r2_final4/` | 1,517 | 25.16 MiB (26,381,393 bytes) |
| `development/tmp/pr_ef_r2_final5/` | 1,517 | 25.16 MiB (26,381,356 bytes) |
| `development/tmp/pr_ef_r2_final3/` | 1,508 | 25.15 MiB (26,373,779 bytes) |


The A1 selector requires a path under development/tmp containing a leaf component named test_*, excluding github_checkpoint/ and maintenance_ci_venv/. The ignored root is the owner; current tests seed fresh per-test stores. Root-level scripts, baseline copies, maintenance environments and other unmatched files in that temporary tree remain C.

## Appendix B — exact archive-backed historical file list

The following files were each compared with their ZIP member `support/<same repository-relative path>`. The listed SHA-256 is the current file and verified member hash. Retain `handoff/history/pr_eg_r2c_r2_reference_eligibility_20261017/REVIEW.zip`, its manifest and this restore mapping if these working copies are ever retired. No other file in their parent directories is covered by this list.

| Repository-relative file | Bytes | SHA-256 |
| --- | --- | --- |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final_console.txt` | 26,743 | `ea15698897c9261e02a8b82aa22015c4c985bfc54f7d7649f1ae2d2fa731bcd4` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final.xml` | 116,934 | `9e83ce462788bd00f45d9601badd45af7a34a7dbadc0297f1f810722c0e7f171` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_console.txt` | 4,680 | `6ba6ace23827a1a7203cbcdf1ac687afbf99bd133860a42fcfcb25fdd7573b3a` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_freeze.json` | 135 | `b5152bef1b358d961eb8ebdb6e782914902fd59970147b7ca3fa0bd9b2dd4020` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_plan.json` | 2,581 | `e1e5ea94a287960f2742307068e46bb4b89ea6ca81d24d7e73b007b5dd7caa3f` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_qualification.json` | 37,733,582 | `6e2288b3fe767f323e75db9225868f5eb70c5a6390fd2413610863f0ce448493` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_status.json` | 151 | `7a1dcf26025680164ef866d8c807cff36c2059dd6e54e79727093c3cad1145c0` |
| `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/source_hashes.json` | 332 | `4a777dc4088bf31c26f0eb130dae03a35f15a163f70d70fb9bec65218afe06a2` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/adversarial_annotations.json` | 56,100 | `1262f8bddc884a81e811314553f9900d3989a31ae4d85c93e3d2ec8e21fbda9b` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final_console.txt` | 24,012 | `a6a61794513d9fd462cfa913dba67ac1a52859242deb556c496076defccde82b` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final.xml` | 114,883 | `ea73e6813638b323d653bab9702825608e6ccd954799c593c2a2189c1702e8b6` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_console.txt` | 4,950 | `377c8cbfd2bdf6f6d32337607428814bf12a596dc9d80d156e20563568b10974` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_freeze.json` | 135 | `9840ec48212dd1904f7e579009381072b9e3b949b834809eda8c531d1ca6927e` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_plan.json` | 2,704 | `9ee9c7766f58fa0743dd5ad3bb4526dd2166763d3f62cc2f8bae84005b713cdb` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_qualification.json` | 39,761,114 | `5043989bede5de74cabbeaafa8a1a3d9b9f305acfcc403ce62c84acb04acbf58` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_semantic_audit.json` | 86,063 | `c963410aa0dc0e2e5e6cdb9876cd449196b1d9141b52e043815a3a3d36bc287d` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/performance.json` | 2,601 | `93ead6053b48433b7e3c31331ca1ec119c9fbd8b2d9cc69316ea17d788dd5a34` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/qualification_source_hashes.json` | 1,144 | `e951f99e81cf44315cd23589cd7e1dcda4506fe185506c3e31d948dbb6c47d50` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/conversational_continuity.py` | 33,961 | `19638f542a5a3e57d7d0dda16308951a301c3d06339d81fe0ea51dc26f7dbac1` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/live_chat_interpretation.py` | 27,076 | `e1bb64a32566c02d9ff537cc67e8a7929e247270fcff04fabe8af03b8b8af126` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/player_interpretation_bridge.py` | 16,232 | `2c53e13289716032fc53d4b5ae89064ba1e9282a216e8ce2d9ad230b3241e60f` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/targeted_results.json` | 8,283 | `e1f6b28c3625f10e894d379144eb38213fa1cd15c89f2c2a89c785a31e0c515e` |
| `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/test_pr_eg_r2c_r2_reference_eligibility.py` | 13,295 | `66b37c3e1f3fede13e091a0e3bfda373ab0019d52dd15254164abeb66278c149` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final_console.txt` | 24,012 | `ce49c1cc1eb8bccce6c8cedd09af7792ccfd8114c5a0c1baf0b355514f3ddc10` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final.xml` | 113,746 | `fc46a835a21812454799c65449c28fab69c1bf104ecd400164f0f0883c40610a` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_console.txt` | 5,000 | `6aba08aaae07ad7237deda21374d5c33c456357c67a30744fd0cc88aec0ad75b` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_freeze.json` | 135 | `be4fedf5db634e4c10c7055a99d9e7f85d2b1ba607018e7fb9dbb4fab4029b2e` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_plan.json` | 2,725 | `1de23e93887811caedefc433f2d28695942bce6c212646417d8bafd2baebeec0` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_qualification.json` | 35,653,522 | `e153649b0932324287b871935dc6749e3be40b0be4b78188854b18719e14cd4f` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_status.json` | 151 | `37c1d9d16cbe424538b5adbf62d9bbf60f651efb25811ada89cd65f4d47e3ab4` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/source_hashes.json` | 332 | `2df78aa3206d520e13f7c739450991767429e05c7a340f346a14d27244239e02` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/live_chat_interpretation.py` | 26,467 | `f0903c5cd34a9a179a711b7065e55c4873b46607c3c96966f071065a72094e82` |
| `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/player_interpretation_bridge.py` | 14,489 | `1c85a75ae128bb20459de2c5dd5393cd07ed3cfd76a93bf87069e30dde8f2396` |


## Appendix C — cache files excluded because matching source was absent

These 66 ignored files total 2.54 MiB (2,664,536 bytes) and are C, not A. They are listed so an eventual source-backed cache cleanup cannot silently become a blanket cache-directory purge.

| Excluded cache path | Bytes |
| --- | --- |
| `__pycache__/_probe_routes.cpython-314.pyc` | 2,601 |
| `artifacts/pr_eg_r6/__pycache__/_debug_preseal.cpython-314.pyc` | 1,810 |
| `experiments/pr_dm/__pycache__/_probe.cpython-314.pyc` | 4,894 |
| `game/__pycache__/final_emission_opening_contamination.cpython-312.pyc` | 50,443 |
| `game/__pycache__/final_emission_opening_contamination.cpython-314.pyc` | 61,035 |
| `game/__pycache__/final_emission_rejection_severity.cpython-312.pyc` | 15,433 |
| `game/__pycache__/final_emission_rejection_severity.cpython-314.pyc` | 17,745 |
| `game/__pycache__/narration_quality_baseline.cpython-312.pyc` | 6,829 |
| `game/__pycache__/narration_quality_baseline.cpython-314.pyc` | 7,769 |
| `game/__pycache__/scene_entry_model_route.cpython-312.pyc` | 9,320 |
| `game/__pycache__/scene_entry_model_route.cpython-314.pyc` | 10,680 |
| `tests/__pycache__/_aer4_probe.cpython-314-pytest-9.0.2.pyc` | 4,057 |
| `tests/__pycache__/_debug_emit.cpython-39-pytest-8.4.2.pyc` | 1,533 |
| `tests/__pycache__/_debug_leads_tmp.cpython-314-pytest-9.0.2.pyc` | 4,763 |
| `tests/__pycache__/_debug_ssa_pass.cpython-314.pyc` | 1,446 |
| `tests/__pycache__/test_affordance_label_presentation_rc3r.cpython-314-pytest-9.0.2.pyc` | 27,033 |
| `tests/__pycache__/test_atomic_runtime_writes_and_snapshot_restore.cpython-314-pytest-9.0.2.pyc` | 14,823 |
| `tests/__pycache__/test_final_emission_non_social_strict_suppression.cpython-39-pytest-8.4.2.pyc` | 11,449 |
| `tests/__pycache__/test_final_emission_preservation_guard.cpython-314-pytest-9.0.2.pyc` | 37,251 |
| `tests/__pycache__/test_fm5_opening_salvage_seam.cpython-314-pytest-9.0.2.pyc` | 48,295 |
| `tests/__pycache__/test_fm5_opening_salvage_seam.cpython-314.pyc` | 12,040 |
| `tests/__pycache__/test_narration_local_referential_exempt.cpython-314-pytest-9.0.2.pyc` | 66,605 |
| `tests/__pycache__/test_narration_local_referential_exempt.cpython-314.pyc` | 14,574 |
| `tests/__pycache__/test_nq1_nq2_behavior_regressions.cpython-314-pytest-9.0.2.pyc` | 49,391 |
| `tests/__pycache__/test_nq1_nq2_behavior_regressions.cpython-314.pyc` | 17,573 |
| `tests/__pycache__/test_opening_fallback_owner_bucket.cpython-312-pytest-9.0.2.pyc.12828` | 13,922 |
| `tests/__pycache__/test_opening_quality.cpython-314-pytest-9.0.2.pyc` | 37,244 |
| `tests/__pycache__/test_opening_soft_stock_salvage_seam.cpython-314-pytest-9.0.2.pyc` | 51,493 |
| `tests/__pycache__/test_ownership_registry_head.cpython-314-pytest-9.0.2.pyc` | 954,997 |
| `tests/__pycache__/test_persistence_contract.cpython-314-pytest-9.0.2.pyc` | 14,838 |
| `tests/__pycache__/test_post_narrative_cleanup_memory_quarantine.cpython-314-pytest-9.0.2.pyc` | 42,790 |
| `tests/__pycache__/test_post_narrative_cleanup.cpython-312-pytest-9.0.3.pyc` | 24,285 |
| `tests/__pycache__/test_post_narrative_cleanup.cpython-314-pytest-9.0.2.pyc` | 138,963 |
| `tests/__pycache__/test_post_narrative_cleanup.cpython-314.pyc` | 15,508 |
| `tests/__pycache__/test_pr_br_c19_authority_probe.cpython-314-pytest-9.0.2.pyc` | 9,153 |
| `tests/__pycache__/test_pr_br_c19_failure_dump.cpython-314-pytest-9.0.2.pyc` | 4,642 |
| `tests/__pycache__/test_referential_clarity_residual_rc5b.cpython-314-pytest-9.0.2.pyc` | 123,160 |
| `tests/__pycache__/test_referential_clarity_residual_rc5b.cpython-314.pyc` | 5,186 |
| `tests/__pycache__/test_runtime_persistence_concurrency_and_coherency.cpython-314-pytest-9.0.2.pyc` | 35,613 |
| `tests/__pycache__/test_same_scene_authoritative_transition.cpython-39-pytest-8.4.2.pyc` | 6,883 |
| `tests/__pycache__/test_scene_entry_model_route.cpython-314-pytest-9.0.2.pyc` | 27,770 |
| `tests/__pycache__/test_synthetic_runner.cpython-314-pytest-9.0.2.pyc` | 36,905 |
| `tests/__pycache__/test_synthetic_smoke.cpython-314-pytest-9.0.2.pyc.5104` | 38,543 |
| `tests/__pycache__/test_transcript_gauntlet_lead_to_consequence.cpython-39-pytest-8.4.2.pyc` | 39,386 |
| `tests/__pycache__/test_transcript_runner_smoke.cpython-314-pytest-9.0.2.pyc.13488` | 8,783 |
| `tests/helpers/__pycache__/_bt_closeout_snapshot.cpython-314.pyc` | 8,145 |
| `tests/helpers/__pycache__/final_emission_gate_fixtures.cpython-312.pyc` | 13,808 |
| `tests/helpers/__pycache__/final_emission_gate_fixtures.cpython-314.pyc` | 16,038 |
| `tests/helpers/__pycache__/replay_bug_recurrence_classification.cpython-314.pyc` | 9,000 |
| `tests/helpers/__pycache__/replay_bug_recurrence_completion.cpython-314.pyc` | 46,850 |
| `tests/helpers/__pycache__/replay_bug_recurrence_confidence.cpython-314.pyc` | 35,604 |
| `tests/helpers/__pycache__/replay_bug_recurrence_constants.cpython-314.pyc` | 33,960 |
| `tests/helpers/__pycache__/replay_bug_recurrence_effectiveness.cpython-314.pyc` | 32,249 |
| `tests/helpers/__pycache__/replay_bug_recurrence_forecast.cpython-314.pyc` | 15,022 |
| `tests/helpers/__pycache__/replay_bug_recurrence_governance.cpython-314.pyc` | 28,019 |
| `tests/helpers/__pycache__/replay_bug_recurrence_graduation.cpython-314.pyc` | 39,954 |
| `tests/helpers/__pycache__/replay_bug_recurrence_lifecycle.cpython-314.pyc` | 20,678 |
| `tests/helpers/__pycache__/replay_bug_recurrence_maturity.cpython-314.pyc` | 60,248 |
| `tests/helpers/__pycache__/replay_bug_recurrence_outcome.cpython-314.pyc` | 24,848 |
| `tests/helpers/__pycache__/replay_bug_recurrence_portfolio.cpython-314.pyc` | 25,436 |
| `tests/helpers/__pycache__/replay_bug_recurrence_remediation.cpython-314.pyc` | 43,505 |
| `tests/helpers/__pycache__/replay_bug_recurrence_roadmap.cpython-314.pyc` | 29,258 |
| `tests/helpers/__pycache__/replay_bug_recurrence_trajectory.cpython-314.pyc` | 27,547 |
| `tests/helpers/__pycache__/replay_bug_recurrence_trends.cpython-314.pyc` | 16,614 |
| `tools/__pycache__/__init__.cpython-314.pyc` | 273 |
| `tools/__pycache__/score_pr_eg_r6_r2.cpython-312.pyc` | 8,024 |


## Appendix D — representative exact duplicate ZIP groups

These are content-equality examples, not additional approved cleanup. Preserve current handoffs and historical citations. Identical bytes at different paths can already share one Git blob; savings shown here are local working-copy duplication.

| SHA-256 | Copies | Excess logical bytes | Paths (bounded examples) |
| --- | --- | --- | --- |
| `7766f3f8b9296c15b1c14c9fa5a8a418b6047b8f9d8c337a7fcca52ae2e270eb` | 3 | 14.38 MiB (15,081,628 bytes) | `handoff/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip`; `artifacts/pr_eg_r2c_r2/predecessor_current_review/CURRENT_REVIEW.zip`; `artifacts/pr_eg_r2c_r1/review_staging/history/pr_eg_r2c_r1_topic_grounding_20261017/REVIEW.zip` |
| `39a780c1081f83d83cd5fdf242942e9c641a26791f73f5b81309418a73863231` | 2 | 7.85 MiB (8,229,096 bytes) | `handoff/history/pr_eg_r5_predecessor_before_reassessment/CURRENT_REVIEW.zip`; `handoff/history/pr_eg_r4_r1_final_delivery_integrity_20261017/REVIEW.zip` |
| `4149ca960c4d72c9b284dbd105f8dbd9c1f49327c910c0a5ac7e630fc472ff49` | 88 | 7.55 MiB (7,913,085 bytes) | `development/tmp/pr_play_11_export_atgb_1793413643850655500/test_repeated_generation_is_by0/two/CURRENT_REVIEW.zip`; `development/tmp/pr_play_11_export_atgb_1793413643850655500/test_repeated_generation_is_by0/one/CURRENT_REVIEW.zip`; `development/tmp/pr_play_11_export_atgb_1793413643850655500/test_new_and_preexisting_failu0/CURRENT_REVIEW.zip`; `development/tmp/pr_play_11_export_atgb_1793413643850655500/test_manifest_has_provenance_a0/CURRENT_REVIEW.zip`; … 84 additional copies |
| `8dc2619d2c1ca9a4fc1da5f2d7ad99ab81703529ed28283878f8376f6cc488a0` | 3 | 7.24 MiB (7,593,952 bytes) | `handoff/history/pr_play_12/REVIEW.zip`; `handoff/CURRENT_REVIEW.zip`; `handoff/CURRENT_REVIEW(20261031-141539).zip` |
| `f83918c5da1002b81d2ee5a04881aea80b384efd90d80806d6f543688ce44186` | 2 | 6.29 MiB (6,598,350 bytes) | `handoff/history/pr_eg_r5_conversational_architecture_reassessment_20261017/REVIEW.zip`; `artifacts/pr_eg_r5/package_staging/CURRENT_REVIEW.zip` |
| `c8f3318eb11dbed75112e2683a453c559a5e096376595b35ac0b6b2d117d8454` | 2 | 5.04 MiB (5,289,542 bytes) | `handoff/history/pr_eg_r4_conversational_playability_20261017/REVIEW.zip`; `handoff/history/pr_eg_r4_before_r1/CURRENT_REVIEW.zip` |
| `c48702be9ba27b2979e04e07ee4c5ee923b3b0235c8e4da5a2c4474fb5c8888b` | 3 | 2.50 MiB (2,619,914 bytes) | `handoff/history/pr_play_03/REVIEW.zip`; `handoff/CURRENT_REVIEW(20261026-204131).zip`; `development/tmp/pr_play_03/review_stage/CURRENT_REVIEW.zip` |
| `fa816c929c2d000c24f3204db67af7480b3c310386f70fa16892e1e9cff72008` | 2 | 2.26 MiB (2,366,884 bytes) | `handoff/history/pr_eg_r2c_predecessor_20261017/CURRENT_REVIEW.zip`; `handoff/history/pr_eg_r2c_host_owned_speech_20261017/REVIEW.zip` |


## Audit closeout

Only `artifacts/storage_cleanup_audit.md` is written for this task. No candidate file was deleted, moved, renamed, compressed or edited; .gitignore, source/configuration, state, fixtures, frozen ATGB evidence, history and handoffs remain unchanged. Git history was inspected read-only, not changed. No cleanup command or automatic cleanup policy ran. Current session handoff documents were intentionally not updated because this request authorizes only the audit report.
