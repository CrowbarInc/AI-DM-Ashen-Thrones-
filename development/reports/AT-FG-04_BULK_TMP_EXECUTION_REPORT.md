# AT-FG-04 — Bulk verified TMP cleanup

**Disposition: PASS.**

## 1. Authorization

The original allowlist was not modified. Deletion was limited to candidates derived by removing the seven Pilot A roots and the forty-five Pilot B roots from that allowlist.
Allowlist canonical SHA-256: `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`.
Allowlist digest match: `True`.
Manifest SHA-256: `c4114e375c26e303ffef69ce9e8324031fe190c9c9b9e746493bcd221c4ec6a2`.
Authorization ceiling: 815 roots, 1113200 files, 3671945277 apparent bytes.

## 2. Reconciliation

Derived roots: 815. Files: 1113200. Apparent bytes: 3671945277. Allocated bytes: 4110533056. Descendant directories: 55909.
Pilot B remaining-capacity match: `True`.

## 3. Repository and protected evidence

Branch `feature/product-realization`. HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`.
HEAD matches the Pilot B baseline: `True`. Index matches: `True`.
Protected mismatches before deletion: 0.

## 4. Verification

READY: 815. SKIP: 0. STOP: 0.
Dependency hits: 0.

## 5. Deletion

Candidate roots removed: 815.
Files removed: 1113200.
Directories removed, including roots: 56724.
Apparent bytes removed: 3671945277.
Allocated bytes accounted from deleted-file handles: 4110533056.
Candidates skipped: 0.
Partial candidates: 0.
Stop reason: none.

## 6. Measured storage

`development/tmp` before: 3224281 files, 264502 directories, 12099377489 apparent bytes.
`development/tmp` after: 2111081 files, 207778 directories, 8427432212 apparent bytes.
Census reduction: {'files': 1113200, 'directories': 56724, 'apparent_bytes': 3671945277}.
Free bytes before: 378772926464. Free bytes after: 380766535680. Change: 1993609216.
Apparent bytes are the sum of file sizes. The free-byte change is the measured disk-space change and includes unrelated filesystem activity.

## 7. Integrity after deletion

Protected mismatches after deletion: [].
Rejected roots still present: 3.
Pilot A roots still absent: 7. Pilot B roots still absent: 45.
Git HEAD unchanged: `True`. Git index unchanged: `True`.
Unexpected working-tree lines: [].
Removed pre-existing status lines: [].

Per-candidate results and file-level deletion records are in `development/reports/AT-FG-04_BULK_TMP_LEDGER.json` and `development/reports/AT-FG-04_BULK_TMP_DELETED_FILES.jsonl`.

No artifacts and no campaign documents were deleted.
