# Ashen Thrones — Storage Cleanup Phase 1

Status: COMPLETE — Category A cleanup and validation passed

Original branch: `feature/product-realization`; original HEAD: `c16d922865b7182d47b87d27ec633f9308f1ef4c`.
Audit SHA-256: `840c8705f789687995a95d6af5d1b7eefc957f1bd90d864b7dc456116576af53`.

Original audit size: 5,919,390,899 bytes (5.51 GiB).
Fresh preflight project size: 5,919,528,374 bytes.
Files removed: **96,143**; actual logical file bytes removed: **1,888,047,624** (1.758381 GiB).
Final project size: 4377470981 bytes (4.076838 GiB)
Net project-size reduction: 1542057393 bytes (1.436153 GiB)

Measurements use logical file lengths, consistent with the audit; NTFS allocation and directory metadata are not measured.
Final size includes new isolated control/validation outputs and this report. No GitHub-history reduction is claimed.

| Group | Removed files | Removed bytes |
| --- | ---: | ---: |
| A1 | 79,025 | 1,454,736,068 |
| A2 | 13,216 | 305,416,574 |
| A3 | 3,895 | 126,518,851 |
| A4 | 5 | 1,307,087 |
| A5 | 2 | 69,044 |

## Preflight

Every candidate confirmed Git-ignored; zero tracked candidates. 4541 reference files reviewed; no invalidating A2 inbound references found.
Selectors and original per-group counts/bytes match the immutable complete audit. The 44 roots and 66 exceptions were parsed from its appendices.
Read-only process check: {'processesInspected': 365, 'otherPythonProcesses': 0, 'blockers': []}. Each file also passed an exclusive read-handle probe; this probe was repeated immediately before individual deletion.
Resolved absolute targets were checked inside the repository, aliases/reparse targets rejected, source existence rechecked for A3, and index identity checked repeatedly. Only individual os.unlink calls were used. No directories or broad trees were recursively removed. Only empty A2 directories were subsequently removed individually; other empty directories remain.
Current evidence/cache subtrees were conservatively excluded except the two explicitly approved local metrics files.

## Excluded candidates

| Path | Group | Reason |
| --- | --- | --- |
| `artifacts/pr_play_12/__pycache__/build_evidence.cpython-312.pyc` | A3 | Conservative preservation of current evidence subtree cache |
| `artifacts/pr_play_12/__pycache__/build_reports.cpython-312.pyc` | A3 | Conservative preservation of current evidence subtree cache |
| `artifacts/pr_play_05/__pycache__/run_checks.cpython-312.pyc` | A3 | Conservative preservation of current evidence subtree cache |
| `artifacts/atgb/atgb_r2_01/__pycache__/build_review.cpython-312.pyc` | A3 | Conservative preservation of current evidence subtree cache |
| `artifacts/atgb/atgb_r1_02/__pycache__/orchestration_before.cpython-312.pyc` | A3 | Conservative preservation of current evidence subtree cache |

All 66 source-missing bytecode exceptions were retained and included in preservation hashing. Categories B, C and D were not cleanup targets.

## Verification

```json
{
  "preservation_snapshot_files": 128734,
  "processes_before_deletion": {
    "processesInspected": 371,
    "otherPythonProcesses": 0,
    "blockers": []
  },
  "all_noncandidate_worktree_hashes": {
    "files": 128734,
    "changed": 0
  },
  "protected_groups": {
    "canonical_campaign_data": {
      "files": 150,
      "changed": 0
    },
    "frozen_ATGB_inputs": {
      "files": 20,
      "changed": 0
    },
    "ATGB_evidence": {
      "files": 14421,
      "changed": 0
    },
    "protected_replay_materials_except_approved_metrics": {
      "files": 116,
      "changed": 0
    },
    "current_PR_PLAY_evidence": {
      "files": 1439,
      "changed": 0
    },
    "handoffs": {
      "files": 479,
      "changed": 0
    },
    "all_tracked_worktree_files": {
      "files": 75403,
      "changed": 0
    },
    "all_66_source_missing_exceptions": {
      "files": 66,
      "changed": 0
    },
    "root_environments": {
      "files": 16548,
      "changed": 0
    }
  },
  "branch_unchanged": true,
  "head_unchanged": true,
  "refs_unchanged": true,
  "index_unchanged": true,
  "removed_files_absent": true,
  "preserved_66_present": true,
  "post_validation_preservation": {
    "files": 128734,
    "changed": 0
  },
  "only_expected_untracked_reports": true
}
```

## Non-provider validation

```json
{
  "command": [
    "C:\\Users\\Master Mandalcio\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
    "-B",
    "-c",
    "import socket,sys,pytest\ndef blocked(*a,**k): raise AssertionError(\"Network forbidden during cleanup validation\")\nsocket.socket.connect=blocked\nsocket.create_connection=blocked\nraise SystemExit(pytest.main(sys.argv[1:]))",
    "tests/test_state_authority.py",
    "tests/test_save_load.py",
    "tests/test_golden_replay_artifact_manifest.py",
    "tests/test_atgb_readiness.py::test_incompatible_baseline_refused_before_store_creation",
    "-x",
    "-q",
    "--tb=short",
    "-p",
    "no:cacheprovider",
    "-o",
    "addopts=",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\storage_cleanup_phase1_control\\validation\\cases",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\storage_cleanup_phase1_control\\validation\\pytest.xml"
  ],
  "exit_code": 0,
  "output": "development\\tmp\\storage_cleanup_phase1_control\\validation\\pytest.txt",
  "tests": 63,
  "passed": 63,
  "frozen_baseline": {
    "version": "frontier-gate-v1",
    "verified_files": 7
  }
}
```

Isolated control/output directory: `development/tmp/storage_cleanup_phase1_control`.
Validation disables provider calls, live interpretation, expression generation, preflight, bytecode and pytest cache; an explicit socket guard denies connections. No fixed-output PR-PLAY or evidence-generating suites are selected. Pytest stops at its first failure; no unrelated repair or retry is attempted.

## Git working-tree status

```
?? artifacts/storage_cleanup_audit.md
?? artifacts/storage_cleanup_phase1_report.md
```

## Unexpected findings / limits

Two earlier in-memory preparation attempts suffered tooling errors before deletion. They were read-only; the final preflight was rerun and logged by this isolated control script.
The fresh inventory differs slightly from the earlier audit because the audit report and local metadata/output files exist. Category A counts and bytes were independently matched before conservative exclusions.
Control manifests, logs and isolated test output are retained for review; they are newly authorized validation/control output and were not added to the old deletion set.
No tracked source/configuration, campaign save, regression fixture, protected evidence, environment or Git history was intentionally modified. No provider request, commit or push was performed. No application/test process was terminated.

## A2 empty-directory finalization

{
  "removed_empty_directories": 4143,
  "authorized_A2_roots": 44,
  "A2_roots_absent": 44,
  "retained_uncertain": [],
  "recursive_deletion": false,
  "files_removed_by_finalization": 0
}

Each resolved target stayed inside its exact allowlisted A2 root. Only os.rmdir on already-empty directories was used, with no recursive deletion or additional file removal. This followed passing validation.

## Final size reconciliation

The gross removal above is the sum of the exact deleted files. The measured net project reduction is smaller because local metadata and audit/control outputs increased during the operation. In particular, `.git/cursor/` now occupies 407,712,529 bytes versus 79,357,970 bytes in the audit, an increase of 328,354,559 bytes (313.14 MiB). Root `.git/` now totals 732,190,873 bytes versus 403,794,962 bytes in the audit. This IDE-owned metadata was outside the authorized cleanup and was left untouched. Branch, HEAD, refs and index preservation checks passed; this storage growth does not imply a project-history rewrite.

The retained isolated control/validation files total 17,652,087 bytes, including the exact allowlist and validation logs. No newly created control output was added to the old deletion set. All 44 A2 roots are absent; the 66 exceptions and five conservatively excluded evidence caches remain. Final direct Git status shows only the pre-existing untracked audit and this new untracked report.
