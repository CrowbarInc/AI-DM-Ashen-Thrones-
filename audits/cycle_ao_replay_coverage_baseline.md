# Cycle AO0 — Replay Coverage Baseline

**Date:** 2026-06-03  
**Environment:** Windows 10, workspace `ashen_thrones_ai_gm`  
**Purpose:** Pre-refactoring test baseline for Cycle AO. Record commands and results before ownership consolidation.

---

## Summary

| Suite | Command | Collected | Result |
|---|---|---:|---|
| Golden replay (CI gate) | `python -m pytest -m golden_replay -q --tb=no` | 67 | **PASS** |
| Classifier + contract + dashboard + lineage | `python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_runtime_lineage_telemetry.py -q --tb=no` | 156 | **PASS** |
| Runtime drift seed audit | `python -m pytest tests/test_runtime_drift_seed_audit.py -q --tb=no` | 1 | **PASS** |
| Manifest registry parity | `python tools/refresh_protected_replay_manifest.py --check` | n/a | **PASS** (exit 0) |

**Total replay-adjacent tests executed:** 224  
**Failures:** 0  
**Pre-existing failures observed:** None

---

## Commands (exact)

### 1. Primary CI acceptance gate

```powershell
Set-Location "c:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm"
python -m pytest -m golden_replay -q --tb=no
```

**Output:**
```
...................................................................      [100%]
```

**Duration:** ~27s  
**Exit code:** 0

### 2. Classifier, contract, dashboard, lineage

```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_runtime_lineage_telemetry.py -q --tb=no
```

**Output:**
```
........................................................................ [ 46%]
........................................................................ [ 92%]
............                                                             [100%]
```

**Duration:** ~2s  
**Exit code:** 0

**Breakdown (collect-only):**
- `tests/test_failure_classification_contract.py`: 32
- `tests/test_failure_classifier.py`: 66
- `tests/test_failure_dashboard_controlled_failures.py`: 51
- `tests/test_runtime_lineage_telemetry.py`: 7

### 3. Runtime drift seed audit

```powershell
python -m pytest tests/test_runtime_drift_seed_audit.py -q --tb=no
```

**Output:**
```
.                                                                        [100%]
```

**Exit code:** 0

### 4. Manifest registry parity (CI step)

```powershell
python tools/refresh_protected_replay_manifest.py --check
```

**Output:** (empty — success)  
**Exit code:** 0

---

## Failing tests

None at baseline capture time.

---

## Tests especially important to preserve before refactoring

### Acceptance-blocking (CI hard gate)

| Test / group | Why critical |
|---|---|
| `test_golden_replay_*_structural_invariants` (9 PROTECTED scenarios) | Declared acceptance blockers in manifest |
| `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability` | Long-session protected scenario (25 turns) |
| `test_ak5_every_protected_path_is_projected_or_marked_unavailable` | Ensures all 41 registry paths are wired |
| `test_ak5_synthetic_turn_exercises_fem_backed_protected_fields` | FEM-backed field extraction lock |
| `test_ak5_synthetic_turn_exercises_sanitizer_backed_protected_fields` | Sanitizer-backed field extraction lock |
| `test_protected_replay_manifest_matches_observation_registry` | Manifest ↔ registry parity |
| `test_ak5_manifest_generated_section_matches_registry` | Generated manifest section lock |
| `test_golden_replay_dual_family_projection_*` (4 tests) | AB dual fallback-family precedence contract |

### Schema alignment locks

| Test / group | Why critical |
|---|---|
| `test_classifier_tables_stay_aligned_with_contract` | Classifier rules ↔ contract taxonomies |
| `tests/test_failure_classification_contract.py` alignment tests | Contract ↔ classifier ↔ dashboard sync |
| `failure_dashboard_report._assert_failure_dashboard_evidence_manifest` | Runtime assert: dashboard keys ⊆ classifier |

### Diagnostic (not CI hard gate, but preserve behavior)

| Test / group | Why critical |
|---|---|
| `test_golden_drift_classifier_buckets_exact_structural_and_semantic_drift` | Drift policy unchanged |
| `test_golden_drift_classification_ignores_runtime_lineage_diagnostics` | Lineage excluded from drift — intentional |
| `test_compare_golden_replay_reruns_*` | Advisory rerun compare semantics |
| `test_protected_golden_assertion_failure_records_canonical_report` | CI failure artifact shape |
| `test_runtime_drift_seed_audit.py` | Nondeterminism guard on replay-sensitive paths |

### Opt-in (run manually when touching dashboard)

```powershell
python -m pytest -m golden_replay -q --write-failure-dashboard
python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
```

---

## CI reference

From `.github/workflows/convergence-checks.yml`:

1. `python -m pytest -m golden_replay -q` — hard fail on protected assertion failure
2. `python tools/refresh_protected_replay_manifest.py --check` — manifest parity
3. Upload `artifacts/golden_replay/replay_failure_report.md` on failure

---

## Notes for AO implementation

- All 67 golden_replay tests passed without fixture updates — baseline is clean for consolidation work.
- Classifier/dashboard tests pass without `--write-failure-dashboard`; probe tests may skip unless opt-in (by design).
- No golden fixture files in repo were modified during this recon.
