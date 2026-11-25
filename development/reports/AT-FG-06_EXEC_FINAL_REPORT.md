# AT-FG-06-EXEC final report

**Verdict PARTIAL.** 3,477 verified historical deletions and 1,565,286,999 net apparent bytes at the durable execution evidence boundary.

| Check | Result |
|---|---:|
| Retention policy adjustment | PASS |
| Focused and existing executor validation | PASS |
| Authorization verification | PASS |
| Immediate targets deleted | 464 |
| Consolidation groups completed | 19 |
| Conditional targets deleted | 3,013 |
| Total files deleted | 3,477 |
| Retained or unprocessed targets | 16,434 |
| Retained or unprocessed groups | 5 |
| Gross apparent source bytes removed | 1,861,544,540 |
| Gross allocated source bytes removed | 1,865,888,496 |
| New retained archive bytes, apparent / allocated | 285,942,389 / 285,986,816 |
| Retention index bytes, apparent / allocated | 300,905 / 344,064 |
| Durable governance bytes, apparent / allocated | 10,014,247 / 10,064,560 |
| Net apparent recovery | 1,565,286,999 |
| Net allocated recovery | 1,569,493,056 |
| Measured volume free-space change | 1,326,239,744 |
| Unauthorized deletions | 0 |
| Protected evidence and active state | PASS |
| Git HEAD, index and tracked changes | PASS |
| Remaining projected recovery | 1,633,671,130 bytes |

The frozen projection was 3,079,638,222 apparent bytes. The established offline comparison reproduced the same five inherited PR-PLAY-72V assertions across 37 cases. Measured free space is a volume-wide observation. Review packaging has separate storage accounting in `REVIEW_VERIFICATION.json`.

## Retained population

- 14,833 files. Retained object access does not match the source access profile.
- 1,601 files. complete group includes protected or dependent members.

## Evidence and restoration

- Adjusted release SHA-256 is `ffc5b89c22b219809ad85cde79162965e2cbb3fd515b87ff38f3d2074998f744`. The original preparation release remains intact.
- The archived receipt summary records the verified archive and index seals and points to the authoritative SQLite ledger at `artifacts/at_fg_06_exec_runtime/continuation.sqlite3` when execution created it. The compressed deletion evidence binds the exact verified source objects.
- Find the selected file in the retention index or the existing-carrier sidecar and verify the whole ZIP against its receipt. Extract only the exact case-sensitive member into a new directory with verified access controls and recreate its original repository-relative path. Compare the restored length and SHA-256 with the frozen inventory or retention record before use. The stored creation and write times and ordinary attributes can be reapplied where practical.

**Further historical cleanup recommended NO.** Close this workstream. The residual is an estimate tied to the excluded scope and its existing protection or access requirements.
