# AT-FG-02B-EXEC-PREFLIGHT — Verified cleanup authorization preparation

**Disposition: PASS.**

This was a read-only preflight. Nothing under `development/tmp/` was deleted, moved, compressed, restored, or rewritten. The allowlist is a proposal. Every included candidate has `authorized_for_deletion: false`.

## 1. Executive summary

The AT-FG-02B manifest contains 870 candidates. All of them are accounted for. 867 remain PREFLIGHT-VERIFIED, 3 are PREFLIGHT-REJECTED, and 0 are PREFLIGHT-DEFERRED.

Verified apparent capacity is 4,171,860,328 bytes (4.172 GB, 3.885 GiB). Verified file count is 1,262,906.

Allocated bytes, summed from file allocation sizes, are 4,670,263,128 (4.349 GiB). Twenty verified directories are exact fixture matches or empty shells. The other 847 are structurally supported pytest scratch. Three candidates stay out because each contains one atomic temporary file.

The allowlist content digest is `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.

A content digest records the bytes observed during this preflight. It does not by itself prove that those bytes are disposable. Dependency, fixture, and activity checks are recorded separately.

## 2. Disposition

**PASS.** Source candidates are accounted for, included paths are exact, and rejected or deferred paths stay out of the allowlist. No deletion was performed.

## 3. Repository baseline

Recorded before this preflight wrote its reports. The 39 modified and 51 missing tracked files were already present and were left in place.

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `6e59c070dcf522594c915ab39b61e198f56c3e28` |
| Staged changes | 0 |
| Modified tracked files | 39 |
| Missing tracked files | 51 |
| Untracked entries before this preflight | 281 at Git's collapsed granularity |

The verifier's own script appears in the in-run Git snapshot because that snapshot is taken after the script file exists. The 281-entry count above is the snapshot taken before any preflight file was created.

Preflight start: 2026-11-22T04:49:38Z. No `python.exe`, `pytest.exe`, or ATGB process was returned by the process query.

Active PR-PLAY pointer in `docs/NEXT_SESSION.md`: `pr_play_fresh_live_foundational_capability_validation`. Stable `handoff/CURRENT_REVIEW.*` was hashed and left unchanged. AT-OPT-01 through AT-OPT-06 are present. No AT-OPT-07 milestone was opened.

The three incident paths were absent at the start and were not recreated.

## 4. Source manifest validation

Source file: `development/reports/AT-FG-02B_CLEANUP_CANDIDATES.json`. SHA-256 `686a54828d0da43ef40ab0b6310b8bc0c57ff24576ba0acc8b98adaa38e8c76d`.

The manifest parsed. Candidate IDs are unique. Candidate paths are unique. Every path is repository-relative, classified `VERIFIED-DISPOSABLE-CANDIDATE`, and marked `authorized_for_deletion: false`. No wildcard, parent traversal, protected descendant, incident path, or ancestor relationship was present. No additional deletion candidates were added.

## 5. Candidate verification methodology

Each candidate was opened without following reparse points. Directory identity used the volume serial and file index. The metadata digest uses the AT-FG-02B algorithm: sorted siblings, path, size, and mtime_ns, with reparse points not descended.

File contents were hashed with streaming SHA-256. The candidate digest is SHA-256 of the exact path, descendant directories, file sizes, and file hashes, sorted as described in the allowlist method field.

A candidate stays verified only when the metadata digest, file count, directory count, and apparent size match the source manifest, every file is a `.json` or `.jsonl` file under `pytest/`, fixture comparison does not find unexplained files, the reference rescan finds no new operational citation, and no active-use flag is set. The recorded metadata digest uses repository-relative scandir paths, the same form as AT-FG-02B.

## 6. Current filesystem measurements

`development/tmp/` measured 3,373,987 files, 272,601 directories, and 12,599,292,540 apparent bytes.

Legacy sharded metadata SHA-256 current `52ebe416cf33a40dbacefa307c3d7a85e70806fffcfa7d48a4a24eb4e054628d`, prior `52ebe416cf33a40dbacefa307c3d7a85e70806fffcfa7d48a4a24eb4e054628d`, match `True`.

Scene-scope legacy SHA-256 match `True`.

## 7. Content hashing results

Verified candidates: 867. Their per-file inventories are gzip JSONL files under `artifacts/at_fg_02b_exec_preflight/file-inventories/`. Each allowlist entry records the inventory SHA-256 and the candidate digest.

Allowlist SHA-256: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.

Method: SHA-256 of the canonical allowlist object with the digest field removed.

## 8. Evidence-dependency findings

Reference rescan covered 4440 operational files and skipped 0 files larger than 2 MB. New hit files outside the AT-FG-02B classification records: 0.

Published regression evidence checked for each producer is recorded in the integrity report. Prior AT-FG-02B reference rows were required to remain `NO_ACTIVE_DEPENDENCY`.

Fixture comparison uses current `data/` as the canonical source. A `pytest/<test>/data/<rel>` file is compared with `data/<rel>`. A `pytest/<test>/<rel>` file is compared with `data/<rel>`. `EXACT` means every file matches that source, or the directory has no files. `STRUCTURALLY_SUPPORTED` means every file remains `.json` or `.jsonl` under `pytest/`, including test-mutated copies and generated session files. `NOT_EQUIVALENT` is excluded.

## 9. Active execution checks

No Python, pytest, or ATGB process was observed at the start or end of the preflight. Verified directories contain no `.ashen-execution-owner` file. Their metadata digests still match the AT-FG-02B census, so their membership did not change during classification or this preflight.

Kernel handle tables were not enumerated for every file. An old timestamp alone was not treated as proof of inactivity. The conclusion uses the combination of process absence, owner-file absence, and unchanged metadata. A later deletion must repeat the check.

## 10. Verified, rejected, and deferred counts

| Status | Candidates |
| --- | ---: |
| PREFLIGHT-VERIFIED | 867 |
| PREFLIGHT-REJECTED | 3 |
| PREFLIGHT-DEFERRED | 0 |
| Accounted | 870 |

Excluded candidates:

- `AT-FG-02B-000011` `development/tmp/npc-regression/combined-fpj12tsi` — PREFLIGHT-REJECTED: `pytest/test_http_whole_request_no_par11/data/session.json.tmp.7ghpoqe7`.
- `AT-FG-02B-000015` `development/tmp/npc-regression/focused-_xxeeyc2` — PREFLIGHT-REJECTED: `pytest/test_invalid_state_never_repai6/data/session.json.tmp.4nunnn3n`.
- `AT-FG-02B-000045` `development/tmp/posture-regression/focused-o7e9v4n1` — PREFLIGHT-REJECTED: `pytest/test_wrong_binding_or_request_5/data/character.json.tmp.y9sglq_0`.

## 11. Verified recovery capacity

| Measure | Value |
| --- | ---: |
| Apparent bytes | 4,171,860,328 |
| Apparent GB | 4.172 |
| Apparent GiB | 3.885 |
| Allocated bytes | 4,670,263,128 |
| Allocated GiB | 4.349 |

Apparent size is not free space. Allocation is the sum of file allocation sizes and omits directory-entry clusters.

## 12. Proposed pilot batch

The proposal contains 10 directories, 6,148 files, and 9,824,400 apparent bytes. Limits are 10 directories, 10,000 files, and 50,000,000 apparent bytes. The inspection producer's smallest directory does not fit beside the smaller producers without passing 10,000 files, so it is not in the pilot. Execution is not authorized.

| Candidate | Path | Files | Apparent bytes |
| --- | --- | ---: | ---: |
| `AT-FG-02B-000149` | `development/tmp/scene-scope-regression/combat-controls-00-362318ip` | 0 | 0 |
| `AT-FG-02B-000002` | `development/tmp/npc-regression/acceptance-2evvyd1_` | 1449 | 851298 |
| `AT-FG-02B-000044` | `development/tmp/posture-regression/focused-8drd75v_` | 3859 | 3980364 |
| `AT-FG-02B-000082` | `development/tmp/repeat/ownership-u96lkpzg` | 840 | 4992738 |
| `AT-FG-02B-000150` | `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti` | 0 | 0 |
| `AT-FG-02B-000151` | `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d` | 0 | 0 |
| `AT-FG-02B-000152` | `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70` | 0 | 0 |
| `AT-FG-02B-000153` | `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt` | 0 | 0 |
| `AT-FG-02B-000166` | `development/tmp/scene-scope-regression/combined-00-_l9w3acr` | 0 | 0 |
| `AT-FG-02B-000201` | `development/tmp/scene-scope-regression/combined-01-vqfi2x8w` | 0 | 0 |

## 13. Protected artifact integrity

Stable review files were unchanged. Social reconciliation matches the AT-FG-03B-R1 content hash. AT-OPT-01 through AT-OPT-06, the fresh live campaign directory, both live campaign stores, and the prior AT-FG review packages matched their before and after content hashes, and they match the R1 protected inventory.

The frozen PR-PLAY-79D-F3 manifest lists 150 files. Six of those files differ from the current Git HEAD: `data/combat.json`, `data/world.json`, `data/session.json`, `data/session_log.jsonl`, `data/scenes/market_quarter.json`, and `data/scenes/old_milestone.json`. Their hashes at the end of this preflight match the hashes recorded at the start. This preflight did not write them. The other 144 frozen files match. This is not a full-repository content hash.

## 14. Remaining risks

- A verified directory can change after this preflight and before a later deletion.
- Handle enumeration did not cover every candidate file.
- Fixture equivalence does not mean the scratch copy is a published regression report. The published reports remain outside these directories.
- Allocated bytes can be lower than apparent bytes when files are sparse or compressed by the filesystem.
- The reference scan skipped files larger than 2 MB and skipped campaign `evidence/` trees.

## 15. Recommended next milestone

Controlled pilot execution of the proposed batch only, after a separate authorization. Immediately before any removal, recompute the candidate digest and refuse the path if it differs. Do not start that work from this report.

Review package: `handoff/history/at_fg_02b_exec_preflight/REVIEW.zip`. Stable `handoff/CURRENT_REVIEW.*` was not replaced.
