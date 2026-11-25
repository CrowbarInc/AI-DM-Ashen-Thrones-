# AT-FG-02B-EXEC-PILOT-A — Controlled empty-directory cleanup validation

**Disposition: PASS.**

## 1. Executive summary

7 authorized roots and 27 empty descendant directories were removed. Files removed: 0. Unexpected historical removals: 0. Allowlist digest verified: True.

## 2. Disposition

**PASS.** All seven authorized empty trees were removed and the integrity comparisons passed.

## 3. Exact authorization scope

Authorization is the seven candidate IDs and paths named in the milestone instruction. The original allowlist still has `authorized_for_deletion: false` and was not modified.

The frozen inventories, not the instruction table's uniform count of five descendants, define each tree. Five candidates have five descendant directories. `AT-FG-02B-000166` and `AT-FG-02B-000201` each have one descendant, `diagnostics`. The frozen allowlist and both inventories agree. No extra directories were added to make those trees match the table.

Maximum authorized file deletions: 0. Maximum authorized root deletions: 7. The scene-scope parent was not authorized.

## 4. Source allowlist verification

Canonical allowlist digest computed: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.
Recorded digest: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.
Match: `True`.
Raw file SHA-256, which is not the canonical digest: `44931fdb7d4948d0c49bf3ad4d704db4a47796d8a40724a241e104b712542c9e`.
Candidates in the allowlist: 867.

## 5. Repository baseline

Branch `feature/product-realization`. HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. HEAD tree `fc777dc562a98f64acbaf1b2abc7bd7a5319aecb`.
Staged names: 0. Modified tracked lines: 39. Missing tracked lines: 51. Collapsed untracked entries: 289.
Index file SHA-256 before execution: `4ec4348f0dc591a1c6e0a356b6dff1d52e3f1721304b65b8a450a355f67ac6e2`.
The preflight narrative recorded zero staged changes at its initial baseline, while its in-run integrity file recorded one staged entry. This run's initial staged diff is empty.
Historical HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28` still matches. Historical modified and missing counts, 39 and 51, still match. Collapsed untracked entries are higher than the preflight's initial 281 because later preflight outputs remain untracked.

## 6. Candidate pre-deletion verification

| Candidate | Frozen digest match | Files | Descendant directories | Identity match | Status |
| --- | --- | ---: | ---: | --- | --- |
| `AT-FG-02B-000149` | `True` | 0 | 5 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000150` | `True` | 0 | 5 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000151` | `True` | 0 | 5 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000152` | `True` | 0 | 5 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000153` | `True` | 0 | 5 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000166` | `True` | 0 | 1 | `True` | DELETED-VERIFIED |
| `AT-FG-02B-000201` | `True` | 0 | 1 | `True` | DELETED-VERIFIED |

## 7. Activity and filesystem identity checks

Python, pytest, and ATGB process records before execution: 2. After execution: 2. A process blocks a candidate only when its command line contains that candidate path or directory name. Reference scan operational hits: []. Full kernel handle enumeration was not available and was not treated as a passed proof of inactivity.

Filesystem identity uses `CreateFileW` with backup semantics and open-reparse-point, then the volume serial and file index. A candidate is deleted only when the current identity equals the frozen identity on established, volume serial, file index, attributes, link count, and reparse.

## 8. Exact deletion procedure

Each eligible candidate was selected by ID and exact path. The handle was reopened without following reparse points. Identity, zero files, descendant membership, and the candidate digest were recomputed. Empty descendants were removed from deepest to shallowest with `os.rmdir`, which fails when a directory is not empty. The authorized root was removed the same way. The scene-scope parent was listed after every candidate.

No wildcard, prefix, age, recursive force, or git cleanup command was used. `artifacts/at_fg_03b/validate-runners.py` was not run.

## 9. Per-candidate results

### `AT-FG-02B-000149`

Path: `development/tmp/scene-scope-regression/combat-controls-00-362318ip`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip/pytest/test_resolve_attack_returns_ca0/data/scenes`
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip/pytest/test_resolve_attack_returns_ca0/data`
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip/pytest/test_resolve_attack_returns_ca0`
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip/pytest`
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip/diagnostics`
- `development/tmp/scene-scope-regression/combat-controls-00-362318ip`

### `AT-FG-02B-000150`

Path: `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti/pytest/test_resolve_attack_returns_ca0/data/scenes`
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti/pytest/test_resolve_attack_returns_ca0/data`
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti/pytest/test_resolve_attack_returns_ca0`
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti/pytest`
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti/diagnostics`
- `development/tmp/scene-scope-regression/combat-controls-00-83g7t1ti`

### `AT-FG-02B-000151`

Path: `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d/pytest/test_resolve_attack_returns_ca0/data/scenes`
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d/pytest/test_resolve_attack_returns_ca0/data`
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d/pytest/test_resolve_attack_returns_ca0`
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d/pytest`
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d/diagnostics`
- `development/tmp/scene-scope-regression/combat-controls-00-98u_6e1d`

### `AT-FG-02B-000152`

Path: `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70/pytest/test_resolve_attack_returns_ca0/data/scenes`
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70/pytest/test_resolve_attack_returns_ca0/data`
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70/pytest/test_resolve_attack_returns_ca0`
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70/pytest`
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70/diagnostics`
- `development/tmp/scene-scope-regression/combat-controls-00-l2eyrp70`

### `AT-FG-02B-000153`

Path: `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt/pytest/test_resolve_attack_returns_ca0/data/scenes`
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt/pytest/test_resolve_attack_returns_ca0/data`
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt/pytest/test_resolve_attack_returns_ca0`
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt/pytest`
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt/diagnostics`
- `development/tmp/scene-scope-regression/combat-controls-00-o3dz5xpt`

### `AT-FG-02B-000166`

Path: `development/tmp/scene-scope-regression/combined-00-_l9w3acr`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combined-00-_l9w3acr/diagnostics`
- `development/tmp/scene-scope-regression/combined-00-_l9w3acr`

### `AT-FG-02B-000201`

Path: `development/tmp/scene-scope-regression/combined-01-vqfi2x8w`.
Final status: `DELETED-VERIFIED`.
Deletion attempted: `True`.
Directories removed:
- `development/tmp/scene-scope-regression/combined-01-vqfi2x8w/diagnostics`
- `development/tmp/scene-scope-regression/combined-01-vqfi2x8w`

## 10. Files deleted

Files removed: 0.

## 11. Directories deleted

Roots removed: 7. Descendant directories removed: 27. Total directories removed: 34.

## 12. Storage measurements

`development/tmp` apparent bytes before 12599292540 and after 12599292540. Files before 3373987 and after 3373987. Directories before 272601 and after 272567. Directory delta 34, expected 34. Volume free-byte delta measured around the removals: 0. Apparent file bytes are the historical file measurement. The free-byte delta is allocation movement and can include unrelated filesystem activity. This pilot does not claim meaningful capacity recovery.

## 13. Integrity comparison

Child-record removals: 7. Unexpected removals: 0. Added child records: 0. Changed child metadata records: 0. Non-scene top-level metadata changes: 0. Protected trees unchanged: True. Stable review unchanged: True. Governance files unchanged: True. PR-PLAY-79D-F3 bytes unchanged during the run: True. Git HEAD, index, and staged diff unchanged: True.

## 14. Unexpected behavior

The instruction table lists five descendants for AT-FG-02B-000166 and AT-FG-02B-000201. The frozen allowlist and inventories list one descendant each.

## 15. Remaining risks

- Kernel handle tables were not enumerated for every directory. Activity uses process command lines, owner-file absence, and an immediate empty-directory removal that fails if a directory is in use or not empty.
- Metadata comparisons for the other historical directories use path, size, and mtime. They are not a new content hash of every temporary file.
- Volume free-space movement can include filesystem activity outside this pilot. Apparent file bytes are the capacity measurement for historical files.
- `AT-FG-02B-000166` and `AT-FG-02B-000201` do not have the five-descendant shape stated in the instruction table. Their frozen inventories were followed.

## 16. Recommended next milestone

Controlled nonempty-directory pilot, subject to separate authorization. Do not start it from this report.

Review package: `handoff/history/at_fg_02b_exec_pilot_a/`.
