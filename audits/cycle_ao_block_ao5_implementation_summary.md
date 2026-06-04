# Cycle AO5 — Runtime vs Test Projection Boundary Clarity (Closeout)

**Date:** 2026-06-03  
**Status:** Completed — documentation and ownership tests only; no behavior changes.

---

## Objective

Document and lock the split between runtime FEM lineage projection and acceptance-side golden replay observation projection.

---

## Files changed

| File | Change |
|---|---|
| `game/final_emission_replay_projection.py` | AO5 module docstring: runtime lineage ownership, cross-link to acceptance module, do-not-merge rule |
| `tests/helpers/golden_replay_projection.py` | AO5 module docstring: acceptance authority, lineage exclusion from drift, cross-link to runtime module |
| `docs/testing/protected_replay_manifest.md` | New **Cycle AO5 Runtime vs Acceptance Projection Boundary** section |
| `tests/test_ownership_registry.py` | Added `test_ao5_runtime_and_acceptance_projection_modules_remain_separate` |

**Not changed:** projection logic, classifier, dashboard, golden fixtures, generated manifest section.

---

## Boundary summary (now explicit in code + manifest)

| Layer | Module | Owns |
|---|---|---|
| Runtime (diagnostic) | `game/final_emission_replay_projection.py` | `fem_runtime_lineage_events`, sealed sub-kinds, lineage owner fields on events |
| Acceptance (test-only) | `tests/helpers/golden_replay_projection.py` | 41 protected paths, `project_turn_observation`, drift buckets |

**Explicit rules documented:**
- Modules must not be merged
- Runtime lineage is read-side diagnostic only
- Protected fields are acceptance authority
- Lineage owner mismatch excluded from protected drift unless explicitly promoted later

---

## Tests executed

```powershell
python -m pytest tests/test_ownership_registry.py tests/test_runtime_drift_seed_audit.py -q
# passed (ownership registry + new AO5 test + drift seed audit)

python -m pytest -m golden_replay -q
# 68 passed

python tools/refresh_protected_replay_manifest.py --check
# exit 0 (manual AO5 section does not affect generated field-path block)
```

---

## Cycle AO status

| Block | Status |
|---|---|
| AO0 Recon | Complete |
| AO1 Registry-driven projection extraction | Complete |
| AO2 Classifier evidence from protected registry | Complete |
| AO3 Dashboard evidence manifest from contract | Complete |
| AO4 Unified synthetic observed-row factory | Complete |
| AO5 Runtime vs acceptance boundary docs | Complete |
| AO6 Machine-readable scenario registry | Optional — not required for closeout |

---

## Recommendation: Cycle AO closeout

**Proceed to Cycle AO closeout** unless scenario-registry automation (AO6) is still desired.

AO6 would add a machine-readable PROTECTED scenario registry (IDs ↔ test functions) to reduce manual manifest ↔ pytest drift. It is independent, low risk, and optional — the core ownership consolidation goals (AO1–AO5) are satisfied:

- Projection extraction registry-first (AO1)
- Classifier protected overlap derived (AO2)
- Dashboard evidence contract-owned (AO3)
- Single synthetic row factory (AO4)
- Runtime/acceptance boundary explicit (AO5)

Suggested closeout artifact: `audits/cycle_ao_replay_ownership_consolidation_closeout.md` summarizing blocks AO1–AO5, test baselines, and deferred AO6 scope.
