# Cycle AO Closeout — Replay Ownership Consolidation

**Date:** 2026-06-03  
**Status:** Complete (AO0–AO5). AO6 deferred optional.  
**Scope:** Acceptance-side replay governance consolidation; no runtime behavior changes.

---

## 1. Cycle goal recap

Cycle AO addressed replay ownership spread across helpers, manifests, projections, classifiers, and dashboards. The five ownership domains and their post-cycle authority:

| Domain | Pre-cycle state | Post-cycle authority |
|---|---|---|
| **Replay ownership boundaries** | Split across runner, projection, contract, dashboard with unclear SoT | Documented in recon + AO5; acceptance vs runtime split explicit |
| **Projection ownership** | 41 protected paths in registry but hand-wired extraction, presence, unavailable lists | `tests/helpers/golden_replay_projection.py` — registry + `_ProtectedExtractionSpec` drive extraction (AO1) |
| **Manifest ownership** | Scenario table manual; field paths CI-synced via refresh tool | Unchanged governance model; AO5 boundary note added; generated paths still derived from registry |
| **Classifier ownership** | 32-field protected overlap hand-maintained in contract | `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` derived via `protected_classifier_evidence_field_paths()` (AO2) |
| **Dashboard ownership** | 29-key evidence manifest hand-curated in dashboard module | `FAILURE_DASHBOARD_EVIDENCE_MANIFEST` contract-owned; dashboard renders only (AO3) |

**Recon artifacts (AO0):**

- `audits/cycle_ao_replay_ownership_inventory.md`
- `audits/cycle_ao_replay_schema_touchpoints.json`
- `audits/cycle_ao_replay_authority_boundaries.md`
- `audits/cycle_ao_replay_coverage_baseline.md`
- `audits/cycle_ao_candidate_blocks.md`

---

## 2. Completed blocks

### AO0 — Recon

- Mapped replay modules, schema touchpoints, authority overlaps, and test baseline
- Identified primary consolidation targets: projection extraction, classifier overlap, dashboard manifest, fixture duplication, runtime/acceptance boundary
- Recommended AO1 as first implementation block

### AO1 — Registry-driven projection extraction

- Added `_ProtectedExtractionSpec` registry (41 paths) with import-time validation
- Derived FEM/sanitizer extractors from registry; registry-driven `raw_signal_presence`, `normalized_signal_presence`, unavailable computation
- New export: `protected_observation_extraction_registry()`
- **Summary:** `audits/cycle_ao_block_ao1_implementation_summary.md`

### AO2 — Classifier evidence from protected registry

- Replaced hand-maintained 32-field `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` frozenset with `protected_classifier_evidence_field_paths()` (flat protected − 5 exclusions)
- Strengthened sync alignment checks; classifier behavior unchanged
- **Summary:** `audits/cycle_ao_block_ao2_implementation_summary.md`

### AO3 — Dashboard evidence manifest from classifier contract

- Moved `FAILURE_DASHBOARD_EVIDENCE_MANIFEST` (29 keys + labels) to `tests/failure_classification_contract.py`
- Dashboard module imports and renders; removed duplicate label lock in sync
- **Summary:** `audits/cycle_ao_block_ao3_implementation_summary.md`

### AO4 — Unified synthetic observed-row factory

- New `tests/helpers/replay_observed_row_fixtures.py` — single authority with `classifier_probe` and `dashboard_probe` profiles
- Removed duplicate builders from `failure_classification_sync.py` and `failure_dashboard_fixtures.py`
- 22 controlled failure cases unchanged
- **Summary:** `audits/cycle_ao_block_ao4_implementation_summary.md`

### AO5 — Runtime vs acceptance projection boundary

- Module docstrings cross-link runtime (`game/final_emission_replay_projection.py`) vs acceptance (`tests/helpers/golden_replay_projection.py`); do-not-merge rule
- Manifest section: **Cycle AO5 Runtime vs Acceptance Projection Boundary**
- Ownership test: `test_ao5_runtime_and_acceptance_projection_modules_remain_separate`
- **Summary:** `audits/cycle_ao_block_ao5_implementation_summary.md`

---

## 3. Ownership improvements

| Improvement | Mechanism | Edit touchpoints reduced |
|---|---|---|
| **Protected observation registry is extraction authority** | `_PROTECTED_EXTRACTION_SPECS` drives FEM/sanitizer extractors, presence, unavailable (AO1) | Was: registry + manual `project_turn_observation` blocks + separate `raw_signal_presence` dict |
| **Classifier protected overlap is derived** | `protected_classifier_evidence_field_paths()` from observation registry (AO2) | Was: 32-field manual frozenset in contract |
| **Dashboard evidence manifest is contract-owned** | `FAILURE_DASHBOARD_EVIDENCE_MANIFEST` in `failure_classification_contract.py` (AO3) | Was: 29-key tuple in `failure_dashboard_report.py` + duplicate label lock in sync |
| **Synthetic observed rows have one factory** | `replay_observed_row_fixtures.synthetic_observed_replay_row()` (AO4) | Was: parallel `observed_failure_row()` and `_observed()` baselines |
| **Runtime and acceptance projection explicitly separate** | Docstrings + manifest + ownership test (AO5) | Was: implicit split documented only in cycle recon docs |

**Preserved intentionally manual (documented):**

- `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` (47 fields) — full optional allowlist
- `CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` (15 fields) — classifier-only diagnostics
- `REQUIRED_CLASSIFICATION_FIELDS` (15 fields) — row identity/routing
- Manifest PROTECTED scenario table (markdown) — governance, not machine-readable
- `_PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS` (5 paths) — classifier-ineligible protected fields
- Compatibility paths not deleted per cycle constraints

---

## 4. Test baseline

Validated at closeout (2026-06-03):

```powershell
python -m pytest -m golden_replay -q
# 68 passed

python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_ownership_registry.py tests/test_runtime_drift_seed_audit.py -q
# 173 passed (66 + 35 + 51 + 20 + 1)

python tools/refresh_protected_replay_manifest.py --check
# exit 0
```

| Suite | Count | Result |
|---|---:|---|
| Golden replay (CI gate) | 68 | **PASS** |
| Failure classifier | 66 | **PASS** |
| Failure classification contract | 35 | **PASS** |
| Failure dashboard controlled failures | 51 | **PASS** |
| Ownership registry (incl. AO5) | 20 | **PASS** |
| Runtime drift seed audit | 1 | **PASS** |
| Protected replay manifest `--check` | n/a | **PASS** (exit 0) |

**Coverage note:** Golden replay grew from 67 → 68 tests during AO (AO1/AO2/AO3 parity lock tests). All original protected scenarios and AK5 locks remain green. No golden fixture updates. No replay output behavior changes asserted by test failures.

**CI reference:** `.github/workflows/convergence-checks.yml` — `pytest -m golden_replay -q` + manifest `--check`.

---

## 5. Deferred work

### AO6 — Machine-readable protected scenario registry (optional)

**Objective:** Python registry listing PROTECTED scenario IDs, test function names, and classification — consumed by manifest refresh or parity tests.

**Why deferred:**

- Not required for Cycle AO success criteria
- Scenario governance already documented in `docs/testing/protected_replay_manifest.md` manual table
- Field-path parity already CI-gated via `refresh_protected_replay_manifest.py --check`
- Independent of AO1–AO5 consolidation; can land in a future cycle

**When useful:** Reducing manual manifest ↔ pytest test-name drift; automating scenario table regeneration.

**Optional follow-ons (not scoped to AO):**

- Derive `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` as `PROTECTED | EXTENSION` (eliminate duplicate 47-field list)
- Move `golden_replay.py` protected expectation DSL fragments toward projection-owned config
- Registry-driven `project_turn_observation` field extractors for remaining complex paths (AO1 follow-on)

---

## 6. Final verdict

### Success criteria assessment

| Criterion | Met? | Evidence |
|---|---|---|
| **Clearer replay authority** | **Yes** | Single SoT per layer: extraction registry (AO1), classifier overlap derivation (AO2), contract dashboard manifest (AO3), shared row factory (AO4), documented runtime/acceptance split (AO5) |
| **Fewer schema edit touchpoints** | **Yes** | Removed parallel manual lists for extraction, classifier overlap, dashboard keys, and synthetic row baselines; adding a flat protected FEM field now updates extraction spec + optional contract if classifier-eligible |
| **Replay coverage unchanged** | **Yes** | 68/68 golden_replay pass; 9 PROTECTED scenarios intact; AK5 locks green; manifest check pass; no fixture updates |
| **Ownership boundaries strengthened** | **Yes** | Import-time validation, sync misalignment helpers, ownership registry test, manifest boundary section, cross-linked module docs |

### Cycle AO verdict: **SUCCESS — ready for commit/push**

All planned blocks AO0–AO5 complete. AO6 explicitly deferred. No compatibility paths removed. No runtime, classifier logic, dashboard output, or golden replay behavior changes beyond additive parity-lock tests.

---

## Files created or updated during Cycle AO

**Recon (AO0):**

- `audits/cycle_ao_replay_ownership_inventory.md`
- `audits/cycle_ao_replay_schema_touchpoints.json`
- `audits/cycle_ao_replay_authority_boundaries.md`
- `audits/cycle_ao_replay_coverage_baseline.md`
- `audits/cycle_ao_candidate_blocks.md`

**Implementation summaries:**

- `audits/cycle_ao_block_ao1_implementation_summary.md`
- `audits/cycle_ao_block_ao2_implementation_summary.md`
- `audits/cycle_ao_block_ao3_implementation_summary.md`
- `audits/cycle_ao_block_ao4_implementation_summary.md`
- `audits/cycle_ao_block_ao5_implementation_summary.md`

**Closeout:**

- `audits/cycle_ao_replay_ownership_consolidation_closeout.md` (this document)

**Code/docs touched across AO1–AO5 (reference):**

- `tests/helpers/golden_replay_projection.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/replay_observed_row_fixtures.py` (new, AO4)
- `tests/helpers/failure_dashboard_fixtures.py` (AO4 wiring)
- `tests/test_golden_replay.py`, `tests/test_failure_classification_contract.py`
- `game/final_emission_replay_projection.py`, `docs/testing/protected_replay_manifest.md` (AO5 docs)
- `tests/test_ownership_registry.py` (AO5 test)

---

## Recommendation

**Ready to commit and push** Cycle AO as a documentation + test-harness ownership consolidation. Suggested commit scope: all AO code changes + audit artifacts together so the closeout references a single coherent changeset.

If splitting commits: AO1 projection → AO2 classifier → AO3 dashboard → AO4 fixtures → AO5 docs → closeout audits; each tranche should keep `pytest -m golden_replay -q` green.
