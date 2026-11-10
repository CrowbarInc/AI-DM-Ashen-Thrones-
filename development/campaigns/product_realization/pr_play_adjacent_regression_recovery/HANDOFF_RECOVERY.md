# Handoff recovery

## Established facts

At entry, docs/NEXT_SESSION.md, handoff/CURRENT_REVIEW.md, and handoff/REVIEW_MANIFEST.json already
identify Adjacent Regression Reconciliation. Seven audit reports, a 12-row classification matrix,
current/historical captures, JUnit logs, an export directory and a dated audit ZIP exist.
Thus the audit did execute and update reports and NEXT_SESSION; alternatives 1–3 are contradicted
by local evidence. A completed local audit exists, though this recovery revises its classifications.

`handoff/CURRENT_REVIEW.zip` has SHA-256
`648317fb809da2e8f2dfb2baa3dc17a0be8c892d8cd9669272bad8507a14f540`, identical to
`CURRENT_REVIEW(20261108-172122).zip`; both internally identify the previous post-NPC repair.
`CURRENT_REVIEW(20261108-174500).zip` instead identifies the audit; its SHA-256 is
`4b1b8e9533aee81cc6d7a39155a2c4aae24f39bf3832a0c043577be2f57c5f2d`.
The audit export under artifacts/pr_play_adjacent_regression/review_export is also distinct.
See archive_diagnosis.json for exact members, sizes, hashes and internal summary headers.

## Cause and limits

Confirmed local failure mode: publication of the new review surfaces was incomplete/inconsistent;
the stable ZIP retained the previous cycle while Markdown and manifest advanced. This matches
stale-file packaging/selection or reuse (alternatives 4–6). The exact copy command, directory-selection
mistake, or execution interruption cannot be determined from available logs. No evidence establishes
alternative 7. Do not infer a particular command solely from mtimes.
The specifically reported CURRENT_REVIEW(20261108-232824).zip does not exist in this workspace;
its rename/copy history and contents cannot be independently inspected. That remains unresolved.

## Procedure examined and corrected

docs/review_handoff_standard.md and tools/build_review_handoff.py require explicit source configuration.
build_handoff writes CURRENT_REVIEW.md, REVIEW_MANIFEST.json, and CURRENT_REVIEW.zip together in the
selected output directory. It does not automatically synchronize exports generated elsewhere or
create a timestamped stable-root copy. Existing configuration/export are preserved as historical evidence.

This recovery uses a new explicit configuration in artifacts/pr_play_adjacent_regression_recovery/.
Generate directly to handoff with --no-history, preserving prior history. Copy the freshly generated
stable ZIP to CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip using America/New_York time. Open that exact new
archive; enumerate members; read both internal CURRENT_REVIEW.md and support/docs/NEXT_SESSION.md;
verify all eight reports, 12 matrix entries, canonical hashes, and absence of prior-package identity.
Record external archive SHA-256 and verification JSON after sealing. Archive hashes cannot be embedded
in the archive they hash without a circular dependency. Packaging failure alone does not rerun tests.
