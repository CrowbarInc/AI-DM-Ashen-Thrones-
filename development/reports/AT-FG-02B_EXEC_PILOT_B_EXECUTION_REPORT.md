# AT-FG-02B-EXEC-PILOT-B — Controlled nonempty cleanup execution

**Disposition: PASS.**

## 1. Authorization verification

The frozen batch file was not rewritten. `execution_authorized` remains false and every candidate `authorized_for_deletion` remains false.
Approved batch SHA-256: `7dcae5393150540cbef3ce892eed6ad3459091d6649338ddb8eae2fae8dda078`.
Recomputed canonical digest: `7dcae5393150540cbef3ce892eed6ad3459091d6649338ddb8eae2fae8dda078`.
Digest match: `True`.
Raw batch SHA-256 before execution: `6119f2f170c2a5ac30bae54252d80ab8f2d19d0218e60ed674ad705c3f7499c0`. After execution: `6119f2f170c2a5ac30bae54252d80ab8f2d19d0218e60ed674ad705c3f7499c0`.
Authorization source: the Phase 2 instruction that names this digest and the 45 recorded candidates.
Separate authorization record: `development/reports/AT-FG-02B_EXEC_PILOT_B_AUTHORIZATION.json`.
Maximum authorized files: 149706. Maximum authorized apparent bytes: 499915051.

## 2. Frozen batch digest

Method: SHA-256 of UTF-8 canonical JSON with sorted keys, compact separators, and ensure_ascii false, after removing `batch_sha256`.
Candidate roots: 45. Files: 149706. Descendant directories: 8020. Apparent bytes: 499915051. Allocated bytes: 559730072.
The inventory directory count does not include the candidate root. Removing a root also removes that one directory from `development/tmp`.

## 3. Source allowlist verification

Canonical allowlist digest: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.
Expected digest: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.
Match: `True`.
Raw allowlist SHA-256: `44931fdb7d4948d0c49bf3ad4d704db4a47796d8a40724a241e104b712542c9e`.
Allowlist candidates: 867. Selected candidates present with matching IDs, paths, digests, inventories, and STRUCTURALLY_SUPPORTED classification: `True`.
Rejected candidates in the allowlist: 0. Pilot A removals in the batch: 0. The allowlist file was not regenerated or reclassified.

## 4. Repository baseline

Branch `feature/product-realization`. HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. HEAD tree `fc777dc562a98f64acbaf1b2abc7bd7a5319aecb`.
Index SHA-256 `4ec4348f0dc591a1c6e0a356b6dff1d52e3f1721304b65b8a450a355f67ac6e2`. Staged names: 0. Modified tracked lines: 39. Missing tracked lines: 51. Collapsed untracked entries: 300.
Pilot B preflight HEAD match: `True`. Index match: `True`. Modified-set match: `True`. Missing-set match: `True`.
`development/tmp` before deletion: 3373987 files, 272567 directories, 12599292540 apparent bytes.
Free bytes before deletion: 378280906752.

## 5. Candidate verification results

| Candidate | Disposition | Files | Directories | Apparent bytes | Digest match | Identity match |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `AT-FG-02B-000001` | READY | 1470 | 64 | 6608471 | `True` | `True` |
| `AT-FG-02B-000002` | READY | 1449 | 64 | 851298 | `True` | `True` |
| `AT-FG-02B-000003` | READY | 1468 | 64 | 6576998 | `True` | `True` |
| `AT-FG-02B-000004` | READY | 1538 | 67 | 6588573 | `True` | `True` |
| `AT-FG-02B-000005` | READY | 1747 | 76 | 8044239 | `True` | `True` |
| `AT-FG-02B-000006` | READY | 1747 | 76 | 7874672 | `True` | `True` |
| `AT-FG-02B-000007` | READY | 1747 | 76 | 7266894 | `True` | `True` |
| `AT-FG-02B-000008` | READY | 1470 | 64 | 6743175 | `True` | `True` |
| `AT-FG-02B-000020` | READY | 4480 | 193 | 7451582 | `True` | `True` |
| `AT-FG-02B-000021` | READY | 4480 | 193 | 7963165 | `True` | `True` |
| `AT-FG-02B-000022` | READY | 4480 | 193 | 7963128 | `True` | `True` |
| `AT-FG-02B-000023` | READY | 4480 | 193 | 7963185 | `True` | `True` |
| `AT-FG-02B-000024` | READY | 4480 | 193 | 7451511 | `True` | `True` |
| `AT-FG-02B-000025` | READY | 910 | 40 | 5169153 | `True` | `True` |
| `AT-FG-02B-000026` | READY | 910 | 40 | 5169176 | `True` | `True` |
| `AT-FG-02B-000049` | READY | 4480 | 193 | 8069234 | `True` | `True` |
| `AT-FG-02B-000055` | READY | 5950 | 256 | 29648788 | `True` | `True` |
| `AT-FG-02B-000058` | READY | 5950 | 256 | 29655069 | `True` | `True` |
| `AT-FG-02B-000059` | READY | 5950 | 256 | 29655100 | `True` | `True` |
| `AT-FG-02B-000069` | READY | 4480 | 193 | 7963072 | `True` | `True` |
| `AT-FG-02B-000070` | READY | 4479 | 193 | 7623755 | `True` | `True` |
| `AT-FG-02B-000071` | READY | 6282 | 324 | 19076787 | `True` | `True` |
| `AT-FG-02B-000072` | READY | 6019 | 942 | 7671405 | `True` | `True` |
| `AT-FG-02B-000073` | READY | 11480 | 501 | 13584055 | `True` | `True` |
| `AT-FG-02B-000074` | READY | 6282 | 324 | 19077158 | `True` | `True` |
| `AT-FG-02B-000075` | READY | 6282 | 324 | 19060846 | `True` | `True` |
| `AT-FG-02B-000076` | READY | 6019 | 942 | 7671414 | `True` | `True` |
| `AT-FG-02B-000077` | READY | 4480 | 193 | 7963206 | `True` | `True` |
| `AT-FG-02B-000078` | READY | 4480 | 193 | 7963226 | `True` | `True` |
| `AT-FG-02B-000079` | READY | 910 | 40 | 5470902 | `True` | `True` |
| `AT-FG-02B-000080` | READY | 910 | 40 | 5470942 | `True` | `True` |
| `AT-FG-02B-000081` | READY | 840 | 37 | 5420796 | `True` | `True` |
| `AT-FG-02B-000082` | READY | 840 | 37 | 4992738 | `True` | `True` |
| `AT-FG-02B-000083` | READY | 11480 | 501 | 13584036 | `True` | `True` |
| `AT-FG-02B-000532` | READY | 1190 | 53 | 6471930 | `True` | `True` |
| `AT-FG-02B-000573` | READY | 1190 | 53 | 6510215 | `True` | `True` |
| `AT-FG-02B-000658` | READY | 5670 | 245 | 59899314 | `True` | `True` |
| `AT-FG-02B-000676` | READY | 35 | 5 | 23764 | `True` | `True` |
| `AT-FG-02B-000739` | READY | 1190 | 53 | 12947571 | `True` | `True` |
| `AT-FG-02B-000745` | READY | 1190 | 53 | 12947568 | `True` | `True` |
| `AT-FG-02B-000746` | READY | 1190 | 53 | 12946953 | `True` | `True` |
| `AT-FG-02B-000750` | READY | 1190 | 53 | 12947549 | `True` | `True` |
| `AT-FG-02B-000753` | READY | 1190 | 53 | 12947567 | `True` | `True` |
| `AT-FG-02B-000757` | READY | 1190 | 53 | 12947580 | `True` | `True` |
| `AT-FG-02B-000800` | READY | 32 | 5 | 17291 | `True` | `True` |

READY before deletion: 45. Skipped before deletion: 0.
Reference-scan files: 4440. Operational or protected-evidence name hits: 0.
Python, pytest, and ATGB process records, excluding this executor: 0. A command-line match skips that candidate. Kernel handle tables were not enumerated, so a negative process search is not proof that no open handle exists.

## 6. Executor implementation and safety properties

Executor: `artifacts/at_fg_02b_exec_pilot_b/execute_pilot_b.py`.
The executor reloads the frozen batch, recomputes its digest, and requires the separate authorization record to name that same digest before deleting.
Each file is opened with `FILE_FLAG_OPEN_REPARSE_POINT` and no share mode. The SHA-256 is read from that handle. Deletion is `FileDispositionInfo` on the same handle. There is no `os.remove` fallback and no `shutil.rmtree`.
A read-only attribute is cleared only on a handle whose hash already matched, and only for that file.
Empty descendant directories are removed deepest-first with `os.rmdir` after a no-follow listing. The candidate root is removed last, after its frozen file index is checked again. Parent directories are not removed.
This is not a race-free executor. The exclusive handle closes the file-content gap. The directory empty-check and `os.rmdir` are still separate operations.
Candidates are processed in frozen-batch order. An unexpected file, identity change, or delete failure stops the remaining candidates.

## 7. Actual deletion results

Candidates removed: 45. Candidates skipped: 0. Partial candidates: 0.
Files removed: 149706. Directories removed, including roots: 8065.
Apparent bytes removed: 499915051. Allocated bytes accounted from the deleted-file handles: 559730072.
Stop reason: none.

| Candidate | Status | Files | Directories | Apparent bytes | Allocated bytes | Root absent |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `AT-FG-02B-000001` | DELETED-VERIFIED | 1470 | 65 | 6608471 | 7137208 | `True` |
| `AT-FG-02B-000002` | DELETED-VERIFIED | 1449 | 65 | 851298 | 1317120 | `True` |
| `AT-FG-02B-000003` | DELETED-VERIFIED | 1468 | 65 | 6576998 | 7103320 | `True` |
| `AT-FG-02B-000004` | DELETED-VERIFIED | 1538 | 68 | 6588573 | 7162248 | `True` |
| `AT-FG-02B-000005` | DELETED-VERIFIED | 1747 | 77 | 8044239 | 8666968 | `True` |
| `AT-FG-02B-000006` | DELETED-VERIFIED | 1747 | 77 | 7874672 | 8494936 | `True` |
| `AT-FG-02B-000007` | DELETED-VERIFIED | 1747 | 77 | 7266894 | 7909208 | `True` |
| `AT-FG-02B-000008` | DELETED-VERIFIED | 1470 | 65 | 6743175 | 7272376 | `True` |
| `AT-FG-02B-000020` | DELETED-VERIFIED | 4480 | 194 | 7451582 | 9070632 | `True` |
| `AT-FG-02B-000021` | DELETED-VERIFIED | 4480 | 194 | 7963165 | 9597768 | `True` |
| `AT-FG-02B-000022` | DELETED-VERIFIED | 4480 | 194 | 7963128 | 9597768 | `True` |
| `AT-FG-02B-000023` | DELETED-VERIFIED | 4480 | 194 | 7963185 | 9597768 | `True` |
| `AT-FG-02B-000024` | DELETED-VERIFIED | 4480 | 194 | 7451511 | 9070632 | `True` |
| `AT-FG-02B-000025` | DELETED-VERIFIED | 910 | 41 | 5169153 | 5502680 | `True` |
| `AT-FG-02B-000026` | DELETED-VERIFIED | 910 | 41 | 5169176 | 5502680 | `True` |
| `AT-FG-02B-000049` | DELETED-VERIFIED | 4480 | 194 | 8069234 | 9704264 | `True` |
| `AT-FG-02B-000055` | DELETED-VERIFIED | 5950 | 257 | 29648788 | 31874824 | `True` |
| `AT-FG-02B-000058` | DELETED-VERIFIED | 5950 | 257 | 29655069 | 31874824 | `True` |
| `AT-FG-02B-000059` | DELETED-VERIFIED | 5950 | 257 | 29655100 | 31874824 | `True` |
| `AT-FG-02B-000069` | DELETED-VERIFIED | 4480 | 194 | 7963072 | 9597768 | `True` |
| `AT-FG-02B-000070` | DELETED-VERIFIED | 4479 | 194 | 7623755 | 9253400 | `True` |
| `AT-FG-02B-000071` | DELETED-VERIFIED | 6282 | 325 | 19076787 | 21815968 | `True` |
| `AT-FG-02B-000072` | DELETED-VERIFIED | 6019 | 943 | 7671405 | 11553856 | `True` |
| `AT-FG-02B-000073` | DELETED-VERIFIED | 11480 | 502 | 13584055 | 17812584 | `True` |
| `AT-FG-02B-000074` | DELETED-VERIFIED | 6282 | 325 | 19077158 | 21815968 | `True` |
| `AT-FG-02B-000075` | DELETED-VERIFIED | 6282 | 325 | 19060846 | 21803680 | `True` |
| `AT-FG-02B-000076` | DELETED-VERIFIED | 6019 | 943 | 7671414 | 11553856 | `True` |
| `AT-FG-02B-000077` | DELETED-VERIFIED | 4480 | 194 | 7963206 | 9597768 | `True` |
| `AT-FG-02B-000078` | DELETED-VERIFIED | 4480 | 194 | 7963226 | 9597768 | `True` |
| `AT-FG-02B-000079` | DELETED-VERIFIED | 910 | 41 | 5470902 | 5806056 | `True` |
| `AT-FG-02B-000080` | DELETED-VERIFIED | 910 | 41 | 5470942 | 5806056 | `True` |
| `AT-FG-02B-000081` | DELETED-VERIFIED | 840 | 38 | 5420796 | 5731048 | `True` |
| `AT-FG-02B-000082` | DELETED-VERIFIED | 840 | 38 | 4992738 | 5300664 | `True` |
| `AT-FG-02B-000083` | DELETED-VERIFIED | 11480 | 502 | 13584036 | 17812584 | `True` |
| `AT-FG-02B-000532` | DELETED-VERIFIED | 1190 | 54 | 6471930 | 6911088 | `True` |
| `AT-FG-02B-000573` | DELETED-VERIFIED | 1190 | 54 | 6510215 | 6947952 | `True` |
| `AT-FG-02B-000658` | DELETED-VERIFIED | 5670 | 246 | 59899314 | 62117168 | `True` |
| `AT-FG-02B-000676` | DELETED-VERIFIED | 35 | 6 | 23764 | 37360 | `True` |
| `AT-FG-02B-000739` | DELETED-VERIFIED | 1190 | 54 | 12947571 | 13416752 | `True` |
| `AT-FG-02B-000745` | DELETED-VERIFIED | 1190 | 54 | 12947568 | 13416752 | `True` |
| `AT-FG-02B-000746` | DELETED-VERIFIED | 1190 | 54 | 12946953 | 13416752 | `True` |
| `AT-FG-02B-000750` | DELETED-VERIFIED | 1190 | 54 | 12947549 | 13416752 | `True` |
| `AT-FG-02B-000753` | DELETED-VERIFIED | 1190 | 54 | 12947567 | 13416752 | `True` |
| `AT-FG-02B-000757` | DELETED-VERIFIED | 1190 | 54 | 12947580 | 13416752 | `True` |
| `AT-FG-02B-000800` | DELETED-VERIFIED | 32 | 6 | 17291 | 24920 | `True` |

## 8. Per-producer accounting

| Producer | Roots removed | Files removed | Apparent bytes removed |
| --- | ---: | ---: | ---: |
| NPC | 15 | 36856 | 99685220 |
| Posture | 4 | 22330 | 97028191 |
| Inspection | 5 | 32740 | 55919074 |
| Repeat | 10 | 42523 | 96675264 |
| Scene-scope | 11 | 15257 | 150607302 |

## 9. Errors and interruptions

No candidate in this execution was skipped, interrupted, or partially deleted.

An earlier pre-deletion attempt stopped before removing any historical file. Windows directory enumeration reported `st_nlink` 0, and that attempt treated the value as a hard link. Those outputs were moved to `artifacts/at_fg_02b_exec_pilot_b/aborted-direntry-nlink/`. This execution used `os.lstat` and the file-handle link count.

## 10. Storage recovery

`development/tmp` after: 3224281 files, 264502 directories, 12099377489 apparent bytes.
Measured file reduction: 149706. Directory reduction: 8065. Apparent-byte reduction: 499915051.
Free bytes after: 378796888064. Measured free-space change: 515981312.
Allocated bytes and free space are not the same measurement. Directory allocation and concurrent filesystem activity can make the free-space change differ from the apparent-byte total.
Remaining allowlist roots present: 815. Their frozen apparent bytes: 3671945277.

## 11. Protected-evidence integrity

Protected-tree mismatches against the execution-start hashes: none.
Protected-tree mismatches against the Pilot B preflight baseline: none.
Governance mismatches: none. Stable review mismatches: none.
PR-PLAY-79D-F3 current bytes still match the preflight record: `True`.
Rejected roots still present: `True`. Pilot A roots still absent: `True`. Incident paths still absent: `True`.

## 12. Git integrity

HEAD unchanged: `True`. Index unchanged: `True`.
Modified tracked lines unchanged: `True`. Missing tracked lines unchanged: `True`.
Unexpected porcelain additions: none.
New milestone reports are untracked files under the execution output prefixes. Pre-existing tracked modifications were not restored.

## 13. Final verdict

**PASS.** All 45 authorized roots were removed, every deleted file matched its frozen inventory, and the integrity comparisons passed.

No further cleanup batch was started.

Review package: `handoff/history/at_fg_02b_exec_pilot_b_execution`.
