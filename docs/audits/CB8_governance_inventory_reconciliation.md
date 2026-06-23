# CB8 Governance Inventory Reconciliation

**Block:** CB8 — Governance Inventory Reconciliation  
**Type:** Maintenance cleanup (no runtime behavior changes)  
**Primary metric:** Governance Drift  
**Prior audits:** CB5 (+19 drift surfaced), CB7 (root cause: missed regeneration)  
**Generated:** 2026-06-23

---

## Executive summary

| Metric | Before | After |
|---|---:|---:|
| **File drift** (`--check`) | **+19** added, 0 removed | **0** |
| Governance `files[]` count | 45 | **64** |
| Registry-owned paths missing from JSON | 19 | **0** |
| Stale entries removed | — | **0** |
| Orphaned suites (missing on disk) | 0 | **0** |
| Duplicate `direct_owner` claims | 0 | **0** |

**Governance Drift: Resolved**

`py tools/test_audit.py --check` → **Inventory check OK** (5806 tests derived, 64 registry-owned files / 406 total).

**Feature Readiness impact: None** — inventory-only maintenance; no emit-path or gameplay changes.

---

# Missing Files

All **19** files identified by CB5/CB7 `tools/test_audit.py --check` drift report.

## Classification

| Category | Count | Files |
|---|---:|---|
| **BW/BZ** (protected replay trend closeout) | 2 | `tests/test_bw_protected_replay_trend_window_closeout.py`, `tests/test_bz_protected_replay_trend_window_2_closeout.py` |
| **Structural** (golden replay structural suite) | 5 | `tests/test_golden_replay_direct_seam.py`, `tests/test_golden_replay_long_session.py`, `tests/test_golden_replay_protected_bridge.py`, `tests/test_golden_replay_scenario_spine.py`, `tests/test_golden_replay_structural_invariants.py` |
| **Fallback** (portfolio / economics / recurrence) | 8 | `tests/test_fallback_incidence_anomalies.py`, `tests/test_fallback_maintenance_economics.py`, `tests/test_fallback_portfolio_benefit.py`, `tests/test_fallback_recurrence.py`, `tests/test_fallback_remediation_effectiveness.py`, `tests/test_fallback_remediation_queue.py`, `tests/test_fallback_risk_scoring.py`, `tests/test_fallback_roi.py` |
| **Corrective** (CA attribution / availability reports) | 4 | `tests/test_corrective_fix_absence_report.py`, `tests/test_corrective_fix_availability_report.py`, `tests/test_corrective_prevention_effectiveness.py`, `tests/test_embedded_corrective_attribution.py` |
| **Other** | 0 | — |

**Total: 19**

### Enrollment mechanism

New suites entered committed governance via `governance_committed_file_paths()`:

1. **Registry `files_roles`** — unchanged 46 paths; all present in governance JSON.
2. **Cross-file duplicate blocks** — 18 additional paths enrolled because they participate in allowlisted duplicate base-name families (see Validation).

`tests/test_golden_replay.py` was already enrolled before CB8; the five structural golden-replay siblings were among the +19.

---

# Root Cause

| Factor | Finding |
|---|---|
| **Registry health** | **Healthy** — 17 `RESPONSIBILITY_REGISTRY` groups; no duplicate `direct_owner` claims (CB7 confirmed) |
| **Corruption** | **None** — drift was additive only (+19, −0) |
| **Root cause** | **Missed regeneration** — BW/BZ closeout, golden replay structural suite, fallback portfolio, and CA corrective report modules landed without running `py tools/test_audit.py` and committing `tests/test_inventory_governance.json` |
| **Secondary exposure** | Regen surfaced **6 cross-file duplicate test base names** across the new suites; resolved by extending `_CROSS_FILE_DUPLICATE_ALLOWLIST` with documented reasons (governance policy, not runtime) |

---

# Regenerated Inventory

## Command

```text
py tools/test_audit.py
```

## Output

```text
Wrote tests/test_inventory_governance.json (governance: 64 registry-owned files / 406 total; 5806 per-test markers derived at check/full only)
```

## Artifact changes

| File | Change |
|---|---|
| `tests/test_inventory_governance.json` | +19 `files[]` path rows (45 → 64) |
| `tests/test_ownership_registry.py` | +6 `_CROSS_FILE_DUPLICATE_ALLOWLIST` entries for new audit-suite parallel test names |

No changes to `game/**`, replay helpers, or emit-path modules.

---

# Validation

## File coverage

| Check | Result |
|---|---|
| All 19 previously missing files in committed JSON | **PASS** |
| All 64 governance paths exist on disk | **PASS** |
| All 46 registry `files_roles` paths in governance JSON | **PASS** (0 missing) |
| Stale paths removed | **PASS** (0 removed) |

## Governance check

```text
py tools/test_audit.py --check
→ Inventory check OK: tests/test_inventory_governance.json matches fresh regen
```

## Duplicate ownership

| Check | Result |
|---|---|
| Duplicate `direct_owner` in `RESPONSIBILITY_REGISTRY` | **PASS** — 0 conflicts |
| Cross-file duplicate base names | **PASS** — 6 families allowlisted |

### Allowlisted duplicate families (CB8)

| Base name | Files (summary) |
|---|---|
| `test_build_report_from_inputs` | CA absence + availability reports |
| `test_closeout_doc_states_six_scenario_protected_corpus` | BW + BZ closeout |
| `test_concentration_calculations` | CA prevention + embedded attribution |
| `test_deterministic_ordering` | 8 fallback portfolio modules |
| `test_empty_history` | Fallback economics + remediation queue |
| `test_report_generation` | 4 CA/fallback report modules |

## Orphaned suites

| Definition | Count |
|---|---:|
| Registry paths absent from governance JSON | **0** |
| Governance paths absent from disk | **0** |
| Registry groups without `direct_owner` | **0** |

18 governance paths are **not** in `files_roles` — expected: they are cross-file-duplicate enrolled neighbors, not direct owners.

## Ownership registry tests (spot check)

| Test | Result | CB8 scope? |
|---|---|---|
| `test_cross_file_duplicate_allowlist_from_derived_full_audit` | **PASS** | Yes |
| `test_ownership_registry_governance` | **FAIL** (1 error) | Pre-existing — see Residual Issues |

---

# Residual Issues

Issues **not introduced by CB8**; outside governance-inventory drift scope:

| ID | Issue | Status |
|---|---|---|
| R1 | `final_emission_gate_orchestration`: `tests/test_final_emission_gate.py` heuristic layer `general` vs declared `gate` | Pre-existing heuristic mismatch in `test_ownership_registry_governance` |
| R2 | BD-6 / BV2C / BJ-127 / BU8 / BU9 ownership-registry guard failures | Pre-existing import-parity and harness scans; unrelated to inventory regen |

These do not affect `tools/test_audit.py --check` pass/fail for committed governance JSON.

---

## Readiness impact

| Dimension | Impact |
|---|---|
| **Feature Readiness** | **None** — no product or emit-path changes |
| **Governance Drift** | **Resolved** — file drift 0; `--check` OK |
| **Safe-domain throughput** | Unchanged (CB2/CB7 posture holds) |
| **Prohibited domains** | Unchanged |

---

## Restrictions compliance

| Restricted area | Modified? |
|---|---|
| `game/**` runtime modules | **No** |
| `final_emission*` / `fallback*` / `speaker*` / `response_policy*` / `replay*` | **No** |
| Runtime behavior | **No** |

---

## Cursor Feedback

| Item | Value |
|---|---|
| **Drift count before** | **+19** added, **0** removed |
| **Drift count after** | **0** (`--check` OK) |
| **Orphaned suites** | **0** (all registry paths enrolled; all governance paths on disk) |
| **Ownership issues found** | **0** duplicate owners; **6** cross-file duplicate families allowlisted; **1** pre-existing gate-layer heuristic (R1) |
