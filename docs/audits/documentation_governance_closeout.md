# Documentation Governance Closeout

Date: 2026-06-23

## Executive Summary

The remaining documentation population is predominantly immovable by design or historical rather
than unclassified debt. Of 472 retained records reviewed, 259 are generator-owned, 24 are test/path-
contract owned, and 157 are historical records whose relocation would provide little operational
value. Only 32 are technically safe future migration candidates, and six of those are normal project
documentation that should remain outside the audit hierarchy.

The practical migration opportunity is therefore 26 audit-related files. Fifteen are already within
the canonical `docs/audits/` tree and would gain only subfolder symmetry. The remaining 11 are legacy
human-readable files under `audits/`; they could be moved later, but doing so is low-value and does
not justify another repository-wide cleanup cycle.

No review item remained unknown after this pass.

## Classification Scope and Method

The review population is the union of:

- all 319 rows classified `G` in `documentation_inventory.csv`; and
- all other medium-confidence rows, primarily generated evidence and path-retained contracts.

This produced 472 unique files. Normal high-confidence project documentation was excluded because it
is not documentation cleanup debt.

Each file was assigned exactly once using the following precedence:

1. **Generator-Owned** — artifact namespace, explicit writer/refresh ownership, or a known generated
   report family.
2. **Test-Owned** — exact path referenced by tests, validation, CI, replay infrastructure, or tooling
   as an input/authority, unless the whole file is generator-owned.
3. **Historical Archive** — closed cycle or superseded investigation with no current whole-file
   generator ownership.
4. **Safe Future Migration** — documentation-only, no exact path contract, and no generator owner.
5. **Unknown** — insufficient evidence after the above checks.

This ordering prevents double counting. A generated file validated by tests remains Generator-Owned;
a human-authored policy read by tests is Test-Owned.

## Classification Results

| Bucket | Count | Review inventory | Representative examples | Migration risk |
|---|---:|---:|---|---|
| A. Generator-Owned | 259 | 54.9% | `artifacts/golden_replay/bug_recurrence_history.md`, `docs/audits/BU15_split_owner_acceptance_matrix.md`, generated BV10-BV17 report families | High; migrate writer, readers, refresh commands, and validation together |
| B. Test-Owned | 24 | 5.1% | `docs/testing/protected_replay_manifest.md`, `docs/gate_convergence_closeout.md`, `audits/cycle_av_governance_registry_inventory.md` | High; exact path is operationally significant |
| C. Historical Archive | 157 | 33.3% | Cycle C-AO closeouts, old reconnaissance, retained implementation summaries | Low technical risk, low strategic benefit |
| D. Safe Future Migration | 32 | 6.8% | legacy failure inventories, CA/CB human reports, `docs/audits/BV_follow_on_candidates.md` | Low to medium |
| E. Unknown | 0 | 0.0% | None | N/A |
| **Total** | **472** | **100.0%** |  |  |

## Complete Classification Register

Every review file is covered by the mutually exclusive rules below. The source population remains
the file-by-file `documentation_inventory.csv`.

### A. Generator-Owned — 259 files

- All 125 reviewed records under `artifacts/`.
- `audits/failure_dashboard_latest.md`.
- Generated recurrence and matrix authorities:
  `BQ16_recurrence_graduation_audit.md`, `BQC3_confidence_calibration_audit.md`,
  `BQC4_final_graduation_decision.md`, `BQC5_effectiveness_validation.md`, and
  `BU15_split_owner_acceptance_matrix.md`.
- Generated maintenance-economics and report families:
  `BV_maintenance_economics_validation_closeout.md`, `BV1A_*`, `BV1B_*`, `BV7*`, and
  `BV10*` through `BV17*`, except the eight exact Test-Owned exceptions listed below.
- `docs/audits/CA_post_baseline_cohort.csv` and
  `docs/audits/CA_post_baseline_exclusions.csv`.

The eight BV exceptions assigned to Test-Owned are:

- `BV1_bug_fix_locality_validation.md`
- `BV1_maintenance_cost_matrix.md`
- `BV2_meta_access_patterns.md`
- `BV2_meta_consolidation_verification.md`
- `BV2B_replay_attribution_migration.md`
- `BV3D_measurement_scope.md`
- `BV9_concentration_rankings.md`
- `BV9_maintenance_matrix.md`

### B. Test-Owned — 24 files

- `audits/cycle_av_governance_registry_inventory.md`
- `docs/ai_gm_contract.md`
- `docs/architecture_ownership_ledger.md`
- the eight BV exceptions listed above
- `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`
- `docs/BRL2_bug_fix_locality_regression_guard.md`
- `docs/BS_semantic_replacement_attribution_discovery.md`
- `docs/convergence_ci_inventory.md`
- `docs/gate_cleanup_inventory.md`
- `docs/gate_convergence_closeout.md`
- `docs/reports/BR_bug_fix_locality_measurement.md`
- `docs/reports/openai_api_key_lazy_config_fix_20260520.md`
- `docs/testing/protected_replay_manifest.md`
- `docs/testing/replay_governance_approval_contract.md`
- `docs/testing/replay_governance_contract.md`
- `docs/testing/replay_governance_traceability_contract.md`
- `tests/test_inventory_governance.json`

### C. Historical Archive — 157 files

- 48 closed or superseded `audits/cycle_*` records, excluding the Test-Owned AV inventory.
- 14 non-generated BP-BU records under `docs/audits/`.
- 79 non-generated and non-Test-Owned BV1-BV9 records under `docs/audits/`.
- Seven `docs/audits/cycle_k_*` records, excluding the Test-Owned K4 policy.
- Seven retained cycle/block records under `docs/cycles/`.
- Two historical OpenAI API-key fix/recon records not assigned to Test-Owned.

These files are archival in function even when they remain outside `docs/audits/archived/`.

### D. Safe Future Migration — 32 files

The 26 audit-related candidates are:

- 11 legacy human-readable files under `audits/`:
  `failure_dashboard_precision_pass_2026-05-11.md`, `failure_dashboard_probe_sample.md`,
  `failure_hotspots.md`, `failure_owner_matrix.md`, `failure_surface_inventory.md`,
  `mutation_boundary_inventory.md`, `opening_fallback_surface_inventory_2026-05-11.md`,
  `proposed_failure_classification_schema.md`, `replay_failure_corpus.md`,
  `runtime_signal_inventory.md`, and `thin_answer_fallback_surface_inventory_2026-05-12.md`.
- `docs/audits/BV_follow_on_candidates.md`.
- 14 CA/CB human-authored records currently at the flat `docs/audits/` level.

The remaining six are ordinary project documents that are technically movable but should not be
moved into audits:

- `docs/evaluator_convergence_inventory.md`
- `docs/manual_gauntlet_report_format.md`
- `docs/objective12_validation_contract.md`
- `docs/realization_seam_inventory.md`
- `docs/realization_triage_ledger.md`
- `docs/retry_fallback_selector_contract.md`

### E. Unknown — 0 files

No file lacked enough evidence for a governance classification.

## Migration Opportunity Assessment

### A. How many files remain because they are contract-bound?

**24 files.** These have exact path ownership through tests, validation, CI, replay infrastructure, or
tooling. They should not move without a planned contract migration.

### B. How many files remain because they are generator-owned?

**259 files.** Their location is part of the writer/refresh workflow. Relocating the checked-in output
alone would create drift or broken regeneration.

### C. How many files remain because they are simply undocumented?

**0 files remain unknown.** The pass established ownership for the entire 472-file review population.
There are 32 unbound files, but they are now explicitly classified rather than undocumented.

### D. How many files are realistically worth moving?

**At most 11 files.** These are the legacy human-readable audit inventories under `audits/` that
would visibly benefit from a future archive/evidence migration. The other 15 audit-related safe
candidates are already under `docs/audits/` and would gain only subfolder symmetry. The six normal
project documents should remain where they are.

No immediate move is recommended.

### E. Is another documentation cleanup cycle justified?

**No.** A new repository-wide cleanup would spend most of its effort negotiating 283 generator or
path contracts, or cosmetically moving 157 historical records. The maximum useful migration set is
11 low-value files. Future movement should be opportunistic and owner-driven.

## Recommended Future Policy

- Enforce approved locations for all new human-authored audit-cycle files.
- Treat generated paths and exact test/tool references as contracts.
- Require generator-aware migration planning rather than independent file moves.
- Leave historical records in place unless another change already touches their owner or navigation.
- Fix new root-level audit files immediately instead of accumulating another cleanup batch.
- Keep `audit_manifest.md` as the authority index and this closeout as the ownership baseline.

## Final Judgment

**Repository documentation is effectively organized.**

The residual population is 59.9% generator/test-owned and another 33.3% historical. Only 6.8% is
technically movable, and only 11 files offer a meaningful structural improvement. Documentation debt
should no longer remain an active project concern; governance should shift from cleanup campaigns to
preventing new violations.
