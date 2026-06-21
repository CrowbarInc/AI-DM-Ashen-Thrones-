# Cycle documentation index

## Purpose

This folder is the **canonical home** for cycle-level reconnaissance, closure, and block implementation reports from the post-AER consolidation program (Cycles H through AF). These documents record what was discovered, what shipped, and what was deferred—they do **not** replace executable governance (CI workflows, registries, closeout pytest slices, or protected replay manifest).

**Current governance navigation:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) (executable CI/local parity; split-owner matrix governance in dedicated section).

## Canonical location

| Doc type | Location |
| --- | --- |
| Cycle recon / closure / block notes | **`docs/cycles/`** (this folder) |
| Dead historical audit memos (archived) | `docs/archive/dead_governance/2026-05-31/` |
| Pre–Cycle K fallback/ownership evidence | `audits/cycle_{c,d,e,f,g,q}_*.md` (unchanged; older lane) |
| Cycle K replay promotion blocks | `docs/audits/cycle_k_block_k*.md` |
| Cycle AF governance recon | `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md` |

**Normalized in Cycle AF Block AF-3 (2026-05-31):** files formerly under repo root (`cycle_ad_*`, `cycle_ae_*`), `docs/reports/cycle_*`, and `tests/cycle_r_*` were moved here via `git mv`.

## Recent contraction cycles (AA–AF)

| Cycle | Topic | Recon | Closure |
| --- | --- | --- | --- |
| **AA** | Gate authority extraction | `cycle_aa_gate_authority_extraction_recon_2026-05-31.md` | `cycle_aa_gate_authority_extraction_closure_2026-05-31.md` |
| **AB** | Fallback topology collapse | `cycle_ab_fallback_topology_collapse_recon_2026-05-31.md` | `cycle_ab_fallback_topology_collapse_closure_2026-05-31.md` |
| **AC** | Replay surface compression | `cycle_ac_replay_surface_compression_recon_2026-05-31.md` | `cycle_ac_replay_surface_compression_closure_2026-05-31.md` |
| **AD** | Test authority consolidation | `cycle_ad_test_authority_consolidation_recon_2026-05-31.md` | `cycle_ad_test_authority_consolidation_closure_2026-05-31.md` |
| **AE** | Change locality optimization | `cycle_ae_change_locality_optimization_recon_2026-05-31.md` | `cycle_ae_change_locality_optimization_closure_2026-05-31.md` |
| **AF** | Dead governance removal | [`docs/cycle_af_dead_governance_removal_recon_2026-05-31.md`](../cycle_af_dead_governance_removal_recon_2026-05-31.md) (repo `docs/`, not this folder) | `cycle_af_dead_governance_removal_closure_2026-05-31.md` |

Earlier cycles (**H–U**, **R**, block sub-reports) live in this same folder; use filename prefix (`cycle_h_`, `cycle_r_`, etc.) to browse.

## Active closeout docs (not cycle docs)

These remain **authoritative for CI/runtime behavior** and are intentionally **not** moved into `docs/cycles/`:

- `docs/convergence_ci_inventory.md` — CI seam → enforcement matrix
- `docs/evaluator_convergence_closeout.md`, `docs/gate_convergence_closeout.md`, `docs/final_emission_ownership_convergence.md` — maintenance-grade closeouts enforced in CI
- `docs/testing/protected_replay_manifest.md` — protected golden replay acceptance
- `docs/architecture_ownership_ledger.md` — runtime → test ownership routing
- `docs/current_focus.md` — active vs completed consolidation targets
