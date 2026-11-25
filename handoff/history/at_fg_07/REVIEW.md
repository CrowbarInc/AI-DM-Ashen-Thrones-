# Campaign

Campaign: AT-FG-07 Final TMP Cleanup and Filesystem Governance Closeout
Identifier: `at_fg_07`
Date: 2026-11-25
Generated: 2026-11-25T16:25:43-05:00
Purpose: Remove verified disposable TMP output, preserve required evidence and return to gameplay development.

# Executive Summary

Filesystem governance CLOSED. Integrity PASS. Verified removal of 54,955 files and 5,332 directories. TMP recovered 312,862,520 apparent and 335,438,056 allocated file bytes. Measured volume free-space change +90,636,288 bytes. Unauthorized deletions 0.

Objective status: `PARTIAL / ACCEPTED / CLOSED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- No changes in this category.

## Documentation changes

- Published the retention policy, workstream reports and continuation handoff.

## Generated artifacts

- Published the sealed exact manifest, execution ledger and before-and-after accounting.

# What Was Tested

- **Focused tests:** No-follow exact membership, identity, hash, and parent checks, tracked exclusions, individual absence, and census reconciliation.
- **Broader relevant tests:** Compared Git status, dirty tracked content, prior evidence anchors and retained TMP roots.
- **Full suite:** Omitted for this maintenance scope.
- **Runtime validation:** Verified the exact Windows NTFS disposition results against the census.
- **Model/runtime boundary:** Zero live provider calls.
- **New regressions:** Not reported.
- **Pre-existing failures:** Five inherited PR-PLAY-72V assertions carried forward from prior offline validation.
- **Self-contained bundle review:** The bundle carries the exact compressed manifest and seal, its compact ledger, both reports, accounting, integrity checks, policy and handoff.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- The residual TMP population is accepted. No filesystem-governance decision is needed for handoff.

# Known Problems / Unresolved Findings

## Campaign-specific

- Large mixed and ambiguous families remain documented.

## Pre-existing baseline

- Five inherited PR-PLAY-72V assertions and the grounded NPC addressee findings remain open.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- No gameplay or provider performance conclusion follows from filesystem results.

# Recommended Next Step

Resume separately authorized PR-PLAY / ATGB gameplay from the grounded NPC addressing finding. AT-OPT-06 remains the last accepted optimization milestone.

# Review Bundle Contents

Bundle file count: `13`
Bundle ZIP size: `000001541895` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/AT-FG-07_FINAL_REPORT.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/AT-FG-07_FINAL_REPORT.md`.
- `support/development/reports/AT-FG_CLOSEOUT_REPORT.md`: Workstream closeout, cumulative accounting, retained populations and disposition. Canonical source: `development/reports/AT-FG_CLOSEOUT_REPORT.md`.
- `support/docs/ARTIFACT_RETENTION_POLICY.md`: Authoritative prevention and evidence retention guidance. Canonical source: `docs/ARTIFACT_RETENTION_POLICY.md`.
- `support/docs/NEXT_SESSION.md`: Return to established PR-PLAY / ATGB development and preserved handoff history. Canonical source: `docs/NEXT_SESSION.md`.
- `support/artifacts/at_fg_07/storage-accounting.json`: Fresh before-and-after TMP inventory and storage measurements. Canonical source: `artifacts/at_fg_07/storage-accounting.json`.
- `support/artifacts/at_fg_07/integrity.json`: Git, protected evidence, scope and ledger reconciliation. Canonical source: `artifacts/at_fg_07/integrity.json`.
- `support/artifacts/at_fg_07/assessment.json`: Target selection and explicit exclusions with reasons. Canonical source: `artifacts/at_fg_07/assessment.json`.
- `support/artifacts/at_fg_07/deletion-manifest.json.gz`: Frozen target roots and their complete exact membership. Canonical source: `artifacts/at_fg_07/deletion-manifest.json.gz`.
- `support/artifacts/at_fg_07/deletion-manifest.json.gz.sha256`: Detached SHA-256 seal for the exact compressed manifest bytes. Canonical source: `artifacts/at_fg_07/deletion-manifest.json.gz.sha256`.
- `support/artifacts/at_fg_07/execution-ledger.jsonl.gz`: Compact verified execution results bound to the manifest. Canonical source: `artifacts/at_fg_07/execution-ledger.jsonl.gz`.
- `support/artifacts/at_fg_07/execution-result.json`: Execution dispositions, ledger seal and measured free-space interval. Canonical source: `artifacts/at_fg_07/execution-result.json`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
