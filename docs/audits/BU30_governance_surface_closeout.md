# BU30 — Governance Surface Final Closeout Audit

Date: 2026-06-20  
Scope: BU20–BU29 split-owner / convergence governance stack (post-BJ matrix governance lane)

## Executive summary

BU20–BU29 built a **contract-first governance surface** for the split-owner acceptance matrix: one canonical tuple, one generated audit report, one CI read-only gate, one local refresh wrapper, and test-locked documentation navigation. The **critical path** (matrix → report → CI check → discovery index) is **self-maintaining when maintainers run the refresh workflow before merge**.

**Is post-BJ governance self-maintaining?** **Mostly yes, with bounded manual steps.** CI and fast-lane pytest catch matrix/report/dashboard-builder drift and core doc/CI parity without human memory. Remaining gaps are **adjacent surfaces** (dashboard evidence strings, explicit row-count constants, secondary doc forward pointers, opt-in probe suite, deep classifier/FEM behavior tests) that still rely on maintainer judgment or non-CI test slices.

**Recommendation: CLOSE the BU20–BU30 governance block.** Residual manual steps are documented, low-frequency, and acceptable. Future work should be **targeted extensions** (not reopening the block) unless production split-owner semantics change materially.

Prior sweep record: [`BU28_governance_entrypoint_sweep.md`](BU28_governance_entrypoint_sweep.md).

---

## Governance assets inventory

| BU | Asset | Type | Classification |
| --- | --- | --- | --- |
| BU20/BU21 | `SPLIT_OWNER_ACCEPTANCE_MATRIX` + `split_owner_acceptance_matrix_contract_misalignments()` | Code contract | Self-verifying + CI-enforced + locally enforced |
| BU20/BU21 | `scripts/check_split_owner_acceptance_matrix.py` | CLI gate | CI-enforced + locally enforced |
| BU20/BU21 | `tests/test_split_owner_acceptance_matrix_contract.py` | Pytest | Self-verifying + locally enforced (fast lane) |
| BU20/BU21 | `.github/workflows/convergence-checks.yml` step *Split-owner acceptance matrix contract* | CI | CI-enforced |
| BU22 | `docs/audits/README.md` edit checklist | Documentation | Documentation-only (workflow guide) |
| BU23 | `Makefile` targets `split-owner-matrix-*` | Developer shortcut | Locally enforced (delegates to Python) |
| BU24 | `scripts/refresh_split_owner_acceptance_matrix.py` + `split_owner_acceptance_matrix_ops.py` | CLI refresh | Locally enforced |
| BU25 | `tests/test_refresh_split_owner_acceptance_matrix.py` | Pytest | Self-verifying + locally enforced |
| BU26 | `docs/convergence_ci_inventory.md` → *Split-owner acceptance matrix governance* | Discovery index | Documentation-only (+ BU29 guard) |
| BU27 | `tests/helpers/convergence_ci_inventory_contract.py` (script/workflow parity) | Doc parity guard | Self-verifying + locally enforced |
| BU28 | Forward pointers across audit/replay/ownership entry docs | Documentation | Documentation-only (partial guard) |
| BU29 | Navigation link parity (inventory header + 2 forward pointers) | Doc parity guard | Self-verifying + locally enforced |
| — | `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated report | Self-verifying (rendered vs on-disk compare) |
| — | `test_failure_classifier.py::test_cross_family_split_owner_acceptance_matrix_stays_aligned` | Deep alignment test | Locally enforced (not `split_owner_matrix_contract` marker) |
| — | `test_failure_dashboard_controlled_failures.py` (opt-in probes) | Dashboard evidence | Locally enforced (opt-in marker; not CI default) |

---

## Self-maintaining mechanisms

### Matrix and report (BU20)

| Drift vector | Detection | Where |
| --- | --- | --- |
| Matrix ↔ checked-in report | Rendered report ≠ on-disk `BU15_*.md` | `split_owner_acceptance_matrix_contract_misalignments()` |
| Row count / legacy / dashboard counts | Expected constants vs live counts | Same + `test_split_owner_acceptance_matrix_contract_counts_are_explicit` |
| Dashboard `{matrix_id}_split_owner` case ids | Case-id parity helper | Contract misalignments |
| Classifier/dashboard **builder** surfaces | Lightweight builder drift per row | `split_owner_acceptance_matrix_classifier_builder_misalignments()` |

### Tooling and CI (BU21–BU24)

| Mechanism | Role |
| --- | --- |
| `check_split_owner_acceptance_matrix.py` | **CI-canonical** read-only gate (no file writes) |
| `refresh_split_owner_acceptance_matrix.py` | Local report + check + optional pytest slice |
| `make split-owner-matrix-refresh` | Unix shortcut → refresh wrapper |
| Fast lane | Includes `-m split_owner_matrix_contract` tests |

### Documentation (BU26–BU29)

| Mechanism | Role |
| --- | --- |
| `docs/convergence_ci_inventory.md` | Governance discovery index |
| `convergence_inventory_doc_contract_errors()` | Locks inventory phrases, script names, workflow step, `docs/audits/README.md` + `tests/README_TESTS.md` forward links |

---

## Remaining manual synchronization points

| # | Manual step | When required | Auto-detected? |
| --- | --- | --- | --- |
| 1 | Run `python scripts/refresh_split_owner_acceptance_matrix.py` (or Make equivalent) after matrix edits | Every matrix change | **Partial** — CI fails if report stale; maintainer must remember to regenerate before push |
| 2 | Update `SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_*` constants when row counts change | Add/remove matrix rows | **Partial** — count mismatch fails contract; constants must be updated intentionally |
| 3 | Update `_CONTROLLED_PROBE_EVIDENCE_CELLS` in `test_failure_dashboard_controlled_failures.py` | Dashboard evidence strings change | **No** in CI default — opt-in `failure_dashboard_probe` suite |
| 4 | Run focused classifier / FEM / golden-replay tests when **behavior** changes | Projection or taxonomy logic changes | **No** — not part of `split_owner_matrix_contract` slice |
| 5 | Update secondary BU28 forward-pointer docs (ledger, replay manifest, cycle notes, etc.) | New entry-point doc added | **No** — only 2 docs parity-guarded (audit README, tests README) |
| 6 | Keep `Makefile` targets aligned with refresh CLI flags | CLI refactor | **No** — convention only |
| 7 | Regenerate BU15 footer via `render_split_owner_acceptance_matrix_report()` when footer template changes | Helper template edit | **Yes** — report text compare catches stale on-disk report |

**Count: 7 manual synchronization points** (3 fully manual in CI, 2 partial, 2 guarded by contract).

---

## Residual risks (can drift without detection?)

| Relationship | CI / fast contract | Residual risk |
| --- | --- | --- |
| Matrix ↔ report | **Detected** | None if refresh run or CI check fails merge |
| Matrix ↔ dashboard **case ids** | **Detected** (builder + parity) | Low |
| Matrix ↔ dashboard **evidence cell text** | **Not in CI default** | Medium — opt-in probe suite only |
| Matrix ↔ classifier **deep behavior** | **Partial** (builder + cross-family test outside marker slice) | Low–medium on taxonomy changes |
| Matrix ↔ FEM projection | **Partial** (builder + `test_failure_classifier` cross-family) | Low on projection-only edits |
| Inventory ↔ CI workflow | **Detected** (BU27/BU29 guard) | Low |
| Audit docs ↔ inventory (2 primary entry docs) | **Detected** (BU29) | Low |
| Audit docs ↔ inventory (secondary BU28 docs) | **Not detected** | Low — navigation only |
| Makefile ↔ Python wrappers | **Not detected** | Low — delegates today |

---

## Recommended retirements

| Item | Action |
| --- | --- |
| Duplicate raw `python -c` report regeneration snippets | **Retired** — use refresh wrapper / Make (BU24/BU23) |
| Parallel CI entry via refresh wrapper | **Do not add** — check script remains canonical (BU26) |
| Copying full checklists into `convergence_ci_inventory.md` | **Avoid** — link to `docs/audits/README.md` (BU28) |
| Manual-only matrix validation before push | **Replace** with `refresh_split_owner_acceptance_matrix.py` habit |

No production emission modules should be changed for governance closeout.

---

## Metrics

| Metric | Count | Notes |
| --- | ---: | --- |
| **`split_owner_matrix_contract` pytest tests** | **22** | 10 in `test_split_owner_acceptance_matrix_contract.py`, 12 in `test_refresh_split_owner_acceptance_matrix.py` |
| **Parity guard modules** | **2** | `failure_classification_sync` matrix contract; `convergence_ci_inventory_contract` doc/CI parity |
| **CI-enforced checks (split-owner lane)** | **1** | `python scripts/check_split_owner_acceptance_matrix.py` in `convergence-checks.yml` |
| **Locally enforced CLI entrypoints** | **2** | check script + refresh wrapper (+ 3 Make targets) |
| **Generated governance artifacts** | **1** | `docs/audits/BU15_split_owner_acceptance_matrix.md` |
| **Doc parity–guarded forward pointers** | **2** | `docs/audits/README.md`, `tests/README_TESTS.md` |
| **BU28 secondary pointer docs (unguarded)** | **12** | See BU28 sweep table |
| **Manual synchronization points remaining** | **7** | See table above (3 fully manual in default CI) |

---

## BU final assessment

| Criterion | Status |
| --- | --- |
| Matrix contract gate in CI | ✅ |
| Report regeneration tooling | ✅ |
| Windows-native maintainer path | ✅ |
| Documentation discovery index | ✅ |
| Navigation parity tests | ✅ (primary entry docs) |
| Zero human memory for critical path | ⚠️ Maintainer must run refresh before push |
| Zero human memory for all adjacent surfaces | ❌ Dashboard evidence + deep behavior tests |

### Verdict

**CLOSE BU20–BU30.** The governance surface is **mature enough to operate without block-level follow-ups**. The stack is **self-maintaining for merge-blocking drift** on matrix, report, dashboard builder parity, and primary doc/CI wiring.

### If continuing (optional, post-close)

| ID | Follow-up | Priority |
| --- | --- | --- |
| BU31 (optional) | Extend doc parity guard to 1–2 high-traffic secondary entry docs (`protected_replay_manifest.md`, `architecture_ownership_ledger.md`) | Low |
| BU32 (optional) | Promote dashboard evidence parity into fast contract or CI smoke | Medium — only if dashboard string drift recurs |
| BU33 (optional) | Pre-commit / CI hook running `refresh --check-only` only | Low — check script already in CI |

---

## Quick reference (canonical paths)

| Need | Start here |
| --- | --- |
| Discovery index | [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) |
| Edit checklist | [`docs/audits/README.md`](README.md) |
| Local refresh | `python scripts/refresh_split_owner_acceptance_matrix.py` |
| CI gate | `python scripts/check_split_owner_acceptance_matrix.py` |
| Parity guard source | `tests/helpers/convergence_ci_inventory_contract.py` |
| Matrix source | `tests/helpers/failure_classification_sync.py` |
