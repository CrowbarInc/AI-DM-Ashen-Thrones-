# Cycle AO — Candidate Implementation Blocks

**Date:** 2026-06-03  
**Status:** Proposed only — not implemented.  
**Constraints for all blocks:** No compatibility path deletion; no replay output behavior changes; no golden fixture updates unless tests prove intentional change; preserve 67 golden_replay + CI manifest check.

---

## Block overview

| Block | Objective | Parallel? |
|---|---|---|
| **AO1** | Registry-driven projection extraction | After AO0 recon ✅ |
| **AO2** | Classifier evidence derived from protected registry | Parallel with AO3 after AO1 registry accessors stable |
| **AO3** | Dashboard evidence manifest derived from classifier contract | Parallel with AO2 |
| **AO4** | Unified synthetic observed-row fixture builder | Parallel with AO2/AO3 |
| **AO5** | Runtime vs test projection boundary documentation + import hygiene | Parallel with AO1 (doc-only) or after AO1 |
| **AO6** | Machine-readable protected scenario registry | Independent; lower priority |

---

## AO1 — Registry-driven projection extraction

**Objective:** Reduce schema edit touchpoints inside `golden_replay_projection.py` by driving `project_turn_observation()` field extraction and `raw_signal_presence` from `PROTECTED_OBSERVATION_FIELDS` metadata instead of hand-wired per-field blocks.

**Files likely touched:**
- `tests/helpers/golden_replay_projection.py` (primary)
- `tests/test_golden_replay.py` (AK5 locks — should remain green without semantic change)

**Safety constraints:**
- Observed turn output for all 67 golden_replay tests must be byte-identical for protected fields
- Do not add/remove protected paths
- Do not change dual fallback-family precedence
- `unavailable` parent-prefix rules unchanged

**Expected tests:**
```powershell
python -m pytest -m golden_replay -q
python -m pytest tests/test_golden_replay.py -k "ak5 or dual_family or project_turn" -q
```

**Parallel:** Can start immediately. AO2 benefits from stable registry accessor patterns introduced here.

**Risk:** Medium — large file, high test coverage mitigates.

---

## AO2 — Classifier evidence manifest from projection registry

**Objective:** Replace hand-maintained `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` with a function deriving protected-path ∩ classifier-eligible fields from `protected_observation_field_registry()`. Align `FailureClassification` TypedDict keys with contract via codegen or assert-equal helper.

**Files likely touched:**
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_classifier.py` (TypedDict alignment only)
- Possibly `tests/helpers/golden_replay_projection.py` (export overlap helper)

**Safety constraints:**
- `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` set membership unchanged
- `classify_replay_failure()` output shape unchanged for existing scenarios
- Extension-only fields (15 classifier-only diagnostics) remain manual

**Expected tests:**
```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q
python -m pytest -m golden_replay -q
```

**Parallel:** Yes, with AO3 and AO4, after AO1 registry helpers exist (or in parallel if overlap helper is scoped minimally).

**Risk:** Low–medium — sync tests are strong locks.

---

## AO3 — Dashboard evidence manifest from classifier contract

**Objective:** Derive `FAILURE_DASHBOARD_EVIDENCE_MANIFEST` row keys from `CLASSIFIER_EVIDENCE_FIELDS` (or a labeled manifest in contract module) instead of hand-curated tuple. Keep presentation formatting in dashboard module.

**Files likely touched:**
- `tests/helpers/failure_dashboard_report.py`
- `tests/failure_classification_contract.py` (optional labeled manifest export)
- `tests/test_failure_classification_contract.py`

**Safety constraints:**
- 29 evidence keys and labels unchanged in rendered markdown
- Table columns unchanged
- CI failure report format unchanged

**Expected tests:**
```powershell
python -m pytest tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
python -m pytest tests/test_failure_classifier.py -q
```

**Parallel:** Yes, with AO2 and AO4.

**Risk:** Low — `_assert_failure_dashboard_evidence_manifest` already enforces subset invariant.

---

## AO4 — Unified synthetic observed-row fixture builder

**Objective:** Consolidate `failure_classification_sync.observed_failure_row()` and `failure_dashboard_fixtures._observed()` into one shared builder module; update callers to import single factory.

**Files likely touched:**
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_dashboard_fixtures.py`
- New: `tests/helpers/replay_observed_row_fixtures.py` (or similar)
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_failure_classifier.py` (if imports change)

**Safety constraints:**
- Default synthetic row shape unchanged for all controlled failure probes
- No change to `CONTROLLED_FAILURE_CASES` expected classifications

**Expected tests:**
```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
```

**Parallel:** Yes, with AO2/AO3.

**Risk:** Low — test-only fixtures.

---

## AO5 — Runtime vs test projection boundary clarity

**Objective:** Document and enforce boundary between `game/final_emission_replay_projection.py` (runtime lineage) and `tests/helpers/golden_replay_projection.py` (acceptance observation). Optional: add module doc cross-links; extend ownership registry test; ensure no test-only logic leaks into runtime module.

**Files likely touched:**
- `game/final_emission_replay_projection.py` (docstrings only)
- `tests/helpers/golden_replay_projection.py` (docstrings only)
- `docs/testing/protected_replay_manifest.md` (boundary addendum)
- `tests/test_ownership_registry.py`

**Safety constraints:**
- Zero runtime behavior change
- No import direction changes that create test→game cycles

**Expected tests:**
```powershell
python -m pytest tests/test_ownership_registry.py tests/test_runtime_drift_seed_audit.py -q
python -m pytest -m golden_replay -q
```

**Parallel:** Yes — doc-only can run anytime.

**Risk:** None (documentation).

---

## AO6 — Machine-readable protected scenario registry

**Objective:** Introduce a Python registry (e.g. `tests/helpers/protected_replay_scenarios.py`) listing PROTECTED scenario IDs, test function names, and classification — consumed by manifest refresh tool or parity test. Reduces manual manifest ↔ test drift.

**Files likely touched:**
- New scenario registry module
- `tools/refresh_protected_replay_manifest.py` (optional scenario section generation)
- `docs/testing/protected_replay_manifest.md`
- `tests/test_golden_replay.py` (parity test)

**Safety constraints:**
- PROTECTED scenario set unchanged (9 scenarios)
- Manifest governance semantics unchanged
- Do not alter pytest selection/markers

**Expected tests:**
```powershell
python -m pytest -m golden_replay -q
python tools/refresh_protected_replay_manifest.py --check
```

**Parallel:** Yes — independent of AO1–AO4.

**Risk:** Low governance change; requires careful review of scenario table.

**Ambiguity:** Whether scenario registry should live in `tests/helpers/` or `docs/testing/` — defer decision to implementation PR.

---

## Recommended execution order

```
AO0 recon ✅
    │
    ├── AO5 (doc boundary) ──────────────── parallel track
    │
    ├── AO1 (registry-driven extraction) ── first substantive block
    │       │
    │       ├── AO2 (classifier derive) ─── parallel
    │       ├── AO3 (dashboard derive) ──── parallel
    │       └── AO4 (fixture unify) ─────── parallel
    │
    └── AO6 (scenario registry) ─────────── optional follow-on
```

**Recommended next implementation block:** **AO1** — highest impact on "fewer schema edit touchpoints" without crossing runtime/test boundary or touching classifier/dashboard layers.

---

## Out of scope for Cycle AO (explicit deferrals)

- Merging `final_emission_replay_projection.py` into `golden_replay_projection.py`
- Deleting compatibility paths (`protected_field_paths` alias, legacy repair kinds, compatibility-local authorship)
- Promoting `response_delta_*` or lineage events to protected observation
- Changing drift classification to include lineage owner mismatch
- Updating golden fixtures or protected assertion expectations
