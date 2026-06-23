# Convergence CI inventory

**Status:** Planning / **CI parity only**. This document maps closed convergence seams to executable checks. It does **not** change runtime behavior, evaluator scoring, gate legality, or test semantics.

**Governance discovery index:** Canonical entry point for convergence CI wiring and maintainer navigation to replay, ownership, failure-classification, and split-owner governance surfaces. Edit checklists and command details stay in linked docs (`docs/audits/README.md`, `tests/README_TESTS.md`); link here rather than duplicating them.

**Non-goals:** No reopening of Evaluator, Gate, or FE-C2 cleanup blocks. Test code and production code are not rewritten here; only CI wiring and pointers are in scope.

**Automation:** Continuous integration parity is enforced by `.github/workflows/convergence-checks.yml`, including the required protected golden replay gate declared in `docs/testing/protected_replay_manifest.md`. Planner convergence remains owned by `.github/workflows/content-lint.yml` (see [Planner convergence](#planner-convergence--ctir--narrative-plan--prompt) below)—do not duplicate that step in `convergence-checks.yml`.

---

## Local and CI usage

Run from the **repository root**. GitHub Actions uses the same commands with `python` from `actions/setup-python`. On Windows, if `python` is not on `PATH`, use `py -3` in place of `python` (see `tests/README_TESTS.md`).

**Hard-fail — pytest (matches workflow order):**

```bash
python -m pytest -m golden_replay -q
python -m pytest tests/test_evaluator_convergence_closeout.py -q
python -m pytest tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q
python -m pytest tests/test_final_emission_boundary_contract.py tests/test_final_emission_boundary_convergence.py -q
python -m pytest tests/test_gate_convergence_closeout.py -q
python -m pytest tests/test_validation_coverage_audit.py -q
python -m pytest tests/test_ownership_registry.py -q
python scripts/check_split_owner_acceptance_matrix.py
python tools/test_audit.py --check
```

**Hard-fail — strict audits:**

```bash
python tools/validation_layer_audit.py --strict
python tools/final_emission_ownership_audit.py --strict
python tools/validation_coverage_audit.py --strict
```

**Informational audits (same sequence as CI; non-blocking in Actions via `continue-on-error: true`):**

```bash
python tools/run_governance_audits.py
```

Or run each tool individually: `python tools/architecture_audit.py --print-summary`, then `python tools/realization_layer_audit.py`, `python tools/realization_provenance_audit.py`, `python tools/c1_narration_seam_audit.py`, `python tools/ui_mode_separation_audit.py`.

**Planner convergence (not in `convergence-checks.yml`):** `python tools/planner_convergence_audit.py` runs in `.github/workflows/content-lint.yml` only.

**Protected replay failure artifact:** When the protected replay step fails, Actions attempts to upload the stable artifact `protected-replay-failure-report` from `artifacts/golden_replay/replay_failure_report.md`. It is not uploaded on a successful replay run; missing output is reported as a warning rather than masking the blocking replay failure. Reproduce locally with `python -m pytest -m golden_replay -q`.

---

## Classification legend

| Recommended CI status | Meaning |
| --- | --- |
| **Hard-fail** | Step fails the workflow (`continue-on-error: false`). Fix regressions or tooling breaks before merge. |
| **Informational** | Step runs with `continue-on-error: true` (or advisory-only exit 0 tools); failures surface in logs but do not fail the job until promoted in a later block. |
| **Deferred** | Not wired yet; documented for future promotion or optional local runs. |

---

## Seam → enforcement matrix

| Closed seam | Closeout / source doc | Pytest slice | Static audit / tool | In CI before Block B | Recommended CI status | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| **Protected golden replay acceptance** | `docs/testing/protected_replay_manifest.md`, `docs/audits/cycle_k_block_k1_protected_replay_declaration_2026-05-26.md` | `-m golden_replay` | — | No | **Hard-fail** | Protected end-to-end and direct-seam replay failures block acceptance; marker selection permits future protected replay expansion without workflow rewiring. |
| **Evaluator convergence** | `docs/audits/closeouts/evaluator_convergence_closeout.md`, `docs/evaluator_convergence_inventory.md` | `tests/test_evaluator_convergence_closeout.py` | — | No | **Hard-fail** | Fast lock on evaluator maintenance-grade invariants. |
| **Evaluator boundary / governance guards** | Same | `tests/test_dead_turn_evaluation_threading.py`, `tests/test_playability_eval.py`, `tests/test_behavioral_gauntlet_eval.py`, `tests/test_scenario_spine_eval.py`, `tests/test_final_emission_meta.py`, `tests/test_architecture_audit_tool.py`, `tests/test_validation_layer_audit_smoke.py` | — | No | **Hard-fail** | Same slice as closeout doc; protects evaluator-adjacent and audit-smoke coverage without extending evaluator scope. |
| **FE-C2 / final emission boundary** | `docs/final_emission_ownership_convergence.md` (Block D2), `docs/narrative_integrity_architecture.md` | `tests/test_final_emission_boundary_convergence.py`, `tests/test_final_emission_boundary_contract.py` | `tools/final_emission_ownership_audit.py` | No | **Pytests + ownership audit: Hard-fail** | Convergence scenarios + boundary contract tests; strict ownership audit catches advisory drift signals. |
| **Gate convergence** | `docs/gate_convergence_closeout.md`, `docs/gate_cleanup_inventory.md` | `tests/test_gate_convergence_closeout.py` | — (gate boundary also covered indirectly by FE-C2 tests and audits) | No | **Hard-fail** | Formal closeout regression slice for gate maintenance grade. |
| **Validation layer (Objective #11)** | `docs/validation_layer_separation.md`, `docs/validation_layer_audit.md` | `tests/test_validation_layer_audit_smoke.py` (also in evaluator boundary bundle) | `tools/validation_layer_audit.py` | No | **Hard-fail (`--strict`)** | Strict mode fails on `likely_drift`; aligns with doc “CI opt-in” language. |
| **Validation coverage registry (Objective #12)** | `docs/validation_layer_separation.md`, `tests/TEST_AUDIT.md` | `tests/test_validation_coverage_audit.py` | `tools/validation_coverage_audit.py` | No | **Hard-fail (`--strict`)** | Guard tests lock tool behavior; `--strict` fails on registry validation errors (non-strict CLI exits 0 even when errors print). |
| **Test ownership / inventory** | `docs/architecture_ownership_ledger.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `docs/audits/closeouts/cycle_bf_test_inventory_de_amplification_closeout.md` | `tests/test_ownership_registry.py` | `tools/test_audit.py --check` | Yes (`convergence-checks.yml` only) | **Hard-fail** | Registry map + committed `tests/test_inventory_governance.json` drift gate. **Do not duplicate** in `content-lint.yml` (Cycle BF8). |
| **Split-owner acceptance matrix (BU20–BU25)** | [`docs/audits/README.md`](audits/README.md), [`docs/audits/BU15_split_owner_acceptance_matrix.md`](audits/BU15_split_owner_acceptance_matrix.md) | `tests/test_split_owner_acceptance_matrix_contract.py`, `tests/test_refresh_split_owner_acceptance_matrix.py` (`-m split_owner_matrix_contract`) | **`python scripts/check_split_owner_acceptance_matrix.py`** (CI canonical); local refresh: `python scripts/refresh_split_owner_acceptance_matrix.py` | Yes | **Hard-fail** | Locks canonical split-owner literals, dashboard `{matrix_id}_split_owner` parity, checked-in audit report text, and classifier/dashboard builder surfaces. See [Split-owner acceptance matrix governance](#split-owner-acceptance-matrix-governance). |
| **Architecture governance (broad)** | `docs/architecture_ownership_ledger.md`, `docs/narrative_integrity_architecture.md` | `tests/test_architecture_audit_tool.py` (included in evaluator boundary bundle) | `tools/architecture_audit.py --print-summary` | No | **Informational** | Heuristic breadth; summary keeps artifacts warm without noisy hard-fail until signals stabilize. |
| **Narrative realization / failure locality** | `docs/audits/closeouts/realization_failure_locality_closeout.md` | Guard tests exist (`tests/test_realization_*`) but not part of this minimal CI slice | **`tools/realization_layer_audit.py`** (maps *realization surface* intent), **`tools/realization_provenance_audit.py`** (maps *failure locality / provenance* intent). Repo does **not** ship `realization_surface_audit.py` or `realization_failure_locality_audit.py` under those names. | No | **Informational** | Advisory-only exit 0; large lexical counts—observe drift, do not gate merges yet. |
| **C1 narration seam** | `docs/narrative_integrity_architecture.md` (cross-links), C1 seam docs | — | `tools/c1_narration_seam_audit.py` | No | **Informational** | AST seam tripwire; may exit 1 on issues—kept informational until noise profile is reviewed. |
| **UI mode separation (Objective #15)** | `docs/narrative_integrity_architecture.md` | — | `tools/ui_mode_separation_audit.py` | No | **Informational** | Findings print by default without fatal exit unless `--fail-on`; informational tier. |

---

## Split-owner acceptance matrix governance

BU20–BU25 lock cross-family split-owner owner literals shared by the failure classifier, failure dashboard, golden replay FEM projection, runtime lineage summary, and attribution inventory tests. **This section is the CI/local discovery index**; the edit checklist lives in [`docs/audits/README.md`](audits/README.md).

| Item | Location / command |
| --- | --- |
| **Matrix source of truth** | `SPLIT_OWNER_ACCEPTANCE_MATRIX` in `tests/helpers/failure_classification_sync.py` |
| **Checked-in audit report** | `docs/audits/BU15_split_owner_acceptance_matrix.md` (regenerate after matrix edits) |
| **CI workflow** | `.github/workflows/convergence-checks.yml` — step *Split-owner acceptance matrix contract (BU20/BU21)* |
| **Canonical CI entrypoint** | **`python scripts/check_split_owner_acceptance_matrix.py`** — read-only drift gate; no report writes; no nested pytest subprocess |
| **Local maintainer refresh (Windows-native)** | `python scripts/refresh_split_owner_acceptance_matrix.py` — report write + check + pytest contract slice (default) |
| **Make shortcuts (Unix/mac/Git Bash)** | `make split-owner-matrix-refresh`, `make split-owner-matrix-check`, `make split-owner-matrix-report` (delegate to the Python wrappers) |
| **Shared implementation** | `scripts/split_owner_acceptance_matrix_ops.py` |
| **Contract tests** | `tests/test_split_owner_acceptance_matrix_contract.py`, `tests/test_refresh_split_owner_acceptance_matrix.py` — marker `split_owner_matrix_contract` (included in fast lane) |
| **Doc / CI parity guard (BU29)** | `tests/helpers/convergence_ci_inventory_contract.py` — locks inventory header, workflow wiring, and forward pointers from `docs/audits/README.md` + `tests/README_TESTS.md` |
| **Detailed test doc** | `tests/README_TESTS.md` → *Split-owner acceptance matrix contract* |

### Why the check script is CI-canonical

CI runs **`check_split_owner_acceptance_matrix.py`**, not the refresh wrapper, because:

- **Read-only** — validates committed matrix + report; never rewrites files in Actions.
- **Fast** — single Python process; avoids refresh’s nested `pytest` subprocess on every push/PR.
- **Stable exit surface** — same misalignment messages developers see locally via `--check-only`.

Use **`refresh_split_owner_acceptance_matrix.py`** locally after editing the matrix (especially on Windows without `make`). The refresh wrapper’s default path ends with the same contract checks the check script runs, plus an optional pytest slice for extra confidence before push.

### Quick-reference commands

Run from repo root (`py -3` in place of `python` on Windows when needed):

```bash
# Local full refresh (report + check + pytest contract slice)
python scripts/refresh_split_owner_acceptance_matrix.py

# Check only (matches CI gate; no report write)
python scripts/refresh_split_owner_acceptance_matrix.py --check-only
python scripts/check_split_owner_acceptance_matrix.py

# Make equivalents (Git Bash / macOS / Linux)
make split-owner-matrix-refresh
make split-owner-matrix-check

# Pytest contract slice (also invoked by refresh default)
python -m pytest tests/test_split_owner_acceptance_matrix_contract.py tests/test_refresh_split_owner_acceptance_matrix.py -q -m split_owner_matrix_contract
```

---

## Planner convergence (CTIR → narrative plan → prompt)

| Item | Detail |
| --- | --- |
| **Closeout / doc** | `docs/planner_convergence.md` (and related planner convergence tests referenced in `tests/TEST_AUDIT.md`) |
| **Pytest** | `tests/test_planner_convergence_static_audit.py`, contract/live pipeline tests—already exercised indirectly when developers run full suites |
| **Static tool** | `tools/planner_convergence_audit.py` |
| **Current CI** | **Yes** — `.github/workflows/content-lint.yml` runs `python tools/planner_convergence_audit.py` |
| **Recommended CI status** | **Stay in `content-lint.yml`** (hard-fail there). **Do not duplicate** in `convergence-checks.yml` to avoid double runtime and conflicting ownership. |
| **Rationale / future** | Single workflow owns planner convergence. If CI consolidation is desired later, **move** the step from `content-lint.yml` into `convergence-checks.yml` in one PR and remove it from the old workflow—do not run twice. |

---

## Workflow step classification (authoritative)

Aligned with `.github/workflows/convergence-checks.yml`:

### Hard-fail

- `pytest -m golden_replay` — required protected replay acceptance; a failure fails the workflow.
- `pytest tests/test_evaluator_convergence_closeout.py`
- Evaluator boundary pytest bundle (dead-turn, playability, behavioral gauntlet, scenario spine, FEM meta, architecture audit tool, validation-layer smoke)
- `pytest tests/test_final_emission_boundary_contract.py tests/test_final_emission_boundary_convergence.py`
- `pytest tests/test_gate_convergence_closeout.py`
- `python tools/validation_layer_audit.py --strict`
- `python tools/final_emission_ownership_audit.py --strict`
- `python tools/validation_coverage_audit.py --strict`
- `pytest tests/test_validation_coverage_audit.py`
- `pytest tests/test_ownership_registry.py`
- `python scripts/check_split_owner_acceptance_matrix.py` — split-owner matrix/report/dashboard parity (canonical CI entrypoint; see [Split-owner acceptance matrix governance](#split-owner-acceptance-matrix-governance))
- `python tools/test_audit.py --check`

### Informational (`continue-on-error: true`)

- `python tools/architecture_audit.py --print-summary`
- `python tools/realization_layer_audit.py`
- `python tools/realization_provenance_audit.py`
- `python tools/c1_narration_seam_audit.py`
- `python tools/ui_mode_separation_audit.py`

### Deferred / future work

- **`tools/run_governance_audits.py`** — Thin local runner for informational audits only (`python tools/run_governance_audits.py`). Strict audits and pytest remain separate commands.

**Test inventory (wired in CI):** `python tools/test_audit.py --check` validates committed `tests/test_inventory_governance.json` drift in `convergence-checks.yml` (alongside `tests/test_ownership_registry.py`). Regenerate governance with `py -3 tools/test_audit.py`; full diagnostic via `--full` → `artifacts/test_inventory_full.json`. See `tests/TEST_AUDIT.md`.

---

## Related governance artifacts

- [`docs/audits/README.md`](audits/README.md) — split-owner matrix edit checklist (BU22).
- [`docs/audits/BU15_split_owner_acceptance_matrix.md`](audits/BU15_split_owner_acceptance_matrix.md) — generated split-owner acceptance matrix report.
- `docs/testing/protected_replay_manifest.md` — canonical protected replay declaration and developer reproduction commands.
- `docs/audits/cycle_k_block_k2_replay_ci_promotion_2026-05-26.md` — replay CI promotion record.
- `docs/audits/cycle_k_block_k3b_failure_artifact_retention_2026-05-26.md` — protected replay failure artifact retention record.
- `docs/post_evaluator_next_target_scan.md` — rationale for CI parity as next target.
- `docs/audits/closeouts/evaluator_convergence_closeout.md`, `docs/gate_convergence_closeout.md`, `docs/final_emission_ownership_convergence.md`, `docs/validation_layer_separation.md` — one-line CI pointers in each.
- `tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md` — broader test inventory (not all wired to CI).
