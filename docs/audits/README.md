# Audit artifacts

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
