# Audit artifacts

This directory is the canonical home for audit-cycle documentation. New audit, cycle, report,
measurement, and closeout files must not be placed in the repository root.

## Folder layout

| Folder | Contents |
|---|---|
| `discovery/` | Reconnaissance, discovery reports, inventories, candidate maps, and pre-work analysis |
| `closeouts/` | Closeouts, closures, readiness decisions, completion reports, and implementation summaries |
| `scaffolds/` | Cycle scaffolds, Codex instruction blocks, and execution checklists |
| `metrics/` | Metrics, contracts, regression/recurrence analyses, scorecards, and measurement reports |
| `ledgers/` | Audit-specific ledgers and longitudinal decision records |
| `evidence/` | Human-readable evidence, validation output, failure logs, and retained audit snapshots |
| `archived/` | Clearly superseded or obsolete audit documentation retained for history |
| `needs_review/` | Files explicitly held for human classification; ambiguous files otherwise remain at their current path |

`audit_manifest.md` is the navigation index. `documentation_inventory.csv` is the repository-wide
classification record, and `documentation_reorganization_summary.md` records the June 2026 cleanup.
Permanent ownership and path rules are defined in `documentation_governance.md`; the final debt
assessment is recorded in `documentation_governance_closeout.md`.

## Naming convention

Use a cycle/topic prefix, a descriptive subject, and a type suffix:

```text
<CYCLE>_<topic>_discovery.md
<CYCLE>_<topic>_closeout.md
<CYCLE><block>_<topic>_scaffold.md
<CYCLE>_<topic>_metric.md
<CYCLE>_<topic>_evidence.<md|json|csv|txt>
```

Recent examples:

- BW discovery: `discovery/BW_protected_replay_trend_window_discovery.md`
- BW closeout: `closeouts/BW_protected_replay_trend_window_closeout.md`
- BX discovery and closeout: `discovery/BX_speaker_identity_end_to_end_parity_discovery.md` and `closeouts/BX_speaker_identity_end_to_end_parity_closeout.md`
- BY discovery: `discovery/BY_first_semantic_mutation_attribution_discovery.md`
- BZ scaffold and metric: `scaffolds/BZ1_protected_replay_trend_window_2_scaffold.md` and `metrics/BZ2_recurrence_movement_classification.md`
- CA and CB operational reports remain temporarily flat where generators or tests own their paths.
- CC discovery: `discovery/CC_feature_readiness_closeout_discovery.md`

Before moving an existing generated report, search tests, tools, scripts, and CI for a hard-coded
path. Path-contract migrations require a separate maintenance change; do not silently relocate the
file. Normal architecture, gameplay, user, and system documentation remains under `docs/`.

Machine-readable and human-readable audit reports under `docs/audits/` support ownership, convergence, and replay-governance work. Most reports are regenerated from scripts or test helpers; treat the generator as source of truth when a report footer lists a command.

**Canonical governance inventory:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) → [Split-owner acceptance matrix governance](../convergence_ci_inventory.md#split-owner-acceptance-matrix-governance) (CI entrypoint, local refresh, contract tests). Use that index before adding parallel command blocks in audit notes.

## Split-owner matrix change workflow (BU22)

Use this checklist when editing the canonical split-owner acceptance matrix. The **BU20/BU21 contract gate** (`scripts/check_split_owner_acceptance_matrix.py`, `make split-owner-matrix-check`, CI step **Split-owner acceptance matrix contract (BU20/BU21)** in `.github/workflows/convergence-checks.yml`) must pass before merge.

**CI / convergence discovery index:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) → *Split-owner acceptance matrix governance*.

**Canonical source:** `SPLIT_OWNER_ACCEPTANCE_MATRIX` in `tests/helpers/failure_classification_sync.py`.

**Required order:**

1. **Update `SPLIT_OWNER_ACCEPTANCE_MATRIX`** — add, remove, or edit rows in `tests/helpers/failure_classification_sync.py`. Matrix-only or diagnostic edits must not change production emission behavior.
2. **Update dashboard evidence cells (only if dashboard strings changed)** — when probe evidence text or `{matrix_id}_split_owner` dashboard strings change, update `_CONTROLLED_PROBE_EVIDENCE_CELLS` in `tests/test_failure_dashboard_controlled_failures.py` and any related controlled probe fixtures in `tests/helpers/failure_dashboard_fixtures.py`.
3. **Regenerate and validate** — prefer the Windows-native refresh wrapper (BU24):

   ```bash
   python scripts/refresh_split_owner_acceptance_matrix.py
   ```

   Equivalent on Unix/mac/Git Bash: `make split-owner-matrix-refresh`.

   Step-by-step or partial runs:

   ```bash
   python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only
   python scripts/refresh_split_owner_acceptance_matrix.py --check-only
   python scripts/refresh_split_owner_acceptance_matrix.py --skip-pytest
   make split-owner-matrix-report
   make split-owner-matrix-check
   ```

4. **Run focused affected tests (only when behavior changed)** — skip when the edit is row metadata or report-only. Run the slice that matches what you touched:
   - **Classifier / taxonomy:** `python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q`
   - **Dashboard probes (opt-in):** `python -m pytest tests/test_failure_dashboard_controlled_failures.py -q -m failure_dashboard_probe`
   - **FEM projection / golden replay:** `python -m pytest tests/test_final_emission_meta.py tests/test_golden_replay_fallback_projection.py -q`
   - **Runtime lineage / attribution inventory:** `python -m pytest tests/test_runtime_lineage_telemetry.py tests/test_replacement_attribution_inventory.py -q`

**Do not skip report regeneration** — the contract compares the rendered report to the file on disk; a stale `BU15_split_owner_acceptance_matrix.md` fails CI even when the matrix tuple is correct.

See also: [`docs/convergence_ci_inventory.md`](../docs/convergence_ci_inventory.md) → *Split-owner acceptance matrix governance*, [`tests/README_TESTS.md`](../../tests/README_TESTS.md) → *Split-owner acceptance matrix contract (BU20/BU21)*, and [`docs/audits/BU15_split_owner_acceptance_matrix.md`](BU15_split_owner_acceptance_matrix.md) (generated table + maintainer footer).
