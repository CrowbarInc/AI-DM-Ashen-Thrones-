# AT-FG-02B — Historical temporary storage classification

**Disposition: PASS.**

This was a read-only investigation. Nothing under `development/tmp/` was deleted, moved, compressed, restored, or rewritten. The verified set below is a proposal. Every candidate is marked `authorized_for_deletion: false`.

## 1. Executive summary

`development/tmp/` currently holds **3,373,987 files** and **12,599,292,540 apparent bytes** (12.599 GB, 11.734 GiB) in **272,601** directories. Those file and byte totals, and the legacy metadata digest, match the AT-FG-03B after-census exactly. The tree has not changed since that checkpoint.

The bytes divide without overlap:

| Category | Classified directories | Files | Apparent bytes | Apparent GB |
| --- | ---: | ---: | ---: | ---: |
| Verified disposable candidates | 870 | 1,280,158 | 4,191,191,651 | 4.191 |
| Review required | 1,640 | 2,037,207 | 7,997,102,274 | 7.997 |
| Protected | 25 | 56,622 | 410,998,615 | 0.411 |
| Unclassified | 0 | 0 | 0 | 0 |
| Total investigated | 2,535 | 3,373,987 | 12,599,292,540 | 12.599 |

Allocated bytes were not measured for every file. A stratified sample is in section 10. Deleting a directory would not necessarily free its apparent size.

Of the 999 scene-scope execution roots, **786** are verified disposable candidates and **213** stay review-required because they still contain diagnostic JSON. No scene-scope root is protected or unclassified.

The 870 candidates are exact `mkdtemp` directories whose files are pytest working copies, or which contain no files. They are not the published JUnit or partition JSON. They are not the live campaign stores. They do not include the social-reconciliation tree.

## 2. Disposition

**PASS.** The temporary tree was measured, the large producers were identified, scene-scope roots were separated by what they actually contain, and every byte was assigned to one class. The verified set was not enlarged to increase the recovery estimate.

This pass does not authorize cleanup.

## 3. Repository baseline

Recorded before new AT-FG-02B files were added.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `6e59c070dcf522594c915ab39b61e198f56c3e28` |
| Staged changes | none |
| Modified tracked files | 39 |
| Missing tracked files | 51 |
| Untracked entries | 274 at Git's collapsed granularity |

Modified tracked files: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/README.md`, `docs/ruleset_contract_registry.md`, `docs/system_overview.md`, `game/api.py`, `game/api_turn_support.py`, `game/campaign_reset.py`, `game/campaign_state.py`, `game/conversational_continuity.py`, `game/conversational_orchestration.py`, `game/dialogue_authority.py`, `game/exploration.py`, `game/integrated_play.py`, `game/intent_parser.py`, `game/interaction_completion.py`, `game/live_chat_interpretation.py`, `game/ordinary_semantic_ownership.py`, `game/physical_adjudication.py`, `game/player_commitment.py`, `game/player_http_projection.py`, `game/player_interpretation_bridge.py`, `game/referenced_surface.py`, `game/resolution_contract.py`, `game/response_policy_enforcement.py`, `game/scene_destination_binding.py`, `game/social.py`, `game/storage.py`, `handoff/CURRENT_REVIEW.md`, `handoff/CURRENT_REVIEW.zip`, `handoff/REVIEW_MANIFEST.json`, `pytest.ini`, `tests/conftest.py`, `tests/test_at_opt_02_retreat_and_budget.py`, `tests/test_pr_eb_conversational_continuity.py`, `tests/test_pr_play_post_npc_handoff.py`, `tests/test_pr_play_t04_local_action.py`, `tools/atgb/driver.py`, `tools/atgb/isolation.py`.

The 51 missing tracked paths are historical `CURRENT_REVIEW(timestamp).zip` archives already absent at the start of this milestone. They were not restored.

Active PR-PLAY pointer in `docs/NEXT_SESSION.md`: `pr_play_fresh_live_foundational_capability_validation`. Execution complete, integrity pass, capability mixed. Review archive `development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/CURRENT_REVIEW(20261121-194840).zip`, SHA-256 `62c7a26c4fc5170de1c2667c43d65578af6b7c7c971472de2bd0f7ba46fa0dc4`.

Stable review set, left unchanged: `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip`. The stable summary still identifies `pr_play_extended_live_continuity_validation` from 2026-11-18. That disagreement was already recorded by AT-FG-02A and was not repaired here.

AT-OPT: AT-OPT-01 through AT-OPT-06 are present. AT-OPT-06 is the numbered closeout. No AT-OPT-07 milestone was found. Their content hashes match the AT-FG-03B-R1 protected inventory.

Existing review archives confirmed present: `handoff/history/at_fg_03a/`, `handoff/history/at_fg_03b/`, `handoff/history/at_fg_03b_r1/`. Their content hashes match the R1 inventory.

Authorities read: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/review_handoff_standard.md`, `docs/NEXT_SESSION.md`, AT-FG-01, AT-FG-02A manifest and execution report, AT-FG-03A report and producer manifest, AT-FG-03B report and producer manifest, AT-FG-03B-R1 incident report, execution report, and ownership audit.

Process check at entry: `Get-Process` and a CIM query found no `python.exe` and no `pytest.exe`. The check is point-in-time. It does not prove that every future command will stay idle, and it did not enumerate command lines of unrelated processes. No test runner was identified.

The three incident paths are absent and were not recreated:

- `development/tmp/social-reconciliation/case-1-6zsp9s66`
- `development/tmp/social-reconciliation/case-1-i9v07y94`
- `development/tmp/social-reconciliation/case-1-sezxtw9q`

## 4. Current storage census

One no-reparse metadata walk. File contents were not hashed. Reparse points were recorded and not followed. The recorded reparse count for the walk is 0.

| Measure | Value |
| --- | ---: |
| Files | 3,373,987 |
| Directories inside `development/tmp` | 272,601 |
| Immediate directories | 1,425 |
| Immediate files | 60 |
| Apparent bytes | 12,599,292,540 |
| Apparent GB (1 GB = 1,000^3) | 12.599 |
| Apparent GiB (1 GiB = 1,024^3) | 11.734 |
| Legacy sharded metadata SHA-256 | `52ebe416cf33a40dbacefa307c3d7a85e70806fffcfa7d48a4a24eb4e054628d` |
| Scene-scope legacy sharded metadata SHA-256 | `ee60fd51678b4a7f7f4687164f63c23d0fad1381bf071b73c655e04ae80da81a` |
| Walk time | 446 seconds |

The legacy digests use the AT-FG-03B algorithm: SHA-256 of the hex digests of the direct `development/tmp` listing, each non-scene top directory, and each scene-scope child. Both digests match `artifacts/at_fg_03b/storage-after.json`. The scene digest also matches AT-FG-03A.

The directory total matches the AT-FG-03B-R1 size census (272,601). The AT-FG-03B storage file reports 271,602 directories because that combined total omits the 999 scene-scope root directories themselves. The difference is 999. File counts and apparent bytes are the comparable totals, and they match.

Dominant extensions by apparent bytes: `.json` 3,242,513 files and 7.607 GB; `.jsonl` 88,835 files and 3.597 GB; `.py` 39,960 files and 1.192 GB.

Volume at the start of the investigation: cluster size 4,096 bytes; free space available to the caller 360,674,082,816 bytes. Free space is a volume measurement, not a property of these directories.

Census evidence: `artifacts/at_fg_02b/census-summary.json` and `artifacts/at_fg_02b/census-children.jsonl`.

## 5. Largest temporary-storage producers

Apparent bytes, including everything inside the directory.

| Directory | Files | Apparent bytes | Latest file mtime (UTC) |
| --- | ---: | ---: | --- |
| `development/tmp/scene-scope-regression` | 998,452 | 3,490,133,782 | 2026-11-21T23:42:55Z |
| `development/tmp/posture-regression` | 161,444 | 420,062,343 | 2026-11-20T00:11:24Z |
| `development/tmp/npc-regression` | 161,578 | 281,925,302 | 2026-11-19T03:32:40Z |
| `development/tmp/compound_guard` | 86,570 | 234,065,012 | 2026-11-13T00:31:46Z |
| `development/tmp/pr_play_cross_scene_recall_routing_integrity` | 89,440 | 212,015,106 | 2026-11-18T04:35:36Z |
| `development/tmp/inventory_binding` | 68,576 | 198,167,516 | 2026-11-12T00:50:42Z |
| `development/tmp/ordinary_admission` | 54,311 | 180,934,033 | 2026-11-10T12:49:09Z |
| `development/tmp/pr_play_49_workspace` | 4,578 | 154,000,730 | 2026-11-03T00:53:34Z |
| `development/tmp/pr_play_47_workspace` | 4,446 | 151,592,986 | 2026-11-03T00:26:13Z |
| `development/tmp/pr77_regression` | 19,129 | 144,121,398 | 2026-11-07T20:25:57Z |

The earliest mtime on most of these trees is 2026-03-17. That timestamp comes from fixture files copied with their original timestamps. It is not the time the test run started. Latest mtime is the useful activity bound, and even a recent mtime is not proof that a process is still running.

## 6. Scene-scope regression

`development/tmp/scene-scope-regression/` has 999 immediate execution roots, 998,452 files, and 3,490,133,782 apparent bytes. The producer is `run_regression_partitions.py`, including later campaigns that call the same `run` function. The current worker publishes numbered JUnit and partition JSON outside the scratch directory and removes a workspace it allocated. These 999 roots predate that cleanup. The repaired lifecycle does not by itself make the historical roots disposable. Each root was classified from its contents.

Naming groups, from the directory names:

| Suite prefix | Roots |
| --- | ---: |
| focused | 223 |
| combined | 195 |
| scoped | 112 |
| posture | 107 |
| scene | 106 |
| inspection | 65 |
| acceptance | 64 |
| ownership | 64 |
| reconciliation | 43 |
| harness | 15 |
| combat-controls | 5 |

A clean root has every file under `pytest/`, an empty `diagnostics/` directory or none, no XML, log, markdown, text, storage, or `.ashen-execution-owner` file, and a tempfile-style name. Those `pytest/` trees are per-test copies of campaign fixture files (`campaign.json`, `character.json`, `world.json`, and the same family of stores). `tests/helpers/storage_isolation.py` copies those fixtures into the test store. They are not canonical `data/` and they are not the live campaign.

A sampled clean root, `acceptance-00-0q12874s`, is only `diagnostics/` (empty) and `pytest/<test-name>/data/` fixture files.

213 roots are not clean. Their `diagnostics/` directories contain files such as `marking_snapshots.json`, `inspection_removal_timeline.json`, `atomic_failure_create.json`, and `removal_failure_sync.json`. Campaign evidence trees elsewhere also contain files of those names. Byte identity between each scratch copy and a published copy was not established, so those 213 roots stay review-required.

20 of the 786 verified scene roots contain no files. They are empty `pytest/` and `diagnostics/` shells.

Published keepers for this producer are the numbered partition JSON and JUnit files under campaign `evidence/regression/<suite>/partitions/`. The sampled partition JSON records selected tests and production hashes. It does not record the scratch path. Several runs share one published slot. The scratch directory is the workspace, not the published result.

| Classification | Roots | Files | Apparent bytes |
| --- | ---: | ---: | ---: |
| Verified disposable candidates | 786 | 870,393 | 3,323,025,969 |
| Review required | 213 | 128,059 | 167,107,813 |
| Protected | 0 | 0 | 0 |
| Unclassified | 0 | 0 | 0 |

The newest scene-scope file mtime is 2026-11-21T23:42:55Z, on the clean root `harness-00-_xqkcdwd`. That timestamp is already inside the AT-FG-03B metadata digest, so this investigation did not create it, and no Python test process was running at the check.

## 7. Other producer families

The AT-FG-03A and AT-FG-03B manifests name the producers. Historical contents were judged separately from the repaired lifecycle.

| Family | What the census shows | Classification |
| --- | --- | --- |
| Posture regression, 34 roots | Every file is under `pytest/`. No diagnostics, XML, or owner file. | All 34 verified candidates. 161,444 files, 420,062,343 bytes. |
| NPC regression, 34 roots | Same pytest-only structure. | All 34 verified candidates. 161,578 files, 281,925,302 bytes. |
| Repeat, 11 of 12 roots | Pytest-only `combined-*` and `focused-*` roots. | 11 verified candidates. 54,003 files, 110,258,963 bytes. |
| Repeat remainder | `repeat/__pycache__`, plus `diagnose_legacy_repeat.py` and `initial-current-scene-setup.json` directly in the parent (386,634 bytes). | Review required. The JSON may be a setup record that was not shown to exist elsewhere. |
| Inspection, 5 of 16 roots | Pytest-only. | 5 verified candidates. 32,740 files, 55,919,074 bytes. |
| Inspection remainder | Roots with a `store/` role outside `pytest/`, plus XML and logs. | Review required. 11 roots. |
| Social reconciliation | 21 children and `finalize_reports.py` (8,849 bytes) directly in the parent. Many children are pytest-only. The whole tree is withheld. | Protected. See section 12. |
| Live campaigns | `pr_fresh_live_campaign` (69 files, 39,683 bytes) and `pr_fresh_live_campaign_reconciled` (70 files, 966,487 bytes, latest mtime 2026-11-22T00:42:06Z). | Protected. |
| `pr_play_47_workspace`, `pr_play_49_workspace` | Copied checkouts. AT-FG-01 found source in these trees that differs from the current checkout. | Protected. |
| `compound_guard`, `inventory_binding`, `ordinary_admission`, cross-scene, short multiturn, campaign-ruleset, authored-topic, `pr77`/`pr78`, `pr_play_66_focused_*`, visibility and object-instance pytest trees, and the remaining named pytest bases | Files sit outside a pure `pytest/` role, or the tree is a campaign workspace whose published copy was not matched file by file. | Review required. |
| Sixty files directly in `development/tmp/` | Historical probe scripts, logs, and JSON such as `atgb_r2_03_package.py` and `pr_bl_full_suite_2.txt`. | Review required. 1,383,973 bytes. |
| `development/tmp/pytest` | The old shared pytest base. 11 files, latest mtime 2026-11-21T23:16:56Z. | Review required. It was touched recently and is a fixed path, not a unique `mkdtemp` name. |
| `development/tmp/git_sync` | 14 files, 79,998,159 bytes. Includes the large inventory from AT-FG-01. | Review required. |

A repaired producer is not evidence that its old output is disposable. Posture, NPC, repeat, and inspection roots were admitted only when the same structural test used for scene-scope passed.

## 8. Evidence-reference findings

Operational scan: `.py`, `.md`, `.ini`, `.json`, and `.txt` under `docs/`, `development/reports/`, `tests/`, `tools/`, `game/`, `handoff/` (history excluded), and `development/campaigns/` with `evidence/` directories excluded. Files larger than 2 MB were skipped. The scan covered the exact directory names of all 870 candidates.

**Result: 0 files contained an exact candidate directory name.** No candidate was demoted.

| Reference | Type | Significance |
| --- | --- | --- |
| `run_regression_partitions.py` uses `development/tmp/scene-scope-regression` as the parent for a new `mkdtemp` | Active dependency on the parent directory only | Future runs need the parent. They do not read historical children. |
| Legacy posture, NPC, social, repeat, and inspection runners allocate under their parents | Active dependency on those parents only | Same distinction. |
| `artifacts/at_fg_03b_r1/baseline/named-tmp-roots.json` | Historical evidence reference | Content hashes of scene-scope children from the R1 census. It records the directories. It does not load them. |
| AT-FG-01, AT-FG-02A, AT-FG-03A, AT-FG-03B reports | Documentary reference | They describe the parent sizes and say not to clean historical scratch from those milestones. |
| Partition JSON under campaign `evidence/regression/` | Published result, not a scratch dependency | Sampled files name tests and production hashes, not the `mkdtemp` directory. |
| Files named `marking_snapshots.json` under campaign evidence and under 213 scratch diagnostics directories | Unresolved equivalence | Same filename is not byte identity. Those scratch roots were not proposed. |

Evidence equivalence for the 870 candidates is **structural, not byte-identical**. The required published record is the JUnit and partition JSON outside scratch. The candidate bodies are pytest fixture copies produced by the storage-isolation helper, or empty shells. This investigation did not hash every fixture against `data/`. A later deletion milestone must revalidate path, digest, counts, and bytes. It must not treat a rerun as a substitute for the original files.

## 9. Classification methodology

A directory was verified disposable only when all of the following were true:

1. It is an immediate child of a known `mkdtemp` parent: scene-scope, posture, NPC, repeat, or inspection.
2. Its name ends in a tempfile-style eight-character suffix.
3. It is not under `social-reconciliation` and it is not one of the three incident paths.
4. Every file is under `pytest/`, or the directory contains no files.
5. Diagnostic, XML, log, markdown, text, storage, and `.ashen-execution-owner` counts are zero.
6. There is no reparse point and no census anomaly.
7. The exact name was absent from the operational scan.
8. The metadata digest matches a tree that has not changed since the AT-FG-03B after-census.

Social children that look pytest-only were still protected. The incident showed that a shared prefix is not ownership, and the R1 social content hash is an integrity anchor for the whole tree.

Parents that contain both verified and review-required children were not proposed. Candidates are the exact child paths.

## 10. Verified cleanup candidates

870 exact paths are in `development/reports/AT-FG-02B_CLEANUP_CANDIDATES.json`.

| Parent | Candidates | Files | Apparent bytes |
| --- | ---: | ---: | ---: |
| `scene-scope-regression` | 786 | 870,393 | 3,323,025,969 |
| `posture-regression` | 34 | 161,444 | 420,062,343 |
| `npc-regression` | 34 | 161,578 | 281,925,302 |
| `repeat` | 11 | 54,003 | 110,258,963 |
| `pr_play_inspection_communication_admission_integrity` | 5 | 32,740 | 55,919,074 |
| Total | 870 | 1,280,158 | 4,191,191,651 |

Each record carries the metadata SHA-256, file count, descendant directory count, and apparent bytes from the census. `directory_count` is the number of directories inside the candidate, not including the candidate itself. `allocated_bytes` is null because allocation was sampled, not measured for all 1,280,158 files. `authorized_for_deletion` is false on every record.

## 11. Review-required storage

7,997,102,274 apparent bytes. This includes 225 execution roots that failed the structural test (213 of them scene-scope diagnostics), 1,415 other top-level directories, 60 loose files in `development/tmp/`, and the two loose files in `repeat/`.

The largest of these are campaign pytest bases and workspaces whose files are not confined to `pytest/` and whose keepers were not matched. They may contain unique regression state. They are not an allowlist.

## 12. Protected storage

410,998,615 apparent bytes.

| Path | Why it is protected | Files | Apparent bytes |
| --- | --- | ---: | ---: |
| `development/tmp/pr_fresh_live_campaign` | Active PR-PLAY campaign state | 69 | 39,683 |
| `development/tmp/pr_fresh_live_campaign_reconciled` | Reconciled live campaign state, written 2026-11-22 | 70 | 966,487 |
| `development/tmp/pr_play_47_workspace` | Historical source snapshot called out by AT-FG-01 | 4,446 | 151,592,986 |
| `development/tmp/pr_play_49_workspace` | Historical source snapshot called out by AT-FG-01 | 4,578 | 154,000,730 |
| `development/tmp/social-reconciliation/` and its 21 children | Incident parent. Includes `finalize_reports.py` (8,849 bytes). | 47,459 | 104,398,729 |

The three deleted incident directories remain absent. They are already-missing, not candidates, and not part of the protected byte total.

The 8,849-byte difference between the AT-FG-03B social row (104,407,578 bytes, 47,460 files) and the R1 / current total (104,398,729 bytes, 47,459 files) is exactly `finalize_reports.py`. The AT-FG-03B named-directory combine counted that direct file twice. The file is still present. No social bytes are missing relative to the R1 census.

## 13. Unclassified storage

None. Directories that could not be proposed were classified review-required or protected instead of being forced into the verified set.

## 14. Recovery potential

| Category | Directories | Files | Apparent GB | Allocated GiB |
| --- | ---: | ---: | ---: | --- |
| Verified disposable candidates | 870 | 1,280,158 | 4.191 | not measured |
| Review required | 1,640 | 2,037,207 | 7.997 | not measured |
| Protected | 25 | 56,622 | 0.411 | not measured |
| Unclassified | 0 | 0 | 0 | not measured |
| Total investigated | 2,535 | 3,373,987 | 12.599 | not measured |

Directory counts in this table are the classified directory records: 870 candidate roots, 1,640 review containers (225 roots plus 1,415 other top-level directories), and 25 protected containers (21 social children plus 4 protected top-level directories). Nested folders sit inside those records. The 272,601 census directories are the full nested count. Bytes and files are not double-counted. The sum matches the census exactly.

**Verified reclaimable capacity:** 4,191,191,651 apparent bytes. Allocated bytes were not summed for the whole set.

**Conditional recovery capacity:** 7,997,102,274 apparent bytes. This is review-required storage. It is not part of the verified figure.

**Protected or unresolved capacity:** 410,998,615 apparent bytes protected. Unclassified apparent bytes: 0.

Allocation sample, measured with `GetFileInformationByHandleEx` on candidate files, cluster size 4,096:

| Apparent size | Files | Apparent bytes | Allocated bytes | Resident (0 allocated) |
| --- | ---: | ---: | ---: | ---: |
| 0 | 38 | 0 | 0 | 38 |
| 1–4,096 | 40 | 18,996 | 23,600 | 0 |
| 4,097–65,536 | 40 | 859,632 | 991,232 | 0 |
| 65,537 and larger | 40 | 8,068,032 | 8,155,136 | 0 |

Small files allocate more than their apparent size because of the 4,096-byte cluster. Large files in the sample were within about 1 percent. Zero-byte files in the sample allocated nothing. Directory entries, the MFT, and compression are not in the apparent totals. A deletion would free some amount near the allocated size of the files, minus anything still shared or retained by the filesystem, and the volume's free-space counter can move for unrelated reasons during the same interval. This report does not convert 4.191 GB apparent into a promised free-space gain.

## 15. Integrity verification

Before this investigation, the AT-FG-03B after-census recorded 3,373,987 files, 12,599,292,540 apparent bytes, and legacy metadata SHA-256 `52ebe416cf33a40dbacefa307c3d7a85e70806fffcfa7d48a4a24eb4e054628d`. The new census reproduced those values.

Protected content hashes match `artifacts/at_fg_03b_r1/baseline/protected-trees.json`:

| Tree | Content SHA-256 |
| --- | --- |
| `artifacts/at_opt_01` | `012e038b0c6867cae8e401c63592f551355a9497eb11bac6871d25c7e141c4e4` |
| `artifacts/at_opt_02` | `5d80e4d4496ffef8730ba8c96f7dd1b2195dfdda8d37b7954e72ba110975b9f7` |
| `artifacts/at_opt_03` | `09572f9286a94a2754deb0ccb10d2fc776cb3b2d3931e7d44e3d374cd4ba78e6` |
| `artifacts/at_opt_04` | `22c90ab1814d64ba2f0888321ffc1caa9eb72e41c5373fde2f34b1718afd4ddf` |
| `artifacts/at_opt_05` | `8a4ac252014a627aaa09ae1eb50a86622f01fe13dd764eea77dc6070dc2ec34c` |
| `artifacts/at_opt_06` | `447c23b5bbeb774f5ba74668d648dcaa396e2291bc41dc36f1bbfa32060d2480` |
| Fresh live PR-PLAY campaign directory | `a7e80e57eadfa882ddc6a70ee83715f083eb9ce0f58fab2b769b4fe2159e6290` |
| `handoff/history/at_fg_03a` | `30804e011c6e8233f8a2290e130e48c1d0d7d00b7dbcc14f956fbcf4d9e7106d` |
| `handoff/history/at_fg_03b` | `92d1312a11ebf9677788c5871eb050740eb6e7cdab1e16f8c3479b735a68446c` |

Stable review hashes recorded so a later comparison can show they were not replaced:

| File | SHA-256 |
| --- | --- |
| `handoff/CURRENT_REVIEW.md` | `1907436d25b65cd571c48c00ffeb09161d59a4ea4bb53224493c58800a61f116` |
| `handoff/CURRENT_REVIEW.zip` | `60e5af5d7b4325dba6cfad6b45d45e7e8d985dcb72ac0f61b38f9d5ea2e3a69b` |
| `handoff/REVIEW_MANIFEST.json` | `4e25e22e1742295a9b9f8f26d3a8766e0a80a864fb87785c8f01553b38efef04` |

Live campaign content hashes measured this session, for the after-check: `pr_fresh_live_campaign` `c08c5a3c64949e35c6f4af6e3255d1ee76dc4e69a00e6ae2354efdd943747974`; `pr_fresh_live_campaign_reconciled` `e9cfb18581c60bcbff4759a46a9fdea621ac27b0669351709c3dd46971e483b6`.

Candidate membership was checked again after classification by recomputing each candidate's metadata digest, file count, directory count, and apparent bytes. All 870 candidates matched. Mismatches: 0. The comparison is in `artifacts/at_fg_02b/candidate-recheck.json` and the integrity report.

No historical file was deleted or modified by this milestone. New files are the AT-FG-02B reports, the census under `artifacts/at_fg_02b/`, the history review package, and the session pointer.

## 16. Investigation limitations

- Full content hashes were not computed for the million scene-scope files. Classification uses structure, counts, and metadata digests.
- Fixture copies were not byte-compared with `data/`.
- The 213 diagnostic roots were not matched byte for byte to published diagnostics.
- The operational reference scan skipped `evidence/` trees, files over 2 MB, and artifact inventories. A path buried only inside a large evidence JSON would not have been seen. The sampled partition JSON does not cite scratch paths.
- Allocation was sampled, not enumerated.
- Process ownership is a point-in-time observation.
- The newest mtimes establish that some roots were written on 2026-11-21. The unchanged legacy digest shows they were not written during this investigation.

## 17. Recommended next milestone

Review this manifest. Do not delete anything from it yet.

If the 870 paths are accepted, a separate execution milestone may delete only those exact paths after it recomputes every metadata digest and confirms the process check. It must not use a prefix, must not touch `social-reconciliation`, and must not include the 213 diagnostic roots or the review-required 7.997 GB.

That execution is not authorized by this report.
