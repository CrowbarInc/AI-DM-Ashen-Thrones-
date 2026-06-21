# BU28 — Governance Entry-Point Convergence Sweep

Date: 2026-06-20

## Goal

Converge maintainer navigation on a single discovery index (`docs/convergence_ci_inventory.md`) instead of parallel command blocks and CI explanations across replay, failure-classification, ownership, and audit docs.

## Canonical discovery index

| Surface | Path |
| --- | --- |
| **Governance inventory (source of truth)** | [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) |
| **Split-owner matrix subsection** | [Split-owner acceptance matrix governance](../convergence_ci_inventory.md#split-owner-acceptance-matrix-governance) |
| **Edit checklist (not duplicated in inventory)** | [`docs/audits/README.md`](README.md) |
| **Test maintainer detail** | [`tests/README_TESTS.md`](../../tests/README_TESTS.md) |

## Files updated (one-line pointers added)

| File | Pointer placement |
| --- | --- |
| `docs/convergence_ci_inventory.md` | Header — declares document as governance discovery index |
| `docs/audits/README.md` | Top — inventory link before BU22 checklist |
| `docs/README.md` | Project layout — inventory bullet expanded |
| `docs/architecture_ownership_ledger.md` | Operator Note |
| `docs/testing/protected_replay_manifest.md` | After Purpose |
| `docs/testing/replay_governance_contract.md` | After Purpose |
| `docs/testing/replay_governance_registry.md` | After Purpose |
| `docs/audits/BU4_ownership_write_path_registry.md` | Executive summary — split-owner subsection link |
| `docs/audits/cycle_k_block_k2_replay_ci_promotion_2026-05-26.md` | Top — current CI navigation |
| `docs/audits/cycle_k_block_k3a_reporting_bridge_2026-05-26.md` | Top — current CI navigation |
| `docs/cycles/README.md` | Purpose — current governance navigation |
| `tests/README_TESTS.md` | Golden replay + Failure Classification Dashboard sections |
| `tests/TEST_AUDIT.md` | Governance pytest — inventory-first split-owner pointer (reduced duplication) |

## Files intentionally left unchanged

| File | Reason |
| --- | --- |
| Closeout docs already pointing at inventory (`gate_convergence_closeout.md`, `evaluator_convergence_closeout.md`, `final_emission_ownership_convergence.md`, `validation_layer_separation.md`) | Already have `CI parity: … docs/convergence_ci_inventory.md` one-liners from Block B rollout |
| `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated report; footer links to checklist/inventory via helper |
| `Makefile`, `scripts/*`, `.github/workflows/convergence-checks.yml` | Executable surfaces unchanged in BU28 (BU26 already documented CI canonical entrypoint) |
| Archive / dead governance under `docs/archive/` | Historical; not maintainer entry points |
| Most `docs/cycles/cycle_*` closure and recon notes | Historical record; `docs/cycles/README.md` now routes to inventory |
| `docs/post_evaluator_next_target_scan.md` | Planning artifact that recommended creating the inventory; left as historical rationale |
| `tests/failure_classification_contract.py` and test modules | Code, not navigation docs |

## Remaining governance entry paths (by role)

| Maintainer intent | Start here |
| --- | --- |
| **CI / convergence command parity** | `docs/convergence_ci_inventory.md` |
| **Split-owner matrix edit workflow** | Inventory → *Split-owner acceptance matrix governance* → `docs/audits/README.md` checklist |
| **Golden replay / protected scenarios** | `tests/README_TESTS.md` → Golden replay; `docs/testing/protected_replay_manifest.md` |
| **Failure classifier / dashboard** | `tests/README_TESTS.md` → Failure Classification Dashboard |
| **Test ownership / registry** | `tests/TEST_AUDIT.md`; inventory seam row for test ownership |
| **Module ownership declarations** | `docs/architecture_ownership_ledger.md` |
| **Replay governance vocabulary** | `docs/testing/replay_governance_contract.md`, `docs/testing/replay_governance_registry.md` |
| **Cycle history / promotion record** | `docs/cycles/`, `docs/audits/cycle_k_*` (each now links forward to inventory) |

## Parity guard

Documentation drift is locked by BU27: `tests/helpers/convergence_ci_inventory_contract.py` + `tests/test_split_owner_acceptance_matrix_contract.py`.

## Non-goals (unchanged)

No production emission behavior, matrix tuple, CI wiring, or executable script changes in BU28.
